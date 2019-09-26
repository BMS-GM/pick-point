#!/usr/bin/env python
"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

Driver to connect to a stereo pair of Spinnaker compatible cameras
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'

import sys
import logging
import threading
import pyspin.PySpin as PySpin
import copy

from CameraDriver.StereoCameraThread import StereoCameraThread
from CameraDriver.SpinCameraDriver import SpinCameraDriver


class SpinStereoCameraDriver(StereoCameraThread):
    """
    Stereo Camera Driver Class Compatible with Spinnaker
    """

    def __init__(self, left_camera_id, right_camera_id):
        """
        Constructor
        :param left_camera_id: the id of the left camera in a stereo pair
        :param right_camera_id: the id of the right camera in a stereo pair
        """

        super(SpinStereoCameraDriver, self).__init__()  # Call parent's constructor

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
        self._left_driver = None
        self._right_driver = None

        self._init_cameras(left_camera_id, right_camera_id)

    def __del__(self):
        """
        Deconstuctor
        Ensure that all system objects are destroyed and all resources are returned to avoid memory leaks
        """
        del self._left_driver
        del self._right_driver
        self._system.ReleaseInstance()
        del self._system

    def terminate_thread(self):
        """
        Request Thread Termination
        """
        self._logger.info("Terminating Thread...")
        self._terminate_thread.set()

    def _init_cameras(self, left_camera_id, right_camera_id):
        """
        init the camera connections
        :param left_camera_id: Unique ID of the left camera
        :param right_camera_id: Unique ID of the Right camera
        """

        # init camera drivers
        self._logger.info("Initializing Drivers...")
        self._system = PySpin.System.GetInstance()
        cam_list = self._system.GetCameras()

        drivers = []
        for camera in cam_list:
            drivers.append(SpinCameraDriver(camera))
        self._logger.info("Initializing Drivers - COMPLETE")

        # Find Left Camera
        self._logger.info("Finding Left Camera...")
        for driver in drivers:
            info = driver.get_info()
            if info[1] == left_camera_id:
                self._left_driver = driver
                self._logger.info("Left Camera - FOUND\n"
                                  "\t Serial Number: %s\n"
                                  "\t Vendor Name  : %s\n"
                                  "\t Display Name : %s"
                                  % (info[1], info[2], info[3]))

        if self._left_driver is None:
            self._logger.error("Unable to find Left Camera - EXITING")
            self._logger.info("Cleaning Up System ...")
            for driver in drivers:
                del driver
            del drivers
            del self._left_driver
            del self._right_driver

            for camera in cam_list:
                del camera
            del cam_list

            self._system.ReleaseInstance()
            del self._system
            self._logger.info("Cleaning Up System - COMPLETE")
            sys.exit()

        # Find Right Camera
        self._logger.info("Finding Right Camera...")
        for driver in drivers:
            info = driver.get_info()
            if info[1] == right_camera_id:
                self._right_driver = driver
                self._logger.info("Right Camera - FOUND\n"
                                  "\t Serial Number: %s\n"
                                  "\t Vendor Name  : %s\n"
                                  "\t Display Name : %s"
                                  % (info[1], info[2], info[3]))

        if self._right_driver is None:
            self._logger.error("Unable to find Right Camera - EXITING")
            self._logger.info("Cleaning Up System ...")
            for driver in drivers:
                del driver
            del drivers
            del self._left_driver
            del self._right_driver

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

    def get_stereo_images(self, num_images):
        """
        External facing method to get a stereo image pair from the driver thread
        :param num_images: the number of image pairs
        :return: A list containing image pair tuples
        """

        # Wait to acquire the thread access lock
        self._logger.debug('Requesting %d new stereo images' % num_images)
        with self._lock:

            self._request = (self._get_stereo_images, (num_images,))    # Set request
            self._images_acquired_event.clear()                         # Clear the acquired event before waiting on it
            self._request_images_event.set()                            # Notify the driver thread that a request has
                                                                        # been made
            self._images_acquired_event.wait()                          # Wait for request to be processed
            result = copy.deepcopy(self._acquired_images)
        return result

    def get_mono_images(self, num_images, camera_to_use='RANDOM'):
        """
        External facing method to retrieve images from ONE of the stereo cameras
        :param num_images: Number of images to acquire
        :param camera_to_use: Which camera should be used to get the images
        :return: A list of images
        """
        # Wait to acquire the thread access lock
        self._logger.debug('Requesting %d new mono images from %s camera' % (num_images, camera_to_use))
        with self._lock:
            self._request = (self._get_mono_images, (num_images, camera_to_use))    # Set request
            self._images_acquired_event.clear()                                     # Clear the acquired event before
                                                                                    # waiting on it
            self._request_images_event.set()                                        # Notify the driver thread that a
                                                                                    # request has been made
            self._images_acquired_event.wait()                                      # Wait for request to be processed
            result = copy.deepcopy(self._acquired_images)
        return result

    def _get_stereo_images(self, num_images):
        """
        Internal facing method to get a stereo image pair
        :param num_images: the number of PAIRS to get
        :return: A list of image pair tuples
        """
        self._logger.info("Acquiring %d stereo image pairs..." % num_images)
        result = []
        images_left = num_images
        while images_left > 0:
            # get left image
            try:
                left_image = self._left_driver.get_image(1)[0]
            except IndexError:
                continue

            # get right image
            try:
                right_image = self._right_driver.get_image(1)[0]
            except IndexError:
                continue

            result.append((left_image, right_image))
            images_left -= 1

        self._logger.info("Acquiring %d stereo image pairs - COMPLETE" % num_images)
        self._acquired_images = result

