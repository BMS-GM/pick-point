#!/usr/bin/env python
"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

Vision Thread Class

Vision Thread Class.py
Author: Shaun Flynn
Date Last Modified 2/18/2019
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'

import threading
import numpy as np
import logging
import copy
import cv2
import skimage
import os
import PySpin
from matplotlib import pyplot as plt
import sys
import datetime
import time
import traceback

from CameraDriver.SpinSingleCameraDriver import SpinSingleCameraDriver
from CameraDriver.SpinCameraDriver import SpinCameraDriver
from NeuralNetwork import MachineLearningThread
from Item import Item
from NeuralNetwork.NeuralNetwork import Network

REMAP_INTERPOLATION = cv2.INTER_LINEAR
DEPTH_VISUALIZATION_SCALE = 8192 * 2

SHOW_FPS = False

class VisionThread(threading.Thread):

    """
    Define the Initialization of the Vision Thread
    self - the definition of the thread
    camera_id - the id of the camera
    network_model - the neural network model
    log_dir - Where the log file is stored
    downscale_ratio - How much to scale down the images by
    """
    def __init__(self, camera_id, network_model, log_dir, downscale_ratio):
        """
        Constructor
        :param camera_id:       ID of the camera 
        :param network_model:   The type of network model to use for object detection
        :param log_dir:         The directory to place log files in for TensorFlow
        :param downscale_ratio: The image down sampling percentage [1 - 0)
        """
        # Setup Threading
        super(VisionThread, self).__init__()       # Initialize Thread

        # init the logger
        self._logger = logging.getLogger('GM_Pick_Point.' + self.__class__.__name__)

        # Setup Multi-threading
        self._terminate_thread_event = threading.Event()  # Event used to stop the thread

        self._logger.debug('Initializing Camera Thread')
        self._camera_thread = SpinSingleCameraDriver(camera_id)
        self._camera_result = None
        self._camera_result_lock = threading.Lock()

        self._logger.debug('Initializing Machine Learning Thread')
        self._machine_learning_thread = MachineLearningThread.MachineLearningThread(log_dir, graph_type=network_model)
        self._machine_learning_result = None
        self._last_object_count = dict()
        self._current_object_count = dict()
        self._machine_learning_result_lock = threading.Lock()
        self._downscale_ratio = downscale_ratio
        self._average_time = 0.0
        self._iteration = -1        # Skip the first Frame (first frame includes load time)
        self._current_x = None
        self._current_y = None

        # visualization settings:
        self._visualization_settings_lock = threading.RLock()
        self._display_results = True
        self._class_label_to_show = "None"
        self._max_labels = 1
        self._display_class_name = False
        self._display_score = False

        self.img_counter = 0

        self._item_list = []
        self._item_list_lock = threading.Lock()

        self._logger.debug('Threads Initialized')

    """
    Run the thread
    self - the self of the thread
    """
    def run(self):
        """
        Main thread function
        """
        self._logger.debug('Starting Thread')
        self._main_loop()
        self._logger.debug('Terminated Thread')

    """
    Get the identified result
    self - the self of the thread
    """
    def get_machine_learning_result(self):
        """
        External facing function to get the latest results about detected objects
        :return: a TF result vector
        """
        with self._machine_learning_result_lock:
            result = copy.deepcopy(self._machine_learning_result)
        return result

    """
    Get the image from the camera
    self - the self of the thread
    """
    def retrieve_images(self):
        """
        External facing function to get the latest image
        :return: an image
        """
        with self._camera_result_lock:
            result = copy.deepcopy(self._camera_result)
        return result

    """
    Get the list of detected items and the positions
    self - the self of the thread
    """
    def get_items(self):
        """
        External facing method to get the latest list of detected items and their positions
        :return: a list of Items
        """
        with self._item_list_lock:
            result = copy.deepcopy(self._item_list)
        return result

    """
    Kill the thread
    self - the self of the thread
    """
    def terminate_thread(self):
        """
        External facing method to request termination of this thread
        """
        self._logger.debug("Requesting Termination")
        self._terminate_thread_event.set()

    """
    Loop the thread to keep it running
    self - the self of the thread
    """
    def _main_loop(self):
        """
        Main loop of this thread. Terminate on termination request or on error
        """
        self._logger.debug('Starting Machine Learning Thread')
        self._machine_learning_thread.start()
        self._logger.debug('Starting Camera Thread')
        self._camera_thread.start()

        try:
            while not self._terminate_thread_event.is_set():

                # Get image
                start_time = time.time()
                image = self._camera_thread.get_images(1)[0]

                # If Calibration is needed, collect data
                calibration = False

                # Save images for Calibration
                if (calibration):
                    img_name1 = os.getcwd() + "\calibration\cam_0_images\cam_0_frame_{}.png".format(self.img_counter)
                    cv2.imwrite(img_name1, image)
                    imageName = img_name1

                # Grab the image
                img_name = os.getcwd() + "\images\capture\cam_0_frame_{}.png".format(self.img_counter)
                cv2.imwrite(img_name, image)
                imageName = img_name

                # Read Image
                imgL = cv2.imread(imageName)

                self.img_counter = self.img_counter + 1

                with self._camera_result_lock:
                    self._camera_result = (image)
                
                # process images

                downscaled_img = cv2.resize(image, (0, 0), fx=self._downscale_ratio, fy=self._downscale_ratio)
                ml_result = self._machine_learning_thread.process_image(downscaled_img)

                with self._machine_learning_result_lock:
                    self._machine_learning_result = ml_result

                self._process_results()

                with self._visualization_settings_lock:
                    if self._display_results:
                        self._display_machine_learning_result(image)
                delta_time = time.time() - start_time
                sum = self._average_time * self._iteration
                self._iteration += 1.0
                if self._iteration > 0:
                    self._average_time = float(sum + delta_time) / self._iteration

        except Exception:
            # Pass on error
            tb = traceback.format_exc()
            self._logger.error('Unhandled Exception:\n%s' % str(tb))
            self._logger.error('Terminating All Threads')

        finally:
            # Join all threads
            self._logger.debug('Joining Machine Learning Thread')
            self._machine_learning_thread.terminate_thread()
            self._machine_learning_thread.join()
            self._logger.debug('Joining Camera Thread')
            self._camera_thread.terminate_thread()
            self._camera_thread.join()
            self._logger.debug('Joining Depth Map Thread')

    """
    Process the camera results
    self - the self of the thread
    """
    def _process_results(self):
        """
        Process results from the camera
        """

        ml_results = self.get_machine_learning_result()

        ml_items = Network.get_item_locations(ml_results)
        items = []
        for item in ml_items:
            x = item.x
            y = item.y
            z = 0
            item.z = z
            items.append(item)

        with self._item_list_lock:
            self._item_list = items

    """
    Set the settings of the  thread's visual settings
    self - the self of the thread
    label_to_show - The name of the object to highlight. ALL - All objects are highlighted
    max_labels - The maximum number of objects to highlight
    display_class_name - True - display the names of the all highlighted objects
    display_score - True - Display the prediction score of all highlighted objects
    """
    def set_visualization_settings(self, display_results, label_to_show, max_labels, display_class_name, display_score):
        """
        Configure the OpenCV live image display
        :param display_results:      True - Displays a live feed from the camera, False - No live feed
        :param label_to_show:       The name of the object to highlight. ALL - All objects are highlighted
        :param max_labels:          The maximum number of objects to highlight
        :param display_class_name:  True - display the names of the all highlighted objects
        :param display_score:       True - Display the prediction score of all highlighted objects
        :return:
        """
        with self._visualization_settings_lock:
            self._display_results = display_results
            self._class_label_to_show = label_to_show
            self._max_labels = max_labels
            self._display_class_name = display_class_name
            self._display_score = display_score

    """
    Display the live display of highlighting
    self - the self of the thread
    image - image to be shown
    """
    def _display_machine_learning_result(self, image):
        """
        Internal facing function to update the live display
        :param image: the next frame
        """
        ml_result = self.get_machine_learning_result()

        with self._visualization_settings_lock:
            result, self._current_x, self._current_y = Network.visualize_output(image, ml_result, label=self._class_label_to_show, max_labels=self._max_labels,
                                              display_class_name=self._display_class_name, display_score=self._display_score)
            result = cv2.resize(result, (0, 0), fx=0.5, fy=0.5)
            if SHOW_FPS:
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(result, '%0.4f seconds/frame' % self._average_time, (0, 30), font, 1, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.imshow('GM Pick-Point', result)
            print("Vision Thread X: {}".format(self._current_x))
            print("Vision Thread Y: {}".format(self._current_y))
            cv2.waitKey(1)                      # DO NOT REMOVE: For some reason this works

    def _get_x(self):
        print("Vision Thread X: {}".format(self._current_x))
        return self._current_x

    def _get_y(self):
        print("Vision Thread Y: {}".format(self._current_y))
        return self._current_y

# Logging Parameters
if __name__ == '__main__':
    # =================================
    # Setup Logging
    # =================================
    # Create master logger and set global log level
    log_dir = "C:\\Users\\jmjerred-adm\\PycharmProjects\\pick-point\\Logs"
    logger = logging.getLogger("GM_Pick_Point")
    logger.setLevel(logging.DEBUG)

    # create log file
    file_handler = logging.FileHandler(log_dir + 'MachineLearningThread - %s.log' %
                                       datetime.datetime.now().strftime("%Y.%m.%d-%H.%M.%S"))
    file_handler.setLevel(logging.DEBUG)

    # create console logger
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Format Log
    log_formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(name)s - %(message)s')
    file_handler.setFormatter(log_formatter)
    console_handler.setFormatter(log_formatter)

    # Add outputs to main logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    # =====================================================================

    LOG_DIR = 'Logs'
    CAMERA_SERIAL_NUM = '18585124'

    GRAPH_TYPE = 'SSD_INCEPTION_V2'

    logger.debug('Initializing Vision Thread...')
    visionThread = VisionThread(CAMERA_SERIAL_NUM, GRAPH_TYPE, LOG_DIR)
    logger.debug('Initializing Vision Thread - COMPLETE')

    logger.debug('Starting Vision Thread...')
    visionThread.start()
    visionThread.set_visualization_settings(True, "ALL", float("inf"), True, True)
    logger.debug('Starting Vision Thread - COMPLETE')

    logger.debug('Sleeping for 30 seconds')
    time.sleep(30)
    logger.debug('Woke Up')

    logger.debug('Terminating Vision Thread...')
    visionThread.terminate_thread()
    visionThread.join()
    logger.debug('Terminating Vision Thread - COMPLETE')
