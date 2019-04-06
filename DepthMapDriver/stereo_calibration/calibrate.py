from stereovision.calibration import StereoCalibrator
import cv2
import numpy as np

if __name__ == '__main__':

    calibrator = StereoCalibrator(6, 9, 2.15, (1280, 1024))
    for i in range(7):
        img_l = cv2.imread('calibration_imgs/%d_L.png' % i)
        img_r = cv2.imread('calibration_imgs/%d_R.png' % i)
        calibrator.add_corners((img_l, img_r))

    calibration = calibrator.calibrate_cameras()
    calibration.export('./output')
