##
#
#
# Author: https://gist.github.com/aarmea
# Source: https://gist.github.com/aarmea/629e59ac7b640a60340145809b1c9013
#
#
##

import glob
import os
import random
import sys

import numpy as np
import cv2

CHESSBOARD_SIZE = (7, 7)
CHESSBOARD_OPTIONS = (cv2.CALIB_CB_ADAPTIVE_THRESH |
        cv2.CALIB_CB_NORMALIZE_IMAGE | cv2.CALIB_CB_FAST_CHECK)

OBJECT_POINT_ZERO = np.zeros((CHESSBOARD_SIZE[0] * CHESSBOARD_SIZE[1], 3),
        np.float32)
OBJECT_POINT_ZERO[:, :2] = np.mgrid[0:CHESSBOARD_SIZE[0],
        0:CHESSBOARD_SIZE[1]].T.reshape(-1, 2)

OPTIMIZE_ALPHA = 0.25

TERMINATION_CRITERIA = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER, 30,
        0.001)

MAX_IMAGES = 72

if len(sys.argv) != 4:
    print("Syntax: {0} LEFT_IMAGE_DIR RIGHT_IMAGE_DIR OUTPUT_FILENAME"
            .format(sys.argv[0]))
    sys.exit(1)

leftImageDir = sys.argv[1]
rightImageDir = sys.argv[2]
outputFile = sys.argv[3]

def readImagesAndFindChessboards(imageDirectory):
    cacheFile = "{0}/chessboards.npz".format(imageDirectory)
    try:
        cache = np.load(cacheFile)
        print("Loading image data from cache file at {0}".format(cacheFile))
        return (list(cache["filenames"]), list(cache["objectPoints"]),
                list(cache["imagePoints"]), tuple(cache["imageSize"]))
    except IOError:
        print("Cache file at {0} not found".format(cacheFile))

    print("Reading images at {0}".format(imageDirectory))
    imagePaths = glob.glob("{0}/*.png".format(imageDirectory))

    filenames = []
    objectPoints = []
    imagePoints = []
    imageSize = None

    for imagePath in sorted(imagePaths):
        image = cv2.imread(imagePath)
        grayImage = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        newSize = grayImage.shape[::-1]
        if imageSize != None and newSize != imageSize:
            raise ValueError(
                    "Calibration image at {0} is not the same size as the others"
                    .format(imagePath))
        imageSize = newSize

        hasCorners, corners = cv2.findChessboardCorners(grayImage,
                CHESSBOARD_SIZE, cv2.CALIB_CB_FAST_CHECK)

        if hasCorners:
            filenames.append(os.path.basename(imagePath))
            objectPoints.append(OBJECT_POINT_ZERO)
            cv2.cornerSubPix(grayImage, corners, (11, 11), (-1, -1),
                    TERMINATION_CRITERIA)
            imagePoints.append(corners)

        cv2.drawChessboardCorners(image, CHESSBOARD_SIZE, corners, hasCorners)
        cv2.imshow(imageDirectory, image)

        # Needed to draw the window
        cv2.waitKey(1)

    cv2.destroyWindow(imageDirectory)

    print("Found corners in {0} out of {1} images"
            .format(len(imagePoints), len(imagePaths)))

    np.savez_compressed(cacheFile,
            filenames=filenames, objectPoints=objectPoints,
            imagePoints=imagePoints, imageSize=imageSize)
    return filenames, objectPoints, imagePoints, imageSize

(leftFilenames, leftObjectPoints, leftImagePoints, leftSize
        ) = readImagesAndFindChessboards(leftImageDir)
(rightFilenames, rightObjectPoints, rightImagePoints, rightSize
        ) = readImagesAndFindChessboards(rightImageDir)

if leftSize != rightSize:
    print("Camera resolutions do not match")
    sys.exit(1)
imageSize = leftSize

print("Left Filenames: {}, Right Filenames: {}".format(len(leftFilenames), len(rightFilenames)))

