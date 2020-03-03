import numpy as np
import cv2
import os

REMAP_INTERPOLATION = cv2.INTER_LINEAR
DEPTH_VISUALIZATION_SCALE = 8192 * 2



calibration = np.load(os.getcwd() + '/calibration/testCal.npz')
imageSize = tuple(calibration["imageSize"])
leftMapX = calibration["leftMapX"]
leftMapY = calibration["leftMapY"]
leftROI = tuple(calibration["leftROI"])
rightMapX = calibration["rightMapX"]
rightMapY = calibration["rightMapY"]
rightROI = tuple(calibration["rightROI"])

stereoMatcher = cv2.StereoBM_create()
stereoMatcher.setMinDisparity(4)
stereoMatcher.setNumDisparities(16)
stereoMatcher.setBlockSize(5)
stereoMatcher.setROI1(leftROI)
stereoMatcher.setROI2(rightROI)
stereoMatcher.setSpeckleRange(16)
stereoMatcher.setSpeckleWindowSize(45)

leftName = '/home/crholz/Documents/GitHub/pick-point/calibration/testLeft.png'
rightName = '/home/crholz/Documents/GitHub/pick-point/calibration/testRight.png'

imgL = cv2.imread(leftName)
imgR = cv2.imread(rightName)

cv2.imshow('L Raw', imgL)

imgL = np.array(imgL, dtype=np.uint8)
imgR = np.array(imgR, dtype=np.uint8)

cv2.imshow('L Raw', imgL)

leftHeight, leftWidth = imgL.shape[:2]
rightHeight, rightWidge = imgR.shape[:2]

print(leftMapX)
print(leftMapY)

calImgL = cv2.remap(imgL, leftMapX, leftMapY, REMAP_INTERPOLATION)
calImgR = cv2.remap(imgR, rightMapX, rightMapY, REMAP_INTERPOLATION)

cv2.imshow('L Cal', calImgL)

calImgL = np.array(calImgL, dtype=np.uint8)
calImgR = np.array(calImgR, dtype=np.uint8)

gLeft = cv2.cvtColor(calImgL, cv2.COLOR_BGR2GRAY)
gRight = cv2.cvtColor(calImgR, cv2.COLOR_BGR2GRAY)

depthMap = stereoMatcher.compute(gLeft, gRight)