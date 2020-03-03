#!/usr/bin/env python
"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

Abstract class for camera drivers

CameraDriver.py
Author: Shaun Flynn
Date Last Modified 2/18/2019
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'


class CameraDriver:
    """
    Abstract Class
    """

    def get_image(self, num_images):
        """
        Abstract method to obtain images from a camera
        :param num_images: the number of images to obtain
        :return: a list of images
        """
        raise NotImplementedError('Methods get_image is not defined')

    def get_info(self):
        """
        Abstract method to obtain camera information
        :return: a formatted string of camera information
        """
        raise NotImplementedError('Methods get_info is not defined')
