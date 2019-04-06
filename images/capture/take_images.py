#!/usr/bin/env python
"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

Capture Images
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'

import os
import cv2
import numpy as np
import PySpin
import sys
import time
import random
import logging
import datetime

from CameraDriver.SpinCameraDriver import SpinCameraDriver

from item_randomizer import *

FONT = cv2.FONT_HERSHEY_SIMPLEX
LEFT_CAMERA_SERIAL_NUM = "18585124"
RIGHT_CAMERA_SERIAL_NUM = "18585121"
run_name = time.strftime("%Y-%m-%d_%H-%M-%S")


def save_stereo_images(img_l, img_r, iteration):
    save_dir = "C:/Users\jmjerred-adm\PycharmProjects\pick-point\images\capture\stereo_captures\Run_{}".format(run_name)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    img_name_r = "{}\cam_frame_{}_{}_right.png".format(save_dir, run_name, iteration)
    img_name_l = "{}\cam_frame_{}_{}_left.png".format(save_dir, run_name, iteration)
    cv2.imwrite(img_name_r, img_r)
    cv2.imwrite(img_name_l, img_l)


def save_mono_images(img_r, img_l, iteration):
    save_dir = "C:/Users\jmjerred-adm\PycharmProjects\pick-point\images\capture\mono_captures\Run_{}".format(run_name)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    img_name_mono = "{}\cam_frame_{}_{}.png".format(save_dir, run_name, iteration)
    if random.randint(0, 1) == 0:
        cv2.imwrite(img_name_mono, img_r)
    else:
        cv2.imwrite(img_name_mono, img_l)


if __name__ == "__main__":
    # =================================
    # Setup Logging
    # =================================
    # Create master logger and set global log level
    logger = logging.getLogger("GM_Pick_Point")
    logger.setLevel(logging.DEBUG)

    # create log file
    file_handler = logging.FileHandler('Take Images - %s.log' %
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
    logger.info("Getting Cameras")
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()

    logger.info("Initializing Drivers...")
    drivers = []
    for camera in cam_list:
        drivers.append(SpinCameraDriver(camera))
    logger.info("Initializing Drivers - COMPLETE")

    # Find Cameras
    left_driver = None
    right_driver = None

    # Find Left Camera
    logger.info("Finding Left Camera...")
    for driver in drivers:
        info = driver.get_info()
        if info[1] == LEFT_CAMERA_SERIAL_NUM:
            left_driver = driver
            logger.info("Left Camera - FOUND\n"
                        "\t Serial Number: %s\n"
                        "\t Vendor Name  : %s\n"
                        "\t Display Name : %s"
                        % (info[1], info[2], info[3]))

    if left_driver is None:
        logger.error("Unable to find Left Camera - EXITING")
        logger.info("Cleaning Up System ...")
        for driver in drivers:
            del driver
        del drivers
        del left_driver
        del right_driver

        for camera in cam_list:
            del camera
        del cam_list

        system.ReleaseInstance()
        del system
        logger.info("Cleaning Up System - COMPLETE")
        sys.exit()

    # Find Right Camera
    logger.info("Finding Right Camera...")
    for driver in drivers:
        info = driver.get_info()
        if info[1] == RIGHT_CAMERA_SERIAL_NUM:
            right_driver = driver
            logger.info("Right Camera - FOUND\n"
                        "\t Serial Number: %s\n"
                        "\t Vendor Name  : %s\n"
                        "\t Display Name : %s"
                        % (info[1], info[2], info[3]))

    if right_driver is None:
        logger.error("Unable to find Right Camera - EXITING")
        logger.info("Cleaning Up System ...")
        for driver in drivers:
            del driver
        del drivers
        del left_driver
        del right_driver

        for camera in cam_list:
            del camera
        del cam_list

        system.ReleaseInstance()
        del system
        logger.info("Cleaning Up System - COMPLETE")
        sys.exit()

    # Release Unused Cameras:
    for driver in drivers:
        if (driver is not right_driver) and (driver is not left_driver):
            del driver
    del drivers

    drivers = [left_driver, right_driver]

    parts = get_rand_items_sorted()

    image_cam_0 = np.zeros((1024, 1280, 3), np.uint8)
    image_cam_1 = np.zeros((1024, 1280, 3), np.uint8)

    capture_iteration = 0
    while True:

        # Get Cam_0
        try:
            image_cam_0 = drivers[0].get_image(1)[0]
        except IndexError:
            image_cam_0 = np.zeros((1024, 1280, 3), np.uint8)
            text = "LOST CONNECTION"
            textsize = cv2.getTextSize(text, FONT, 4, 4)[0]
            textX = int((image_cam_0.shape[1] - textsize[0]) / 2)
            textY = int((image_cam_0.shape[0] + textsize[1]) / 2)

            cv2.putText(image_cam_0, text, (textX, textY), FONT, 4, (255, 255, 255), 4)
            cv2.line(image_cam_0, (0, 0), (1280, 1024), (150, 150, 150), 5)
            cv2.line(image_cam_0, (1280, 0), (0, 1024), (150, 150, 150), 5)

        # Get Cam_1
        try:
            image_cam_1 = drivers[1].get_image(1)[0]
        except IndexError:
            image_cam_1 = np.zeros((1024, 1280, 3), np.uint8)
            text = "LOST CONNECTION"
            textsize = cv2.getTextSize(text, FONT, 4, 4)[0]
            textX = int((image_cam_1.shape[1] - textsize[0]) / 2)
            textY = int((image_cam_1.shape[0] + textsize[1]) / 2)

            cv2.putText(image_cam_1, text, (textX, textY), FONT, 4, (255, 255, 255), 4)
            cv2.line(image_cam_1, (0, 0), (1280, 1024), (150, 150, 150), 5)
            cv2.line(image_cam_1, (1280, 0), (0, 1024), (150, 150, 150), 5)


        numpy_horizontal = np.hstack((image_cam_0, image_cam_1))
        numpy_horizontal_small = cv2.resize(numpy_horizontal, (0,0), fx=0.5, fy=0.5)

        text_y = 20
        text_delta_y = 30
        text_x = 10
        text_height = numpy_horizontal_small.shape[0]
        text_width = 200
        text_img = np.zeros((text_height, text_width, 3), np.uint8)
        for part in parts:
            cv2.putText(text_img, part, (text_x, text_y), FONT, 1, (255, 255, 255), 0)
            text_y += text_delta_y

        final_image = np.hstack((numpy_horizontal_small, text_img))
        cv2.imshow("Live Feed", final_image)

        k = cv2.waitKey(1)
        if k % 256 == 27:
            # ESC pressed
            logger.info("Escape hit, exiting...")
            break

        elif k % 256 == 32:
            # SPACE pressed
            save_mono_images(image_cam_0, image_cam_1, capture_iteration)
            save_stereo_images(image_cam_0, image_cam_1, capture_iteration)
            logger.info("Images Saved - {}_{}".format(run_name, capture_iteration))
            capture_iteration += 1
            parts = get_rand_items_sorted()

    # delete all references to the cameras
    logger.info("Cleaning Up System ...")
    for driver in drivers:
        del driver
    del drivers

    del right_driver
    del left_driver

    for camera in cam_list:
        del camera
    del cam_list

    # clean up the system
    system.ReleaseInstance()
    del system
    logger.info("Cleaning Up System - COMPLETE")

