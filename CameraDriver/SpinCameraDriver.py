#!/usr/bin/env python
"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

Driver to connect to Spinnaker compatible cameras
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'

import sys
import datetime
import PySpin
import numpy as np
import cv2
import logging

from CameraDriver import CameraDriver


class SpinCameraDriver(CameraDriver.CameraDriver):
    def __init__(self, camera):
        """
        SpinCameraDriver Constructor
        :param camera: The Spinnaker compatible camera this diver will connect to
        """
        # init the logger
        self._logger = logging.getLogger('GM_Pick_Point.' + self.__class__.__name__ + '.Camera:' + str(camera.GetUniqueID()))
        self._logger.debug('Initializing Camera %s ...' % str(camera.GetUniqueID()))

        # Setup camera to take pictures based on a software trigger
        self._camera = camera
        self._camera.Init()
        self._camera.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
        self._set_trigger_mode_software()

        self._logger.debug('Initialization Complete')

    def _set_trigger_mode_software(self):
        """
        Sets the camera to be software triggered
        :return: N/A
        """
        self._logger.debug("Setting Trigger Mode Software")
        self._camera.TriggerMode.SetValue(PySpin.TriggerMode_Off)
        self._camera.TriggerSource.SetValue(PySpin.TriggerSource_Software)
        self._camera.TriggerMode.SetValue(PySpin.TriggerMode_On)
        self._logger.debug("Set Trigger Mode Software Complete")

    def _reset_trigger_mode_software(self):
        """
        Reset the camera's trigger mode to the default mode (Off)
        :return: N/A
        """
        self._camera.TriggerMode.SetValue(PySpin.TriggerMode_Off)
        self._logger.debug("reset trigger mode")

    def get_image(self, num_images):
        """
        Obtains a set of images form the connected camera
        :param num_images: the number of images to take
        :return: a list of images that is <= num_images
        """
        self._logger.debug('Getting Images from Camera %s ...' % str(self._camera.GetUniqueID()))
        result = []                         # resulting list of images
        self._camera.BeginAcquisition()     # Start acquiring images

        # Attempt to take all images
        for img_num in range(num_images):
            self._logger.debug('Getting Image %d...' % img_num)
            self._camera.TriggerSoftware()
            img = self._camera.GetNextImage()

            # Check if the image was correctly received
            if img.IsIncomplete():
                self._logger.warning('Camera %s Image %d Is Incomplete - Skipping'
                                     % (str(self._camera.GetUniqueID(), img_num)))
                pass
            else:
                self._logger.debug('Image %d Obtained' % img_num)
                # see documentation: enum ColorProcessingAlgorithm
                image_converted = img.Convert(PySpin.PixelFormat_BGR8, PySpin.DIRECTIONAL_FILTER)
                image_data = image_converted.GetData()

                # Convert the image to be compatible with OpenCV
                self._logger.debug('Converting Image %d For OpenCV' % img_num)
                cvi = np.frombuffer(image_data, dtype=np.uint8)
                cvi = cvi.reshape((img.GetHeight(), img.GetWidth(), 3))

                # Add the resulting image to the result list
                result.append(cvi)
                self._logger.debug('Image %d Complete' % img_num)

            # Release and delete the image reference
            img.Release()
            del img

        # Stop acquiring images
        self._camera.EndAcquisition()
        self._logger.debug('Image Acquisition Compete')
        return result

    def __del__(self):
        """
        SpinCameraDriver Deconstructor
        :return: N/A
        """
        self._logger.debug('Deleting Camera %s ...' % str(self._camera.GetUniqueID()))

        # Clean up camera references
        self._reset_trigger_mode_software()
        self._camera.DeInit()
        del self._camera

        self._logger.debug('Camera Successfully Deleted')


if __name__ == '__main__':

    # =================================
    # Setup Logging
    # =================================
    # Create master logger and set global log level
    logger = logging.getLogger("GM_Pick_Point")
    logger.setLevel(logging.DEBUG)

    # create log file
    file_handler = logging.FileHandler('SpinCameraDriver - %s.log' %
                                       datetime.datetime.now().strftime("%Y.%m.%d-%H.%M.%S"))
    file_handler.setLevel(logging.DEBUG)

    # create console logger
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Format Log
    log_formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(name)s - %(message)s')
    file_handler.setFormatter(log_formatter)
    console_handler.setFormatter(log_formatter)

    # Add outputs to main logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    # =====================================================================
    
    # Get a list of all cameras on the system
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()
    logger.debug("number of cameras {}".format(cam_list.GetSize()))
    
    if cam_list.GetSize() == 0:
        logger.error("no cameras found, aborting")
        system.ReleaseInstance()
        del system
        sys.exit()

    cameras = []

    # For each camera make a camera driver to get images
    for i in range(cam_list.GetSize()):
        cam = cam_list.GetByIndex(i)
        logger.debug("camera {} serial: {}".format(i, cam.GetUniqueID()))
        driver = SpinCameraDriver(cam)
        images = driver.get_image(1)

        # save each image obtained then display it
        for j, image in enumerate(images):
            cv2.imwrite('cam - %s - %d.png' % (cam.GetUniqueID(), j), image)    # Save the Image
            cv2.imshow('cam - %s - %d.png' % (cam.GetUniqueID(), j), image)     # Display the image
            cv2.waitKey(0)                                                      # Wait for the 'ESC' key to be pressed
            cv2.destroyAllWindows()                                             # Close the preview window

        # Delete the camera and driver
        del driver
        del cam

    # delete all references to the cameras
    del cameras
    del cam_list

    # clean up the system
    system.ReleaseInstance()
    del system
