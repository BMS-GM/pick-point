import cv2
import numpy as np
import PySpin
import sys

from CameraDriver.SpinCameraDriver import SpinCameraDriver

if __name__ == "__main__":
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()

    # Get a list of all cameras on the system
    if cam_list.GetSize() == 0:
        system.ReleaseInstance()
        del system
        sys.exit()

    cam_0 = cam_list.GetByIndex(0)
    cam_1 = cam_list.GetByIndex(1)
    drivers = [SpinCameraDriver(cam_0), SpinCameraDriver(cam_1)]
    img_counter = 0

    while True:

        # Get Cam_0
        image_cam_0 = drivers[0].get_image(1)[0]
        image_cam_1 = drivers[1].get_image(1)[0]
        numpy_horizontal = np.hstack((image_cam_0, image_cam_1))
        numpy_horizontal_small = cv2.resize(numpy_horizontal, (0,0), fx=0.5, fy=0.5)
        cv2.imshow("Live Feed", numpy_horizontal_small)

        k = cv2.waitKey(1)
        if k % 256 == 27:
            # ESC pressed
            print("Escape hit, closing...")
            break

        elif k % 256 == 32:
            # SPACE pressed
            img_name = "cam_0_frame_{}.png".format(img_counter)
            cv2.imwrite(img_name, image_cam_0)
            img_name = "cam_1_frame_{}.png".format(img_counter)
            cv2.imwrite(img_name, image_cam_1)
            print("{} written!".format(img_name))
            img_counter += 1

    # delete all references to the cameras
    del drivers[1]
    del drivers[0]
    del drivers
    del cam_0
    del cam_1
    del cam_list

    # clean up the system
    system.ReleaseInstance()
    del system



