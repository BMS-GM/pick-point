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
from GUI import GUI

LOG_LEVEL_CMD = logging.DEBUG
LOG_DIR = 'Logs'
LEFT_CAMERA_SERIAL_NUM = '18585124'
RIGHT_CAMERA_SERIAL_NUM = '18585121'
# GRAPH_TYPE = 'FASTER_RCNN_RESNET'
GRAPH_TYPE = 'SSD_INCEPTION_V2'

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

        # Setup Multi-threading
        self._logger.debug('Initializing GUI Thread')
        self._gui_thread = GUI()

        self._logger.debug('Initializing SQL Thread')
        self._sql_thread = None
        self._sql_thread_complete = threading.Event()
        self._processing_job = threading.Event()
        self._requested_item = None
        self._sql_result = []
        self._sql_result_lock = threading.Lock()
        self._sql_db = ObjectDB.ObjectDB()

        self._logger.debug('Initializing Vision Thread')
        self._vision_thread = VisionThread(LEFT_CAMERA_SERIAL_NUM, RIGHT_CAMERA_SERIAL_NUM, GRAPH_TYPE, LOG_DIR)

        self._camera_result = None
        self._camera_result_lock = threading.Lock()

        self._last_item_list = []
        self._last_item_list_lock = threading.Lock()
        self._current_item_list = []
        self._current_item_list_lock = threading.Lock()

        self._termination_requested_event = threading.Event()

        self._logger.debug('Threads Initialized')

    def main_loop(self):
        try:
            self._logger.debug('Starting Vision Thread')
            self._vision_thread.start()

            while self._gui_thread.is_alive():
                vision_task_thread = None
                sql_task_thread = None
                try:
                    vision_task_thread = threading.Thread(target=self._call_vision_thread())
                    vision_task_thread.start()

                    if not self._processing_job.is_set():
                        sql_task_thread = threading.Thread(target=self._call_sql_thread())
                        sql_task_thread.start()

                except Exception as e:

                    if vision_task_thread is not None:
                        vision_task_thread.join()

                    if sql_task_thread is not None:
                        sql_task_thread.join()

                    raise Exception(e)
                else:
                    if vision_task_thread is not None:
                        vision_task_thread.join()

                    if sql_task_thread is not None:
                        sql_task_thread.join()
                        self._processing_job.set()
                    else:
                        msgs = self._process_sql_job()
                        for msg in msgs:
                            text = list(GUI_MESSAGES.keys())[list(GUI_MESSAGES.values()).index(msg[0])]
                            text = "%s : %s" % (text, msg[1].item_type)
                            self._gui_thread.add_msg_to_log(text)

                        requested_item = self._sql_result[0]
                        x = "N/A"
                        y = "N/A"
                        z = "N/A"
                        for item in self._current_item_list:
                            if item.item_type == requested_item.item_type:
                                x = "%d" % item.x
                                y = "%d" % item.y
                                z = "%d" % item.z

                        message = 'Requesting Object: %s' % requested_item.item_type
                        self._gui_thread.set_result(2, error=message, item=requested_item.item_type,
                                                    placement=requested_item.placement, x=x, y=y, z=z)
                        self._gui_thread.wait_on_next_obeject_request()
                        print("Next Iteration")

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
        self._logger.debug('Getting Camera Image...')
        with self._camera_result_lock:
            result = copy.deepcopy(self._camera_result)

        self._logger.debug('Getting Camera Image - COMPLETE')
        return result

    def get_sql_result(self):
        self._sql_thread_complete.wait()
        with self._sql_result_lock:
            result = copy.deepcopy(self._sql_result)
        return result

    def get_current_item_list(self):
        with self._current_item_list_lock:
            result = copy.deepcopy(self._current_item_list)
        return result

    def get_last_item_list(self):
        with self._last_item_list_lock:
            result = copy.deepcopy(self._last_item_list)
        return result

    def _call_vision_thread(self):
        images = self._vision_thread.get_images()
        items = self._vision_thread.get_items()

        with self._camera_result_lock:
            self._camera_result = images

        with self._current_item_list_lock:
            self._last_item_list = self._current_item_list
            self._current_item_list = items

    def _call_sql_thread(self):
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
        for item in current_items:
            if item.item_type == requested_item.item_type:
                break
            msg.append((GUI_MESSAGES["OBJECT_NOT_FOUND"], requested_item))

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
                    print("REMOVED!!!!!")
                    msg.append((GUI_MESSAGES["CORRECT_OBJECT_MOVED"], item))
                else:
                    msg.append((GUI_MESSAGES["WRONG_NUMBER_MOVED"], item))
            else:
                msg.append((GUI_MESSAGES["WRONG_OBJECT_REMOVED"], item))

        if correct_item_removed:
            with self._sql_result_lock:
                self._sql_result.remove(self._sql_result[0])

        return msg

if __name__ == '__main__':
    main_thread = Main()
    main_thread.main_loop()
