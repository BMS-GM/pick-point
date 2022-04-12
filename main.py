#!/usr/bin/env python
"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

main.py
Author: Shaun Flynn
Date last modified: 4/10/21
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
import configparser

from SQL_Driver import ObjectDB
from Item import Item
from VisionThread import VisionThread
from GUI import GUI
from ZEDMiniDriver import ZEDMiniDriver

from pyniryo import *

LOG_LEVEL_CMD = logging.WARNING         # The min log level that will be displayed in the console
LOG_DIR = 'Logs'                        # Directory to save log files to
CAMERA_SERIAL_NUM = '18585124'          # stereo camera ID
GRAPH_TYPE = 'SSD_INCEPTION_V2'         # Network graph model to use for object detection
IMAGE_DOWNSCALE_RATIO = 0.5             # Downscale ratio for machine learning
                                        #    1  = process the full image (more accurate)
                                        #    <1 = process a smaler version of the image (faster)
picked_items = []

sorting_coords = {
    "bird": [-0.014, 0.298, 0.25, -0.296, 1.530, 1.346],
    "cat":  [0.003, -0.152, 0.25, -0.050, 1.395, -1.571],
    "dog":  [0.000, -0.257, 0.25, 0.070, 1.410, -1.496],
    "home": [0.12, 0.0, 0.15, 0.0, 1.57, 0.0],
}


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

    # config_variables: all the variables that need to be read from the config file
    # each "north, east, south west" coordinate system describes the four bounds according to one device, FLIR camera, Niryo arm, or Zed depth sensor
    config_variables = {
        'camera_coordinates': {
            'north': 0.0,
            'east':  0.0,
            'south': 0.0,
            'west':  0.0
        },
        'arm_coordinates': {
            'north': 0.0,
            'east':  0.0,
            'south': 0.0,
            'west':  0.0
        },
        'zed_coordinates': {
            'north': 0.0,
            'east':  0.0,
            'south': 0.0,
            'west':  0.0
        }
    }

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

        # read data from config file
        self.parse_config()

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
        self._vision_thread = VisionThread(CAMERA_SERIAL_NUM, GRAPH_TYPE, LOG_DIR,
                                           IMAGE_DOWNSCALE_RATIO)
        # start TCP connection
        self.robot = NiryoRobot("10.10.10.10")
        self.robot.calibrate_auto()
        
        # Initialize ZED Mini Driver
        self._logger.debug("Initializing ZED Mini Driver")
        self._zed_driver = ZEDMiniDriver()

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

            self._logger.debug('Homing Arm')
            self.robot.move_pose(sorting_coords["home"])

            while self._gui_thread.is_alive():      # Keep going until the GUI thread dies
                # create and run the two task threads to retrieve the vision and machine learning results
                try:
                    sql_task_thread_is_still_running = self.run_vision_and_sql_task_threads()
                    if sql_task_thread_is_still_running:
                        continue
                except Exception as e:
                    raise Exception(e)

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

                # If recognized items are not empty
                if (not self.get_current_item_list): #Modified with continue

                    self.main_loop_helper(requested_item)
                    continue

                selected_item = None
                

                # Choose first existing item that has not been picked
                for next_item in self.get_current_item_list():
                    if (next_item.item_type not in (picked_items)):
                        selected_item = next_item
                        picked_items.append(next_item.item_type)
                        break

                # Prep to create command
                if (selected_item is None): #Modified with continue

                    print("No Objects Identified")

                    self.main_loop_helper(requested_item)
                    continue

                # Translate to arm coordinates
                arm_x, arm_y = self.convert_coordinates(selected_item.x, selected_item.y,
                    self.config_variables['camera_coordinates'],
                    self.config_variables['arm_coordinates'])
                
                # get the coordinates of the drop off location for the identified object
                drop_off = ""
                if ('bird' in selected_item.item_type.lower()):
                    drop_off = sorting_coords['bird']
                elif ('dog' in selected_item.item_type.lower()):
                    drop_off = sorting_coords['dog']
                elif ('cat' in selected_item.item_type.lower()):
                    drop_off = sorting_coords['cat']
                else:
                    print("Object was not able to be identified..... Going Home")
                    drop_off = sorting_coords['home']

                print("Appending instructions for {} X={} Y={}".format(selected_item.item_type, selected_item.x, selected_item.y))
                
                print("Translated Coordinates: Arm_x: {} Arm_y: {}".format(arm_x, arm_y))

                zed_x, zed_y = self.convert_coordinates(selected_item.x, selected_item.y,
                    self.config_variables['camera_coordinates'],
                    self.config_variables['zed_coordinates'])
                print(f"zed x, y : {zed_x}, {zed_y}")
                arm_z = self._zed_driver.get_object_height(zed_x, zed_y)
                print(f"height: {arm_z}")

                # The rotation of the end effector of the robot arm, will be either vertical or horizontal
                applied_rotation = 0
                # If length of detection box is larger than height
                if (selected_item.rot):
                    # Value is in radians [90 degrees]
                    applied_rotation = 1.5708
                
                self.pick_and_place(arm_x, arm_y, arm_z, applied_rotation, drop_off)

                self.main_loop_helper(requested_item)

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
            
            # terminate robot connection
            self.robot.close_connection()

    def parse_config(self):
        """
        Helper function to get data from the config file.
        """
        bad_read = False
        self._logger.debug('parsing config file...')
        config = configparser.ConfigParser()
        config.read('.config')
        # for each key to a subdictionary in the config_variables dictionary...
        for section_name in list(self.config_variables):
            # check if the subdictionary is found in the config file
            if section_name not in config.sections():
                bad_read = True
                print("Error! section " + section_name + " not found in config file, adding it")
                # create an instance of the section in the config file for the user to fill out
                config[section_name] = {}
                for variable_name in list(self.config_variables[section_name]):
                    config[section_name][str(variable_name)] = str(self.config_variables[section_name][variable_name])
                config_file = open('.config', 'w')
                config.write(config_file)

            # for each key in the subdictionary...
            for variable_name in list(self.config_variables[section_name]):
                # retrieve the value from the subdictionary
                self.config_variables[section_name][variable_name] = config.getfloat(section_name, variable_name)
                # if the value is 0.0, then report error
                if self.config_variables[section_name][variable_name] == 0.0:
                    print(variable_name + ' in .config is undefined, please add value in .config file')
                    bad_read = True

        if bad_read == True:
            self._logger.debug('parsing config file - FAILURE, quitting')
            quit()
        self._logger.debug('parsing config file - COMPLETE')
        return
    
    def run_vision_and_sql_task_threads(self):
        """
        runs the vision task thread and sql task thread
        """
        vision_task_thread = None
        sql_task_thread = None
        try:
            vision_task_thread = threading.Thread(target=self._call_vision_thread())
            vision_task_thread.start()
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
                return True
            else:
                return False

    def convert_coordinates(self, in_x:float, in_y:float, in_coor:dict, out_coor:dict):
        """
        converts coordinates from the in_coor coordinate system to the out_coor coordinate system
        in_coor and out_coor are both dictionaries with north, east, south, and west values
        that correspond to the upper, right, lower, and left bounds of the pickable area
        returns the x and y values of "selected_item" in terms of 
        """
        # first, convert the x and y coordinates of the selected item so that they are independent of the input coordinate system
        # mid_x is the x coordinate of the item where 0.0 is the left edge of the pickable area and 1.0 is the right edge of the pickable area
        # mid_y is the y coordinate of the item where 0.0 is the top edge of the pickable area and 1.0 is the bottom edge of the pickable area
        mid_x = (in_x - in_coor['west'])  / (in_coor['east'] - in_coor['west'])
        mid_y = (in_y - in_coor['north']) / (in_coor['south'] - in_coor['north'])
        # out_x and out_y are the coordinates in terms of the output coordinate system
        out_x = mid_x * abs(out_coor['east'] - out_coor['west']) + out_coor['west']
        out_y = mid_y * abs(out_coor['south'] - out_coor['north']) + out_coor['north']
        return out_x, out_y

    def pick_and_place(self, arm_x:float, arm_y:float, arm_z:float, applied_rotation:float, drop_off):
        """
        sends all the commands to the robot to move it to the correct location, pick up the item, and drop it off at the correct location
        :arm_x: the x coordinate of the object that needs to be picked up, in terms of the coordinate system of the robot
        :arm_y: the y coordinate of the object that needs to be picked up, in terms of the coordinate system of the robot
        :arm_z: the z coordinate of the object that needs to be picked up, in terms of the coordinate system of the robot
        :applied_rotation: the rotation of the robot end effector, in radians. It will either be horizontal (0.0) or vertical (1.5708)
        :drop_off: a list of the coordinate that the picked item needs to be dropped off at. It will be one of the values of the sorting_coordinates dictionary
        """

        vertical_offset = 0.2 # the amount that the arm will 'hover' over the selected item

        # NOTE The coordinate values given to the robot are X Y Z ROLL PITCH YAW
        # NOTE The arm flips x and y

        # check if the object is within the bounds of the pickable area
        if (not (arm_x >= self.config_variables['arm_coordinates']['west']
                and arm_x <= self.config_variables['arm_coordinates']['east']
                    and arm_y >= self.config_variables['arm_coordinates']['north']
                        and arm_y <= self.config_variables['arm_coordinates']['south'])):
            print("Error appending instructions... Out of Bounds")
            # TODO self.main_loop_helper(requested_item)
            return

        # Move above the selected object
        self.robot.move_pose(arm_y, arm_x, arm_z + vertical_offset, applied_rotation, 1.4, 0)
        self.robot.release_with_tool()
        # grab the selected object
        self.robot.move_pose(arm_y, arm_x, arm_z, applied_rotation, 1.4, 0)
        self.robot.grasp_with_tool()
        # Move the robot back up above the pickable area
        self.robot.move_pose(arm_y, arm_x, arm_z + vertical_offset, applied_rotation, 1.4, 0)
        # Move to the drop off point and release the item
        self.robot.move_pose(drop_off)
        self.robot.release_with_tool()
        self.robot.grasp_with_tool()
        # Move Home
        self.robot.move_pose(sorting_coords["home"])

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
        images = self._vision_thread.retrieve_images()
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

    def main_loop_helper(self, requested_item):
        """
        Helper function for some repeated end of loop code.
        """
        message = 'Requesting Object: %s' % requested_item.item_type
        time.sleep(5)
        self._object_removed_successfully = False
        self._object_not_found = False


if __name__ == '__main__':
    main_thread = Main()
    main_thread.main_loop()
