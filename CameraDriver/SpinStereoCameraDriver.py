import sys
import logging
import threading
import PySpin

from CameraDriver.StereoCameraThread import StereoCameraThread
from CameraDriver.SpinCameraDriver import SpinCameraDriver


class SpinStereoCameraDriver(StereoCameraThread):

    def __init__(self, left_camera_id, right_camera_id):
        super(SpinStereoCameraDriver, self).__init__()
        self._logger = logging.getLogger('GM_Pick_Point.' + self.__class__.__name__)

        self._lock = threading.Lock()
        self._request_images_event = threading.Event()
        self._images_acquired_event = threading.Event()
        self._terminate_thread = threading.Event()
        self._request = None
        self._acquired_images = None
        self._system = None
        self._left_driver = None
        self._right_driver = None

        self._init_cameras(left_camera_id, right_camera_id)

    def __del__(self):
        del self._left_driver
        del self._right_driver
        self._system.ReleaseInstance()
        del self._system

    def _init_cameras(self, left_camera_id, right_camera_id):
        self._logger.info("Initializing Drivers...")
        self._system = PySpin.System.GetInstance()
        cam_list = self._system.GetCameras()

        drivers = []
        for camera in cam_list:
            drivers.append(SpinCameraDriver(camera))
        self._logger.info("Initializing Drivers - COMPLETE")

        # Find Left Camera
        self._logger.info("Finding Left Camera...")
        for driver in drivers:
            info = driver.get_info()
            if info[1] == left_camera_id:
                self._left_driver = driver
                self._logger.info("Left Camera - FOUND\n"
                                  "\t Serial Number: %s\n"
                                  "\t Vendor Name  : %s\n"
                                  "\t Display Name : %s"
                                  % (info[1], info[2], info[3]))

        if self._left_driver is None:
            self._logger.error("Unable to find Left Camera - EXITING")
            self._logger.info("Cleaning Up System ...")
            for driver in drivers:
                del driver
            del drivers
            del self._left_driver
            del self._right_driver

            for camera in cam_list:
                del camera
            del cam_list

            self._system.ReleaseInstance()
            del self._system
            self._logger.info("Cleaning Up System - COMPLETE")
            sys.exit()

        # Find Right Camera
        self._logger.info("Finding Right Camera...")
        for driver in drivers:
            info = driver.get_info()
            if info[1] == right_camera_id:
                self._right_driver = driver
                self._logger.info("Right Camera - FOUND\n"
                                  "\t Serial Number: %s\n"
                                  "\t Vendor Name  : %s\n"
                                  "\t Display Name : %s"
                                  % (info[1], info[2], info[3]))

        if self._right_driver is None:
            self._logger.error("Unable to find Right Camera - EXITING")
            self._logger.info("Cleaning Up System ...")
            for driver in drivers:
                del driver
            del drivers
            del self._left_driver
            del self._right_driver

            for camera in cam_list:
                del camera
            del cam_list

            self._system.ReleaseInstance()
            del self._system
            self._logger.info("Cleaning Up System - COMPLETE")
            sys.exit()

        # Release Unused Cameras:
        self._logger.info("Releasing Unused Cameras...")
        for driver in drivers:
            del driver
        del drivers

        for camera in cam_list:
            del camera
        del cam_list
        self._logger.info("Releasing Unused Cameras - COMPLETE")

    def run(self):
        pass

    def _main_loop(self):
        while not self._terminate_thread.is_set():
            images_pending = self._request_images_event.wait(0.5)
            if images_pending:
                self._request[0](*self._request[1])

    def get_stereo_images(self, num_images, result):
        with self._lock:
            self._request = (self._get_stereo_images, num_images)
            self._images_acquired_event.clear()
            self._request_images_event.set()
            self._images_acquired_event.wait()
            result = self._acquired_images.copy()

    def get_mono_images(self, num_images, result, camera_to_use='RANDOM'):
        with self._lock:
            self._request = (self._get_mono_images, (num_images, camera_to_use))
            self._request_images_event.set()
            self._images_acquired_event.wait()
            result = self._acquired_images.copy()

    def _get_stereo_images(self, num_images):
        self._logger.info("Acquiring %d stereo image pairs..." % num_images)
        result = []
        images_left = num_images
        while images_left > 0:
            # get left image
            try:
                left_image = self._left_driver.get_image(1)[0]
            except IndexError:
                continue

            # get right image
            try:
                right_image = self._right_driver.get_image(1)[0]
            except IndexError:
                continue

            result.append((left_image, right_image))
            images_left -= 1

        self._logger.info("Acquiring %d stereo image pairs - COMPLETE" % num_images)
        return result

    def _get_mono_images(self, num_images, camera_to_use):
        self._logger.info("Acquiring %d stereo image pairs..." % num_images)
        result = []
        images_left = num_images
        while images_left > 0:
            # get left image
            try:
                left_image = self._left_driver.get_image(1)[0]
            except IndexError:
                continue

            # get right image
            try:
                right_image = self._right_driver.get_image(1)[0]
            except IndexError:
                continue

            result.append((left_image, right_image))
            images_left -= 1

        self._logger.info("Acquiring %d stereo image pairs - COMPLETE" % num_images)
        return result


