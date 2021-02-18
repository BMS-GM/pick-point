#!/usr/bin/env python
"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

Depth Mapping Thread
*** NOT FULLY IMPLEMENTED ***

DepthMapThread.py
Author: Shaun Flynn
Date Last Modified 4/23/2019
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'

import threading
import numpy as np
import logging
import copy

import cv2 as cv2
import PySpin
import os
from matplotlib import pyplot
from CameraDriver.SpinCameraDriver import SpinCameraDriver


class DepthMapThread(threading.Thread):

    def __init__(self, left_image, right_image):
        """
        Class Constructor. This also automatically starts the thread
        :param left_image: the left image in a stereo pair
        :param right_image: the right image in a stereo pair
        """
        # Setup Threading
        super(DepthMapThread, self).__init__()       # Initialize Thread
        self._image_ready_event = threading.Event()
        self._image_ready_event.clear()
        self._image_returned_event = threading.Event()
        self._image_returned_event.clear()

        self._left_image = left_image
        self._right_image = right_image
        self._result = None

        # init the logger
        self._logger = logging.getLogger('GM_Pick_Point.' + self.__class__.__name__)

        self.start()

    def run(self):
        """
        Main Thread Function
        """
        self._logger.debug("Running Depth Map Thread...")
        #self._logger.warning("Depth Mapping is not implemented - Setting result matrix to zero")

        rows = self._left_image.shape[0]
        cols = self._left_image.shape[1]

        self._result = np.zeros((rows, cols))
        self._image_ready_event.set()
        self._logger.debug("Depth Map - COMPLETE | Waiting for result to be requested")
        self._image_returned_event.wait()

    def get_image(self):
        """
        Force Calling Thread to wait until an depth matrix (image) is ready
        :return: A Depth Map
        """
        self._logger.info("Requesting Depth Map Result")
        self._logger.info("Waiting For Image To Be Ready")
        self._image_ready_event.wait()
        image = copy.deepcopy(self._result)
        self._image_returned_event.set()
        self._logger.info("Retrieved Image")
        return image

    def terminate_thread(self):
        """
        Request the thread to terminate
        """
        self._image_returned_event.set()
        self._image_ready_event.set()


