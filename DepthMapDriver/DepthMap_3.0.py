import numpy as np
# from sklearn.preprocessing import normalize
import cv2
import PySpin
import sys
from CameraDriver.SpinCameraDriver import SpinCameraDriver

class DepthMap3:
    print('loading images...')

    # imgL = cv2.imread('C:/Users\jmjerred-adm\PycharmProjects\pick-point\images\capture\cam_1_frame_3.png', 0)
    # downscale images for faster processing
    # imgR = cv2.imread('C:/Users\jmjerred-adm\PycharmProjects\pick-point\images\capture\cam_0_frame_3.png', 0)

    # Get a list of all cameras on the system
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()
    if cam_list.GetSize() < 2:
        system.ReleaseInstance()
        del system
        sys.exit()
    cam_0 = cam_list.GetByIndex(0)
    cam_1 = cam_list.GetByIndex(1)
    drivers = [SpinCameraDriver(cam_0), SpinCameraDriver(cam_1)]
    img_counter = 1
    image_cam_0 = drivers[0].get_image(1)[0]
    image_cam_1 = drivers[1].get_image(1)[0]
    img_name = "C:/Users\jmjerred-adm\PycharmProjects\pick-point\images\capture\cam_0_frame_{}.png".format(img_counter)
    cv2.imwrite(img_name, image_cam_0)
    img_name = "C:/Users\jmjerred-adm\PycharmProjects\pick-point\images\capture\cam_1_frame_{}.png".format(img_counter)
    cv2.imwrite(img_name, image_cam_1)
    imgL = cv2.imread('C:/Users\jmjerred-adm\PycharmProjects\pick-point\images\capture\cam_1_frame_1.png', 0)
    # downscale images for faster processing
    imgR = cv2.imread('C:/Users\jmjerred-adm\PycharmProjects\pick-point\images\capture\cam_0_frame_1.png', 0)

    # SGBM Parameters -----------------
    window_size = 3  # wsize default 3; 5; 7 for SGBM reduced size image; 15 for SGBM full size image (1300px and above); 5 Works nicely

    left_matcher = cv2.StereoSGBM_create(
        minDisparity=0,
        numDisparities=160,  # max_disp has to be dividable by 16 f. E. HH 192, 256
        blockSize=5,
        P1=8 * 3 * window_size ** 2,
        # wsize default 3; 5; 7 for SGBM reduced size image; 15 for SGBM full size image (1300px and above); 5 Works nicely
        P2=32 * 3 * window_size ** 2,
        disp12MaxDiff=1,
        uniquenessRatio=15,
        speckleWindowSize=0,
        speckleRange=2,
        preFilterCap=63,
        mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
    )

    right_matcher = cv2.ximgproc.createRightMatcher(left_matcher)

    # FILTER Parameters
    lmbda = 80000
    sigma = 1.2
    visual_multiplier = 1.0

    wls_filter = cv2.ximgproc.createDisparityWLSFilter(matcher_left=left_matcher)
    wls_filter.setLambda(lmbda)
    wls_filter.setSigmaColor(sigma)

    print('computing disparity...')
    displ = left_matcher.compute(imgL, imgR)  # .astype(np.float32)/16
    dispr = right_matcher.compute(imgR, imgL)  # .astype(np.float32)/16
    displ = np.int16(displ)
    dispr = np.int16(dispr)
    filteredImg = wls_filter.filter(displ, imgL, None, dispr)  # important to put "imgL" here!!!

    filteredImg = cv2.normalize(src=filteredImg, dst=filteredImg, beta=0, alpha=255, norm_type=cv2.NORM_MINMAX);
    filteredImg = np.uint8(filteredImg)
    filteredImg = cv2.resize(filteredImg, None, fx=0.5, fy=0.5)
    cv2.imshow('Disparity Map', filteredImg)
    cv2.waitKey()
    cv2.destroyAllWindows()

    del drivers[1]
    del drivers[0]
    del drivers
    del cam_0
    del cam_1
    del cam_list

