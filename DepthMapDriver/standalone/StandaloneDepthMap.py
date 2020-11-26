"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

StandaloneDepthMap.py - standalone file containing functions to perform depthmap-related tasks

Author: Will Collicott
Date Last Modified 11/25/2020
"""

import cv2
from matplotlib import pyplot as plt
import os


def get_depth(imgL, imgR, x, y):
    stereo = cv2.StereoBM_create(numDisparities=48, blockSize=29)
    disparity = stereo.compute(imgL, imgR)
    z = disparity[y][x]
    cv2.imwrite(os.getcwd() + '/depthmap.png', disparity)
    plt.imshow(imgL)
    plt.imshow(imgR)
    plt.imshow(disparity, 'gray')
    return z

