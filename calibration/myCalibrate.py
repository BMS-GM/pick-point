"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

myCalibrate.py - My take on calibration calculation

Author: Corbin Holz
Author: https://docs.opencv.org/3.0-beta/doc/py_tutorials/py_calib3d/py_calibration/py_calibration.html#calibration
Date Last Modified 3/3/2019
"""

import numpy as np
import cv2
import glob
import os

CHESSBOARD_CORNERS = (7, 7)

# termination criteria
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# prepare object points
objp = np.zeros(((CHESSBOARD_CORNERS[0] * CHESSBOARD_CORNERS[1]), 3), np.float32)
objp[::,:2] = np.mgrid[0:CHESSBOARD_CORNERS[0], 0:CHESSBOARD_CORNERS[1]].T.reshape(-1, 2)

# Arrays to store object points and image points from all the images.
allObjPoints = []
imgpoints1 = []
imgpoints2 = []
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.

path = os.getcwd() + '/calibration/cam_0_images/*.png'
fakePath = os.getcwd() + '/calibration/cam_1_images/cam_1_frame_17.png'
imgSize = cv2.imread(fakePath)
size = imgSize.shape[::-1]
print(size)

# Create a glob of all the images
images = glob.glob(path)

# Calculate Left Camera Calibration
for fname in images:

    img = cv2.imread(fname)
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

    # Find the chess board corners
    ret, corners = cv2.findChessboardCorners(gray, ( CHESSBOARD_CORNERS[0],CHESSBOARD_CORNERS[1]),None)


    # If found, add object points, image points (after refining them)
    if ret == True:
        objpoints.append(objp)
        allObjPoints.append(objp)

        corners2 = cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
        imgpoints.append(corners)
        imgpoints1.append(corners)

        # Draw and display the corners
        cv2.drawChessboardCorners(img, CHESSBOARD_CORNERS, corners2,ret)
        cv2.imshow('Left Camera Image'.format(fname),img)
        cv2.waitKey(500)

cv2.destroyAllWindows()


# Save the returns of the calibration
ret1, mtx1, dist1, rvecs1, tvecs1 = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1],None,None)

# Save the calibration to a file
leftCalibrationPath = os.getcwd() + '/calibration/cam_0_images/leftCal.npz'
np.savez(leftCalibrationPath, ret=ret1, mtx=mtx1, dist=dist1, rvecs=rvecs1, tvecs=tvecs1)

print("Left Calibration Created")

# Calibrate Right Camera

# prepare object points
objp = np.zeros(((CHESSBOARD_CORNERS[0] * CHESSBOARD_CORNERS[1]), 3), np.float32)
objp[::,:2] = np.mgrid[0:CHESSBOARD_CORNERS[0], 0:CHESSBOARD_CORNERS[1]].T.reshape(-1, 2)

# Arrays to store object points and image points from all the images.
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.



path = os.getcwd() + '/calibration/cam_1_images/*.png'


images = glob.glob(path)

# Calculate Right Camera Calibration
for fname in images:
    img = cv2.imread(fname)

    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

    # Find the chess board corners
    ret, corners = cv2.findChessboardCorners(gray, ( CHESSBOARD_CORNERS[0],CHESSBOARD_CORNERS[1]),None)


    # If found, add object points, image points (after refining them)
    if ret == True:
        objpoints.append(objp)
        allObjPoints.append(objp)

        corners2 = cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
        imgpoints.append(corners)
        imgpoints2.append(corners)

        # Draw and display the corners
        cv2.drawChessboardCorners(img, CHESSBOARD_CORNERS, corners2,ret)
        cv2.imshow('Right Camera Image'.format(fname),img)
        cv2.waitKey(500)

cv2.destroyAllWindows()


# Save the returns of the calibration
ret2, mtx2, dist2, rvecs2, tvecs2 = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1],None,None)

# Save the calibration to a file
rightCalibrationPath = os.getcwd() + '/calibration/cam_1_images/rightCal.npz'
np.savez(rightCalibrationPath, ret=ret2, mtx=mtx2, dist=dist2, rvecs=rvecs2, tvecs=tvecs2)

# Save a cumulative package of all of the calibrations
calibrationDetailsPath = os.getcwd() + '/calibration/calDetails.npz'
np.savez(calibrationDetailsPath, allObjPoints=objpoints, imgpoints1=imgpoints1, imgpoints2=imgpoints2, size=size, mtx1=mtx1, mtx2=mtx2, dist1=dist1, dist2=dist2, ret1=ret1, ret2=ret2, tvecs1=tvecs1, tvecs2=tvecs2, rvecs1=rvecs1, rvecs2=rvecs2)
print("Right Calibration Created")

# Create a stereo calibration and save it
ret, camMtx1, dist1, camMtx2, distcoeff2, R, T, E, F = cv2.stereoCalibrate(allObjPoints, imgpoints1, imgpoints2, size, mtx1, dist1, mtx2, dist2, None, None, None, None, cv2.CALIB_FIX_INTRINSIC, tuple(criteria))
fullCalibrationPath = os.getcwd() + '/calibration/fullCalibration.npz'
np.savez(fullCalibrationPath, ret=ret, camMtx1=camMtx1, camMtx2=camMtx2, dist1=dist1, dist2=dist2, R=R, T=T, E=E, F=F)

leftCal = np.load(leftCalibrationPath)
rightCal = np.load(rightCalibrationPath)

print("Calibrations Loaded")

# Left Camera Image Load and apply the Calibration
img = cv2.imread('/home/crholz/Documents/GitHub/pick-point/calibration/cam_0_images/cam_0_frame_17.png')
h,  w = img.shape[:2]
leftcameramtx, Lroi=cv2.getOptimalNewCameraMatrix(leftCal['mtx'], leftCal['dist'],(w,h),1,(w,h))

# Right Camera Image Load and apply the Calibration
img = cv2.imread('/home/crholz/Documents/GitHub/pick-point/calibration/cam_1_images/cam_1_frame_17.png')
h,  w = img.shape[:2]
rightcameramtx, Rroi=cv2.getOptimalNewCameraMatrix(rightCal['mtx'], rightCal['dist'],(w,h),1,(w,h))

