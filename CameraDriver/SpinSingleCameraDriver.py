#!/usr/bin/env python
"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

Driver to connect to a Spinnaker compatible camera

SpinSCameraThread.py
Author: Shaun Flynn
Date Last Modified 4/23/2019
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'

import sys
import logging
import threading
import PySpin
import copy

from CameraDriver.SpinCameraDriver import SpinCameraDriver


class SpinSingleCameraDriver(threading.Thread):
    """
     Camera Driver Class Compatible with Spinnaker
    """

    def __init__(self, camera_id):
        """
        Constructor
        :param camera_id: the id of the camera
        
        """

        super(SpinSingleCameraDriver, self).__init__()  # Call parent's constructor

        # Setup Logging
        self._logger = logging.getLogger('GM_Pick_Point.' + self.__class__.__name__)

        # Setup Multi Threading
        self._lock = threading.Lock()
        self._request_images_event = threading.Event()
        self._images_acquired_event = threading.Event()
        self._terminate_thread = threading.Event()
        self._request = None
        self._acquired_images = None

        # Spinnaker Objects
        self._system = None
        self._driver = None

        self._init_cameras(camera_id)

    def __del__(self):
        """
        Deconstuctor
        Ensure that all system objects are destroyed and all resources are returned to avoid memory leaks
        """
        del self._driver
        self._system.ReleaseInstance()
        del self._system

    def terminate_thread(self):
        """
        Request Thread Termination
        """
        self._logger.info("Terminating Thread...")
        self._terminate_thread.set()

    def _init_cameras(self, camera_id):
        """
        init the camera connections
        :param camera_id: Unique ID of the camera
        
        """

        # init camera drivers
        self._logger.info("Initializing Drivers...")
        self._system = PySpin.System.GetInstance()
        cam_list = self._system.GetCameras()

        drivers = []
        for camera in cam_list:
            drivers.append(SpinCameraDriver(camera))
        self._logger.info("Initializing Drivers - COMPLETE")

        # Find Our Camera
        self._logger.info("Finding Camera...")
        for driver in drivers:
            info = driver.get_info()
            if info[1] == camera_id:
                self._driver = driver
                self._logger.info(" Camera - FOUND\n"
                                  "\t Serial Number: %s\n"
                                  "\t Vendor Name  : %s\n"
                                  "\t Display Name : %s"
                                  % (info[1], info[2], info[3]))

        if self._driver is None:
            self._logger.error("Unable to find Camera - EXITING")
            self._logger.info("Cleaning Up System ...")
            for driver in drivers:
                del driver
            del drivers
            del self._driver

            for camera in cam_list:
                del camera
            del cam_list

            self._system.ReleaseInstance()
            del self._system
            self._logger.info("Cleaning Up System - COMPLETE")
            sys.exit()

        # Release Unused Cameras:
        self._logger.info("Releasing Unused Cameras...")
        for driver in drivers:
            del driver
        del drivers

        for camera in cam_list:
            del camera
        del cam_list
        self._logger.info("Releasing Unused Cameras - COMPLETE")

    def run(self):
        """
        Main Thread Routine
        """
        self._logger.debug('Thread Started')
        self._main_loop()
        self._logger.debug('Thread Terminated')

    def _main_loop(self):
        """
        Main thread loop
        Exit when a termination request event is set or on an error
        """

        # Enter the main loop
        self._logger.debug('Entering Main Loop')
        while not self._terminate_thread.is_set():
            images_pending = self._request_images_event.wait(0.5)
            if images_pending:
                self._logger.debug('Processing Request...')
                self._request_images_event.clear()
                self._request[0](*self._request[1])
                self._logger.debug('Processing Request - COMPLETE')
                self._images_acquired_event.set()

    def get_images(self, num_images):
        """
        External facing method to get images from the driver thread
        :param num_images: the number of images
        :return: A list containing images
        """

        # Wait to acquire the thread access lock
        self._logger.debug('Requesting %d new images' % num_images)
        with self._lock:

            self._request = (self._get_images, (num_images,))           # Set request
            self._images_acquired_event.clear()                         # Clear the acquired event before waiting on it
            self._request_images_event.set()                            # Notify the driver thread that a request has
                                                                        # been made
            self._images_acquired_event.wait()                          # Wait for request to be processed
            result = copy.deepcopy(self._acquired_images)
        return result

    def _get_images(self, num_images):
        """
        Internal facing method to get images
        :param num_images: the number of images to get
        :return: A list of images
        """
        self._logger.info("Acquiring %d images..." % num_images)
        result = []
        images = num_images
        while images > 0:
            # get image
            try:
                image = self._driver.get_image(1)[0]
            except IndexError:
                continue

            result.append(image)
            images -= 1

        self._logger.info("Acquiring %d simages - COMPLETE" % num_images)
        self._acquired_images = result

