import cv2
import numpy as np

if __name__ == "__main__":
    # disparity settings
    window_size = 5
    min_disp = 32
    num_disp = 112 - min_disp
    stereo = cv2.StereoSGBM_create(
        minDisparity=min_disp,
        numDisparities=num_disp,
        blockSize=window_size,
        uniquenessRatio=10,
        speckleWindowSize=100,
        speckleRange=32,
        disp12MaxDiff=1,
        P1=8 * 3 * window_size ** 2,
        P2=32 * 3 * window_size ** 2,
    )

    # morphology settings
    kernel = np.ones((12, 12), np.uint8)

    image_left = cv2.imread('C:/Users\jmjerred-adm\PycharmProjects\pick-point\images\capture\cam_1_frame_3.png')
    image_right = cv2.imread('C:/Users\jmjerred-adm\PycharmProjects\pick-point\images\capture\cam_0_frame_3.png')

    # compute disparity
    disparity = stereo.compute(image_left, image_right).astype(np.float32) / 16.0
    disparity = (disparity - min_disp) / num_disp
    cv2.imshow("TEST", np.array(disparity, dtype=np.uint16 ))
    cv2.waitKey()

    print('Done')
    cv2.destroyAllWindows()