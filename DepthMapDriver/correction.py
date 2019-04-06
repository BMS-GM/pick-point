import numpy as np
import cv2


def correct(imgL, imgR):
    camera_matrix_r = np.load('Intrinsic_mtx_1.npy')
    dist_coeffs_r = np.load('dist_1.npy')
    camera_matrix_l = np.load('Intrinsic_mtx_2.npy')
    dist_coeffs_l = np.load('dist_2.npy')
    R = np.load('R.npy')
    T = np.load('T.npy')

    RL, RR, PL, PR, Q, _, _ = cv2.stereoRectify(camera_matrix_l, dist_coeffs_l, camera_matrix_r, dist_coeffs_r,
                                               imgL.shape[::-1], R, T, alpha=-1)

    mapL1, mapL2 = cv2.initUndistortRectifyMap(camera_matrix_l, dist_coeffs_l, RL, PL, imgL.shape[::-1], cv2.CV_32FC1)
    mapR1, mapR2 = cv2.initUndistortRectifyMap(camera_matrix_r, dist_coeffs_r, RR, PR, imgR.shape[::-1], cv2.CV_32FC1)

    undistorted_rectifiedL = cv2.remap(imgL, mapL1, mapL2, cv2.INTER_LINEAR);
    undistorted_rectifiedR = cv2.remap(imgR, mapR1, mapR2, cv2.INTER_LINEAR);

    # display image
    cv2.imshow("Left", cv2.resize(undistorted_rectifiedL, (0, 0), fx=0.5, fy=0.5))
    cv2.imshow("Right", cv2.resize(undistorted_rectifiedR, (0, 0), fx=0.5, fy=0.5))
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    left_img = cv2.imread('left.png', 0)
    right_img = cv2.imread('right.png', 0)

    correct(left_img, right_img)
