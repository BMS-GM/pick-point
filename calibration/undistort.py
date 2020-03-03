import numpy as np
import cv2
import os

leftCalibrationPath = os.getcwd() + '/calibration/cam_0_images/leftCal.npz'
rightCalibrationPath = os.getcwd() + '/calibration/cam_1_images/rightCal.npz'
calibrationDetailsPath = os.getcwd() + '/calibration/calDetails.npz'
testCal = os.getcwd() + '/calibration/testCal.npz'

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
img = cv2.imread('/home/crholz/Documents/GitHub/pick-point/calibration/testLeft.png')
h,  w = img.shape[:2]
Lnewcameramtx, Lroi=cv2.getOptimalNewCameraMatrix(cameraMatrix1, distCoeffs1,(w,h),1,(w,h))

img = cv2.imread('/home/crholz/Documents/GitHub/pick-point/calibration/testRight.png')
h,  w = img.shape[:2]
Rnewcameramtx, Rroi=cv2.getOptimalNewCameraMatrix(cameraMatrix2, distCoeffs2,(w,h),1,(w,h))

leftRectification, rightRectification, leftProjection, rightProjection, dispartityToDepthMap, leftROI, rightROI = cv2.stereoRectify(Lnewcameramtx, distCoeffs1, Rnewcameramtx, distCoeffs2, thisSize, R, T, None, None, None, None, None, cv2.CALIB_ZERO_DISPARITY, OPTIMIZE_ALPHA)

leftMapX, leftMapY = cv2.initUndistortRectifyMap(
        cameraMatrix1, distCoeffs1, leftRectification,
        leftProjection, thisSize, cv2.CV_32FC1)
rightMapX, rightMapY = cv2.initUndistortRectifyMap(
        cameraMatrix2, distCoeffs2, rightRectification,
        rightProjection, thisSize, cv2.CV_32FC1)

np.savez_compressed(testCal, imageSize=thisSize,
        leftMapX=leftRectification, leftMapY=leftMapY, leftROI=leftROI,
        rightMapX=rightMapX, rightMapY=rightMapY, rightROI=rightROI)

print(leftRectification)
print(rightRectification)

"""
print("Calibrations Loaded")
print(R)
# Left Camera
img = cv2.imread('/home/crholz/Documents/GitHub/pick-point/calibration/testLeft.png')
h,  w = img.shape[:2]
newcameramtx, roi=cv2.getOptimalNewCameraMatrix(cameraMatrix1, distCoeffs1,(w,h),1,(w,h))

# undistort
dst = cv2.undistort(img, cameraMatrix1, distCoeffs1, None, newcameramtx)
print("Undistort Left")


# crop the image
x,y,w,h = roicalibrationDetailsPathint/calibration/testRight.png')
h,  w = img.shape[:2]
newcameramtx, roi=cv2.getOptimalNewCameraMatrix(cameraMatrix2, distCoeffs2,(w,h),1,(w,h))

# undistort
dst = cv2.undistort(img, cameraMatrix2, distCoeffs2, None, newcameramtx)
print("Undistort Right")

# crop the image
x,y,w,h = roi
rdst = dst[y:y+h, x:x+w]

print("Create Depth Map")

cv2.imwrite(os.getcwd() + '/calibration/leftImg.png', ldst)
cv2.imwrite(os.getcwd() + '/calibration/rightImg.png', rdst)

myLeft = os.getcwd() + '/calibration/leftImg.png'
myRight = os.getcwd() + '/calibration/rightImg.png'

# Test Depth Map
imgL = cv2.imread(myLeft,0)
imgR = cv2.imread(myRight,0)

stereo = cv2.StereoBM_create(numDisparities=16, blockSize=5)
disparity = stereo.compute(imgL,imgR)
cv2.imshow(disparity,'gray')
"""