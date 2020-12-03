"""
--------------------------------------------------------------------
Michigan Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

StandaloneDepthMap.py - standalone file containing functions to perform depthmap-related tasks

Author: Will Collicott
Date Last Modified 12/3/2020
"""

import cv2


def initialize_depth_map(imgL, imgR, numDisparities, blockSize):
    stereo = cv2.StereoBM_create(numDisparities=numDisparities, blockSize=blockSize)
    return stereo.compute(imgL, imgR)


