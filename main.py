#!/usr/bin/env python
"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

main.py
Author: Shaun Flynn
Date last modified: 4/23/19
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'

import threading
import numpy as np
import cv2
import logging
import datetime
import traceback
import copy
import time

from SQL_Driver import ObjectDB
from Item import Item
from VisionThread import VisionThread
from SSH_Thread import SSHThread
from GUI import GUI

LOG_LEVEL_CMD = logging.WARNING         # The min log level that will be displayed in the console
LOG_DIR = 'Logs'                        # Directory to save log files to
LEFT_CAMERA_SERIAL_NUM = '18585124'     # Left stereo camera ID
RIGHT_CAMERA_SERIAL_NUM = '18585121'    # Right stereo camera ID
GRAPH_TYPE = 'SSD_INCEPTION_V2'         # Network graph model to use for object detection
INCHES_PER_PIXEL = 0.015735782          # Number of inches each pixel represents at the datum
IMAGE_DOWNSCALE_RATIO = 0.5             # Downscale ratio for machine learning
ARM_CONSTANT = 0.00062927
x_shift_const = 0.4
x_conversion_const = x_shift_const/634.5 #Shift amount/middle pixel value
x_final_const = 0.926277568
y_conversion_const = 0.00061
                                        #    1  = process the full image (more accurate)
                                        #    <1 = process a smaler version of the image (faster)

# GUI Message Codes
GUI_MESSAGES = dict(
                    # GENERAL MESSAGES
                    UNEXPECTED_ERROR=0,
                    KNOWN_ERROR=1,

                    # SQL JOB MESSAGES
                    OBJECT_NOT_MOVED=10,
                    WRONG_OBJECT_REMOVED=11,
                    WRONG_NUMBER_MOVED=12,
                    OBJECT_NOT_FOUND=13,
                    CORRECT_OBJECT_MOVED=14,
                    CURRENT_REQUESTED_OBJECT=15,
                    JOB_QUEUE_EMPTY=16
                    )