filenames = []

filenames += leftFilenames
filenames += rightFilenames

print("What Filenames is: {}".format(len(filenames)))
if (len(filenames) > MAX_IMAGES):
    print("Too many images to calibrate, using {0} randomly selected images"
            .format(MAX_IMAGES))
    filenames = random.sample(filenames, MAX_IMAGES)
filenames = sorted(filenames)
print("Using these images:")
print(filenames)

def getMatchingObjectAndImagePoints(requestedFilenames,
        allFilenames, objectPoints, imagePoints):
    print("Requested: {}    all: {}".format(len(requestedFilenames), len(allFilenames)))
    requestedFilenameSet = set(requestedFilenames)
    requestedObjectPoints = []
    requestedImagePoints = []

    for index, filename in enumerate(allFilenames):
        if filename in requestedFilenameSet:
            requestedObjectPoints.append(objectPoints[index])
            requestedImagePoints.append(imagePoints[index])

    print("Added Everything, object points: {} Image Points: {}".format(len(requestedObjectPoints), len(imagePoints)))

    return requestedObjectPoints, requestedImagePoints

leftObjectPoints, leftImagePoints = getMatchingObjectAndImagePoints(filenames,
        leftFilenames, leftObjectPoints, leftImagePoints)
rightObjectPoints, rightImagePoints = getMatchingObjectAndImagePoints(filenames,
        rightFilenames, rightObjectPoints, rightImagePoints)

# TODO: Fix this validation
# Keep getting "Use a.any() or a.all()" even though it's already used?!
# if (leftObjectPoints != rightObjectPoints).all():
#     print("Object points do not match")
#     sys.exit(1)
objectPoints = leftObjectPoints

print("Object Points Final: {}".format(len(objectPoints)))

print("Calibrating left camera...")
_, leftCameraMatrix, leftDistortionCoefficients, _, _ = cv2.calibrateCamera(
        objectPoints, leftImagePoints, imageSize, None, None)
print("Calibrating right camera...")
_, rightCameraMatrix, rightDistortionCoefficients, _, _ = cv2.calibrateCamera(
        objectPoints, rightImagePoints, imageSize, None, None)

print("Calibrating cameras together...")
(_, _, _, _, _, rotationMatrix, translationVector, _, _) = cv2.stereoCalibrate(
        objectPoints, leftImagePoints, rightImagePoints,
        leftCameraMatrix, leftDistortionCoefficients,
        rightCameraMatrix, rightDistortionCoefficients,
        imageSize, None, None, None, None,
        cv2.CALIB_FIX_INTRINSIC, TERMINATION_CRITERIA)

print("Rectifying cameras...")
# TODO: Why do I care about the disparityToDepthMap?
(leftRectification, rightRectification, leftProjection, rightProjection,
        dispartityToDepthMap, leftROI, rightROI) = cv2.stereoRectify(
                leftCameraMatrix, leftDistortionCoefficients,
                rightCameraMatrix, rightDistortionCoefficients,
                imageSize, rotationMatrix, translationVector,
                None, None, None, None, None,
                cv2.CALIB_ZERO_DISPARITY, OPTIMIZE_ALPHA)

print("Saving calibration...")
leftMapX, leftMapY = cv2.initUndistortRectifyMap(
        leftCameraMatrix, leftDistortionCoefficients, leftRectification,
        leftProjection, imageSize, cv2.CV_32FC1)
rightMapX, rightMapY = cv2.initUndistortRectifyMap(
        rightCameraMatrix, rightDistortionCoefficients, rightRectification,
        rightProjection, imageSize, cv2.CV_32FC1)

np.savez_compressed(outputFile, imageSize=imageSize,
        leftMapX=leftMapX, leftMapY=leftMapY, leftROI=leftROI,
        rightMapX=rightMapX, rightMapY=rightMapY, rightROI=rightROI)

cv2.destroyAllWindows()