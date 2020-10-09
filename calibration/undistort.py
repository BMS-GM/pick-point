"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

undistort.py - Testing File
Quickly test the calibrations

Author: Corbin Holz
Author: https://docs.opencv.org/3.0-beta/doc/py_tutorials/py_calib3d/py_calibration/py_calibration.html#calibration
Author: https://gist.github.com/aarmea/629e59ac7b640a60340145809b1c9013
Date Last Modified 3/3/2019
"""

import numpy as np
import cv2
from matplotlib import pyplot as plt
import os

# Instantiate Paths
leftCalibrationPath = os.getcwd() + '/calibration/cam_0_images/leftCal.npz'
rightCalibrationPath = os.getcwd() + '/calibration/cam_1_images/rightCal.npz'
calibrationDetailsPath = os.getcwd() + '/calibration/calDetails.npz'
testCal = os.getcwd() + '/calibration/testCal.npz'

# Load all of the calibrations
leftCal = np.load(leftCalibrationPath)
rightCal = np.load(rightCalibrationPath)
calDetails = np.load(calibrationDetailsPath)

print(tuple(calDetails['size']))

mySize = tuple(calDetails['size'])
thisSize = (mySize[1], mySize[2])

# Calibrate Cameras together
TERMINATION_CRITERIA = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
retval, cameraMatrix1, distCoeffs1, cameraMatrix2, distCoeffs2, R, T, E, F = cv2.stereoCalibrate(calDetails['allObjPoints'], calDetails['imgpoints1'], calDetails['imgpoints2'], calDetails['mtx1'], calDetails['dist1'], calDetails['mtx2'], calDetails['dist2'], thisSize, None, None, None, None, flags=cv2.CALIB_FIX_INTRINSIC, criteria=TERMINATION_CRITERIA)

OPTIMIZE_ALPHA = -1

# Left Camera
#img = cv2.imread(os.getcwd() + '/calibration/testLeft.png')
img = cv2.imread(os.getcwd() + '/calibration/leftBoard.png')
h,  w = img.shape[:2]
Lnewcameramtx, Lroi=cv2.getOptimalNewCameraMatrix(cameraMatrix1, distCoeffs1,(w,h),1,(w,h))

# Right Camera
#img = cv2.imread(os.getcwd() + '/calibration/testRight.png')
img = cv2.imread(os.getcwd() + '/calibration/rightBoard.png')
h,  w = img.shape[:2]
Rnewcameramtx, Rroi=cv2.getOptimalNewCameraMatrix(cameraMatrix2, distCoeffs2,(w,h),1,(w,h))


# Rectify the images (Rotate/Translate images)
leftRectification, rightRectification, leftProjection, rightProjection, dispartityToDepthMap, leftROI, rightROI = cv2.stereoRectify(Lnewcameramtx, distCoeffs1, Rnewcameramtx, distCoeffs2, thisSize, R, T, None, None, None, None, None, cv2.CALIB_ZERO_DISPARITY, OPTIMIZE_ALPHA)

leftMapX, leftMapY = cv2.initUndistortRectifyMap(
        cameraMatrix1, distCoeffs1, leftRectification,
        leftProjection, thisSize, cv2.CV_32FC1)
rightMapX, rightMapY = cv2.initUndistortRectifyMap(
        cameraMatrix2, distCoeffs2, rightRectification,
        rightProjection, thisSize, cv2.CV_32FC1)


# Save rectified calibration
np.savez_compressed(testCal, imageSize=thisSize,
        leftMapX=leftRectification, leftMapY=leftMapY, leftROI=leftROI,
        rightMapX=rightMapX, rightMapY=rightMapY, rightROI=rightROI)


print("Calibrations Loaded")
print(R)
"""
# Left Camera
#img = cv2.imread(os.getcwd() + '/calibration/testLeft.png')
img = cv2.imread(os.getcwd() + '/calibration/leftBoard.png')
h,  w = img.shape[:2]
newcameramtx, roi=cv2.getOptimalNewCameraMatrix(cameraMatrix1, distCoeffs1,(w,h),1,(w,h))

# undistort
dst = cv2.undistort(img, cameraMatrix1, distCoeffs1, None, newcameramtx)
print("Undistort Left")

x,y,w,h = roi
ldst = dst[y:y+h, x:x+w]

# crop the image
#h,  w = img.shape[:2]
newcameramtx, roi=cv2.getOptimalNewCameraMatrix(cameraMatrix2, distCoeffs2,(w,h),1,(w,h))

# undistort
dst = cv2.undistort(img, cameraMatrix2, distCoeffs2, None, newcameramtx)
print("Undistort Right")

# crop the image
rdst = dst[y:y+h, x:x+w]

print("Create Depth Map")

cv2.imwrite(os.getcwd() + '/calibration/leftImg.png', ldst)
cv2.imwrite(os.getcwd() + '/calibration/rightImg.png', rdst)

myLeft = os.getcwd() + '/calibration/leftImg.png'
myRight = os.getcwd() + '/calibration/rightImg.png'
"""
myLeft = os.getcwd() + '/calibration/leftBoard.png'
myRight = os.getcwd() + '/calibration/rightBoard.png'
# Test Depth Map
imgL = cv2.imread(myLeft,0)
imgR = cv2.imread(myRight,0)

stereo = cv2.StereoBM_create(numDisparities=128, blockSize=15)
disparity = stereo.compute(imgL,imgR)
plt.imshow(disparity,'gray')
plt.show()