class Main:

    def __init__(self):
        """
        Constructor
        """

        # =================================
        # Setup Logging
        # =================================
        # Create master logger and set global log level
        self._logger = logging.getLogger("GM_Pick_Point")
        self._logger.setLevel(logging.DEBUG)

        # create log file
        file_handler = logging.FileHandler(LOG_DIR + '/GM_Pick_Point - %s.log' %
                                           datetime.datetime.now().strftime("%Y.%m.%d-%H.%M.%S"))
        file_handler.setLevel(logging.DEBUG)

        # create console logger
        console_handler = logging.StreamHandler()
        console_handler.setLevel(LOG_LEVEL_CMD)

        # Format Log
        log_formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(name)s - %(message)s')
        file_handler.setFormatter(log_formatter)
        console_handler.setFormatter(log_formatter)

        # Add outputs to main logger
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)
        # =====================================================================

        # Setup GUI
        self._logger.debug('Initializing GUI Thread')
        self._gui_thread = GUI()

        # Setup SQL
        self._logger.debug('Initializing SQL Thread')
        self._sql_thread = None
        self._sql_thread_complete = threading.Event()
        self._processing_job = threading.Event()
        self._requested_item = None
        self._sql_result = []
        self._sql_result_lock = threading.Lock()
        self._sql_db = ObjectDB.ObjectDB()

        # Setup Vision Thread
        self._logger.debug('Initializing Vision Thread')
        self._vision_thread = VisionThread(LEFT_CAMERA_SERIAL_NUM, RIGHT_CAMERA_SERIAL_NUM, GRAPH_TYPE, LOG_DIR,
                                           IMAGE_DOWNSCALE_RATIO)
        
        # Setup SSH
        self._ssh_thread = SSHThread.SSHThread()
        
        
        # Setup local variables
        self._camera_result = None
        self._camera_result_lock = threading.Lock()

        self._last_item_list = []
        self._last_item_list_lock = threading.Lock()

        self._current_item_list = []
        self._current_item_list_lock = threading.Lock()

        self._object_removed_successfully = False
        self._object_not_found = False

        self._termination_requested_event = threading.Event()

        self._logger.debug('Threads Initialized')

    def main_loop(self):
        """
        Main Loop that will run the program until a termination is requested or on an error
        """
        try:
            self._logger.debug('Starting Vision Thread')
            self._vision_thread.start()

            self._logger.debug('Starting SSH Thread')
            self._ssh_thread.start()
            self._ssh_thread._append_command("OPEN")
            self._ssh_thread._append_command("CLOSE")

            while self._gui_thread.is_alive():      # Keep going until the GUI thread dies
                vision_task_thread = None
                sql_task_thread = None
                try:
                    vision_task_thread = threading.Thread(target=self._call_vision_thread())
                    vision_task_thread.start()

                    print("Test")

                    # If a SQL job is being processed don't start another one
                    if not self._processing_job.is_set():
                        sql_task_thread = threading.Thread(target=self._call_sql_thread())
                        sql_task_thread.start()

                except Exception as e:
                    # on an error join the task threads
                    if vision_task_thread is not None:
                        vision_task_thread.join()

                    if sql_task_thread is not None:
                        sql_task_thread.join()

                    raise Exception(e)
                else:
                    # Join Task Threads
                    if vision_task_thread is not None:
                        vision_task_thread.join()

                    if sql_task_thread is not None:
                        sql_task_thread.join()
                        self._processing_job.set()
                    else:
                        # If a SQL job is being processed then continue to processes that job
                        lest_requested_item = self._sql_result[0]
                        msgs = self._process_sql_job()              # Get messages from the processing

                        # Log all messages to the GUI
                        for msg in msgs:
                            text = list(GUI_MESSAGES.keys())[list(GUI_MESSAGES.values()).index(msg[0])]
                            text = "%s : %s" % (text, msg[1].item_type)
                            self._gui_thread.add_msg_to_log(text)

                        size = (0, 0)
                        with self._camera_result_lock:
                            if self._camera_result is not None:
                                image_0 = self._camera_result[0]
                                size = image_0.shape

                        # Get the X, Y, Z coords of the object
                        requested_item = self._sql_result[0]
                        x = "N/A"
                        y = "N/A"
                        z = "N/A"
                        
                        with self._current_item_list_lock:
                            for item in self._current_item_list:
                                if item.item_type == requested_item.item_type:
                                    x = "%0.4f in" % (item.x * size[1] * INCHES_PER_PIXEL)
                                    y = "%0.4f in" % (item.y * size[0] * INCHES_PER_PIXEL)
                                    z = "%0.4f in" % item.z
                                    print("x = %s, y = %s, z = %s" % (x, y, z))
                                    break
                    

                        # Get the image coordinates
                        item_x = self._vision_thread._get_x()
                        x = item_x
                        item_y = self._vision_thread._get_y()
                        y = item_y
                        z = 0
                        print("Tried to get image coordinates")

                        print("Item-X: {}, Item-Y: {}".format(item_x, item_y))

                        if ((item_x is not None) and (item_y is not None)):
                            # Translate to arm coordinates
                            arm_x = float((item_x * x_conversion_const - x_shift_const) * x_final_const)
                            arm_y = float(item_y * y_conversion_const)
                            # PICK X Y Z ROLL PITCH YAW
                            # Arm flips x and y
                            self._ssh_thread._append_command("PICK {} {} {} {} {} {}".format(arm_y, arm_x, 0.1, 0, 1.4, 0))

                            # SHIFT AXIS AMOUNT
                            # Move out of the way
                            self._ssh_thread._append_command("MOVE {} {} {} {} {} {}".format(arm_y, arm_x, 0.1 + .15, 0, 1.4, 0))

                            # DROP OFF POINT
                            self._ssh_thread._append_command("DROP {} {} {} {} {} {}".format(.007, 0.231, 0.340, 0.066, 1.284, 1.687))
                        

                        

                        message = 'Requesting Object: %s' % requested_item.item_type

                        # Update GUI based on results
                        if self._object_removed_successfully:
                            self._gui_thread.set_result(1, error=message, item=lest_requested_item.item_type,
                                                        placement=lest_requested_item.placement, x=x, y=y, z=z)
                        elif self._object_not_found:
                            self._gui_thread.set_result(0, error="Object Not Found!", item=requested_item.item_type,
                                                        placement=requested_item.placement, x="N/A", y="N/A", z="N/A")
                        else:
                            self._gui_thread.set_result(2, error=message, item=requested_item.item_type,
                                                        placement=requested_item.placement, x=x, y=y, z=z)

                        self._gui_thread.wait_on_next_object_request()
                        self._object_removed_successfully = False
                        self._object_not_found = False

        except Exception:
            tb = traceback.format_exc()
            self._logger.error('Unhandled Exception:\n%s' % str(tb))
        finally:
            # Request Termination of Threads
            self._logger.debug('Terminating Vision Thread')
            self._vision_thread.terminate_thread()

            self._logger.debug('Terminating GUI Thread')
            self._gui_thread.terminate_thread()

            # Join all threads
            self._logger.debug('Joining Vision Thread')
            self._vision_thread.join()
            self._gui_thread.join()

    def get_camera_images(self):
        """
        External facing function to get a stereo image pair
        :return: a stereo image pair
        """
        self._logger.debug('Getting Camera Image...')
        with self._camera_result_lock:
            result = copy.deepcopy(self._camera_result)

        self._logger.debug('Getting Camera Image - COMPLETE')
        return result

    def get_sql_result(self):
        """
        External facing function to get the current SQL job
        :return: a stereo image pairan SQL job
        """

        self._sql_thread_complete.wait()
        with self._sql_result_lock:
            result = copy.deepcopy(self._sql_result)
        return result

    def get_current_item_list(self):
        """
        External facing function to get a list of Items that are in the current frame
        :return: a list of Items
        """
        with self._current_item_list_lock:
            result = copy.deepcopy(self._current_item_list)
        return result

    def get_last_item_list(self):
        """
        External facing function to get a list of Items that where in the last frame
        :return: a list of Items
        """
        with self._last_item_list_lock:
            result = copy.deepcopy(self._last_item_list)
        return result

    def _call_vision_thread(self):
        """
        Task thread method to call request updated info from the vision thread
        """
        images = self._vision_thread.get_images()
        items = self._vision_thread.get_items()

        with self._camera_result_lock:
            self._camera_result = images

        with self._current_item_list_lock:
            self._last_item_list = self._current_item_list
            self._current_item_list = items

    def _call_sql_thread(self):
        """
        Task thread function to call the SQL thread to request a new job
        """
        self._sql_thread_complete.clear()
        with self._sql_result_lock:
            next_incomplete_job = self._sql_db.get_incomplete_job()
            self._logger.debug("next job: %s"  % str(next_incomplete_job[1]))
            if next_incomplete_job is None:
                raise ValueError("Database is empty")

            job = self._sql_db.get_object_list(next_incomplete_job[1])
            self._sql_result = []
            for item in job:
                self._sql_result.append(Item(item[1], placement=item[2]))
            self._sql_thread_complete.set()

    def _process_sql_job(self):
        """
        Internal function to process the current sql job
        """
        msg = []

        sql_items = self.get_sql_result()
        current_items = self.get_current_item_list()
        last_items = self.get_last_item_list()

        # Current Job is done
        if len(sql_items) == 0:
            msg.append((GUI_MESSAGES["JOB_QUEUE_EMPTY"],))
            self._processing_job.clear()
            return msg

        # get requested item and update visualization
        requested_item = sql_items[0]
        self._logger.info('Next Requested Item: %s' % requested_item.item_type)
        msg.append((GUI_MESSAGES["CURRENT_REQUESTED_OBJECT"], requested_item))
        self._vision_thread.set_visualization_settings(True, requested_item.item_type, 1, False, False)

        # Check if requested item was found
        item_found = False
        for item in current_items:
            if item.item_type == requested_item.item_type:
                item_found = True
                break

        if not item_found:
            msg.append((GUI_MESSAGES["OBJECT_NOT_FOUND"], requested_item))
            self._object_not_found = False

        # Get all items that have been removed since the last iteration
        removed_items = []
        for item_one in last_items:
            found_difference = True
            for item_two in current_items:
                if item_one.item_type == item_two.item_type:
                    found_difference = False
                    break

            if found_difference:
                removed_items.append(item_one)

        # Check if the correct item was removed
        correct_item_removed = False
        for item in removed_items:
            if item.item_type == requested_item.item_type:

                if not correct_item_removed:
                    correct_item_removed = True
                    msg.append((GUI_MESSAGES["CORRECT_OBJECT_MOVED"], item))
                else:
                    msg.append((GUI_MESSAGES["WRONG_NUMBER_MOVED"], item))
            else:
                msg.append((GUI_MESSAGES["WRONG_OBJECT_REMOVED"], item))

        if correct_item_removed:
            with self._sql_result_lock:
                self._sql_result.remove(self._sql_result[0])
            self._object_removed_successfully = True
        return msg


if __name__ == '__main__':
    main_thread = Main()
    main_thread.main_loop()
