import numpy as np
import cv2
import glob
import logging
import sys
import datetime

import PySpin

from CameraDriver.SpinCameraDriver import SpinCameraDriver


LEFT_CAMERA_SERIAL_NUM = "18585124"
RIGHT_CAMERA_SERIAL_NUM = "18585121"


FONT = cv2.FONT_HERSHEY_SIMPLEX


class StereoCalibration:
    def __init__(self):
        # termination criteria
        self.criteria = (cv2.TERM_CRITERIA_EPS +
                         cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        self.criteria_cal = (cv2.TERM_CRITERIA_EPS +
                             cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-5)

        # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
        self.objp = np.zeros((9*6, 3), np.float32)
        self.objp[:, :2] = np.mgrid[0:9, 0:6].T.reshape(-1, 2)

        # Arrays to store object points and image points from all the images.
        self.objpoints = []  # 3d point in real world space
        self.imgpoints_l = []  # 2d points in image plane.
        self.imgpoints_r = []  # 2d points in image plane.

    def show_grid(self, img_l, img_r):

        gray_l = cv2.cvtColor(img_l, cv2.COLOR_BGR2GRAY)
        gray_r = cv2.cvtColor(img_r, cv2.COLOR_BGR2GRAY)

        # Find the chess board corners
        ret_l, corners_l = cv2.findChessboardCorners(gray_l, (9, 6), None)
        ret_r, corners_r = cv2.findChessboardCorners(gray_r, (9, 6), None)

        # If found, add object points, image points (after refining them)
        self.objpoints.append(self.objp)

        if ret_l is True:
            rt = cv2.cornerSubPix(gray_l, corners_l, (11, 11),
                                  (-1, -1), self.criteria)
            self.imgpoints_l.append(corners_l)

            # Draw and display the corners
            ret_l = cv2.drawChessboardCorners(img_l, (9, 6),
                                              corners_l, ret_l)

        if ret_r is True:
            rt = cv2.cornerSubPix(gray_r, corners_r, (11, 11),
                                  (-1, -1), self.criteria)
            self.imgpoints_r.append(corners_r)

            # Draw and display the corners
            ret_r = cv2.drawChessboardCorners(img_r, (9, 6),
                                              corners_r, ret_r)

        return ret_l, ret_r

    def read_images(self, imgs_l, imgs_r):

        for i, _ in enumerate(imgs_r):
            img_l = imgs_l[i]
            img_r = imgs_r[i]

            gray_l = cv2.cvtColor(img_l, cv2.COLOR_BGR2GRAY)
            gray_r = cv2.cvtColor(img_r, cv2.COLOR_BGR2GRAY)

            # Find the chess board corners
            ret_l, corners_l = cv2.findChessboardCorners(gray_l, (9, 6), None)
            ret_r, corners_r = cv2.findChessboardCorners(gray_r, (9, 6), None)

            # If found, add object points, image points (after refining them)
            self.objpoints.append(self.objp)

            if ret_l is True:
                rt = cv2.cornerSubPix(gray_l, corners_l, (11, 11),
                                      (-1, -1), self.criteria)
                self.imgpoints_l.append(corners_l)

                # Draw and display the corners
                ret_l = cv2.drawChessboardCorners(img_l, (9, 6),
                                                  corners_l, ret_l)

            if ret_r is True:
                rt = cv2.cornerSubPix(gray_r, corners_r, (11, 11),
                                      (-1, -1), self.criteria)
                self.imgpoints_r.append(corners_r)

                # Draw and display the corners
                ret_r = cv2.drawChessboardCorners(img_r, (9, 6),
                                                  corners_r, ret_r)

            img_shape = gray_l.shape[::-1]

        rt, self.M1, self.d1, self.r1, self.t1 = cv2.calibrateCamera(
            self.objpoints, self.imgpoints_l, img_shape, None, None)
        rt, self.M2, self.d2, self.r2, self.t2 = cv2.calibrateCamera(
            self.objpoints, self.imgpoints_r, img_shape, None, None)

        self.camera_model = self.stereo_calibrate(img_shape)

    def stereo_calibrate(self, dims):
        flags = 0
        flags |= cv2.CALIB_FIX_INTRINSIC
        # flags |= cv2.CALIB_FIX_PRINCIPAL_POINT
        flags |= cv2.CALIB_USE_INTRINSIC_GUESS
        flags |= cv2.CALIB_FIX_FOCAL_LENGTH
        # flags |= cv2.CALIB_FIX_ASPECT_RATIO
        flags |= cv2.CALIB_ZERO_TANGENT_DIST
        # flags |= cv2.CALIB_RATIONAL_MODEL
        # flags |= cv2.CALIB_SAME_FOCAL_LENGTH
        # flags |= cv2.CALIB_FIX_K3
        # flags |= cv2.CALIB_FIX_K4
        # flags |= cv2.CALIB_FIX_K5

        stereocalib_criteria = (cv2.TERM_CRITERIA_MAX_ITER +
                                cv2.TERM_CRITERIA_EPS, 100, 1e-5)
        ret, M1, d1, M2, d2, R, T, E, F = cv2.stereoCalibrate(
            self.objpoints, self.imgpoints_l,
            self.imgpoints_r, self.M1, self.d1, self.M2,
            self.d2, dims,
            criteria=stereocalib_criteria, flags=flags)

        print('Intrinsic_mtx_1', M1)
        np.save('Intrinsic_mtx_1', M1)
        print('dist_1', d1)
        np.save('dist_1', d1)
        print('Intrinsic_mtx_2', M2)
        np.save('Intrinsic_mtx_2', M2)
        print('dist_2', d2)
        np.save('dist_2', d2)
        print('R', R)
        np.save('R', R)
        print('T', T)
        np.save('T', T)
        print('E', E)
        np.save('E', E)
        print('F', F)
        np.save('F', F)

        # for i in range(len(self.r1)):
        #     print("--- pose[", i+1, "] ---")
        #     self.ext1, _ = cv2.Rodrigues(self.r1[i])
        #     self.ext2, _ = cv2.Rodrigues(self.r2[i])
        #     print('Ext1', self.ext1)
        #     print('Ext2', self.ext2)

        print('')

        camera_model = dict([('M1', M1), ('M2', M2), ('dist1', d1),
                            ('dist2', d2), ('rvecs1', self.r1),
                            ('rvecs2', self.r2), ('R', R), ('T', T),
                            ('E', E), ('F', F)])

        cv2.destroyAllWindows()
        return camera_model


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
    image_cam_0 = np.zeros((1024, 1280, 3), np.uint8)
    image_cam_1 = np.zeros((1024, 1280, 3), np.uint8)

    # Setup Calibrator
    logger.info("Initializing Calibrator ...")
    calibrator = StereoCalibration()
    logger.info("Initializing Calibrator - COMPLETE")

    capture_iteration = 0
    imgs_l = []
    imgs_r = []

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
        numpy_horizontal_small = cv2.resize(numpy_horizontal, (0, 0), fx=0.5, fy=0.5)
        cv2.imshow("Live Feed", numpy_horizontal_small)

        k = cv2.waitKey(1)
        if k % 256 == 27:
            # ESC pressed
            logger.info("Escape hit, exiting...")
            break

        elif k % 256 == 32:
            # SPACE pressed
            imgs_l.append(image_cam_0)
            imgs_r.append(image_cam_1)
            cv2.imwrite("calibration\\r_{}.png".format(capture_iteration), image_cam_1)
            cv2.imwrite("calibration\\l_{}.png".format(capture_iteration), image_cam_0)
            logger.info("Calibration Image Added. New Total - {}".format(capture_iteration))
            capture_iteration += 1

    calibrator.read_images(imgs_l, imgs_r)

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

