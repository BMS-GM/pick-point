"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

undistort.py - Testing File
Quickly test the calibrations

Author: Corbin Holz, Max Hoglund, Will Collicott
Author: https://docs.opencv.org/3.0-beta/doc/py_tutorials/py_calib3d/py_calibration/py_calibration.html#calibration
Author: https://gist.github.com/aarmea/629e59ac7b640a60340145809b1c9013
Date Last Modified 3/3/2019
"""

import numpy as np
import cv2
from matplotlib import pyplot as plt
import os

LEFT_PATH = os.getcwd() + '/calibration/tripleL.png'
RIGHT_PATH = os.getcwd() + '/calibration/tripleR.png'

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
img = cv2.imread(LEFT_PATH)
h,  w = img.shape[:2]
Lnewcameramtx, Lroi=cv2.getOptimalNewCameraMatrix(cameraMatrix1, distCoeffs1,(w,h),1,(w,h))

# Right Camera
#img = cv2.imread(os.getcwd() + '/calibration/testRight.png')
img = cv2.imread(RIGHT_PATH)
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

# Left Camera
img1 = cv2.imread(LEFT_PATH)
img2 = cv2.imread(RIGHT_PATH)
h,  w = img1.shape[:2]
newcameramtx, roi=cv2.getOptimalNewCameraMatrix(cameraMatrix2, distCoeffs2,(w,h),1,(w,h))

# undistort
dst = cv2.undistort(img1, cameraMatrix2, distCoeffs2, None, newcameramtx)
plt.imshow(dst)
print("Undistort Left")

print("roi: " + str(roi))
x,y,w,h = roi
ldst = dst[y:y+h, x:x+w]
ldst = ldst[250:675, 125:950]

# crop the image
h,  w = img2.shape[:2]
newcameramtx, roi=cv2.getOptimalNewCameraMatrix(cameraMatrix2, distCoeffs2,(w,h),1,(w,h))

# undistort
dst = cv2.undistort(img2, cameraMatrix2, distCoeffs2, None, newcameramtx)
print("Undistort Right")

# crop the image
print("roi: " + str(roi))
x,y,w,h = roi
rdst = dst[y:y+h, x:x+w]
rdst = rdst[250:675, 125:950]

print("Create Depth Map")

cv2.imwrite(os.getcwd() + '/calibration/outputL.png', ldst)
cv2.imwrite(os.getcwd() + '/calibration/outputR.png', rdst)

myLeft = os.getcwd() + '/calibration/outputL.png'
myRight = os.getcwd() + '/calibration/outputR.png'

# Test Depth Map
imgL = cv2.imread(myLeft,0)
imgR = cv2.imread(myRight,0)

stereo = cv2.StereoBM_create(numDisparities=48, blockSize=29)
disparity = stereo.compute(imgL,imgR)
#disparity = np.uint8(disparity)
cv2.imwrite(os.getcwd() + '/calibration/depthmap.png', disparity)
#de_noised = cv2.fastNlMeansDenoising(src = disparity, dst = None, h = 8, templateWindowSize = 7, searchWindowSize = 21)
plt.imshow(imgL)
plt.imshow(imgR)
plt.imshow(disparity,'gray')
#plt.show()