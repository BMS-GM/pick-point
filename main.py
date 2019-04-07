import threading
import numpy as np
import cv2
import logging
import datetime
import queue

from CameraDriver.SpinStereoCameraDriver import SpinStereoCameraDriver
from NeuralNetwork import MachineLearningThread

LOG_DIR = '/logs'
LEFT_CAMERA_SERIAL_NUM = '18585124'
RIGHT_CAMERA_SERIAL_NUM = '18585121'
GRAPH_TYPE = 'SSD_INCEPTION_V2'


class Main:

    def __init__(self):
        # =================================
        # Setup Logging
        # =================================
        # Create master logger and set global log level
        logger = logging.getLogger("GM_Pick_Point")
        logger.setLevel(logging.DEBUG)

        # create log file
        file_handler = logging.FileHandler(LOG_DIR + '/GM_Pick_Point - %s.log' %
                                           datetime.datetime.now().strftime("%Y.%m.%d-%H.%M.%S"))
        file_handler.setLevel(logging.DEBUG)

        # create console logger
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Format Log
        log_formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(name)s - %(message)s')
        file_handler.setFormatter(log_formatter)
        console_handler.setFormatter(log_formatter)

        # Add outputs to main logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        # =====================================================================

        # Setup Multi-threading
        self._camera_thread = SpinStereoCameraDriver(LEFT_CAMERA_SERIAL_NUM, RIGHT_CAMERA_SERIAL_NUM)
        self._machine_learning_thread = MachineLearningThread.MachineLearningThread(LOG_DIR, graph_type=GRAPH_TYPE)
        self._sql_thread = None         # TODO
        self._depth_map_thread = None

        self._camera_thread_complete = threading.Event()
        self._machine_learning_thread_complete = threading.Event()
        self._sql_thread_complete = threading.Event()
        self._depth_map_thread_complete = threading.Event()

        self._camera_result = None
        self._machine_learning_result = None
        self._sql_result = None
        self._depth_map_result = None

        self._camera_result_lock = threading.Lock()
        self._machine_learning_result_lock = threading.Lock()
        self._sql_result_lock = threading.Lock()
        self._depth_map_result_lock = threading.Lock()

    def main_loop(self):
        self._machine_learning_thread.start()
        self._camera_thread.start()
        # self._sql_thread.start() TODO

        while True:
            self._process_next_images()

    def get_camera_images(self):
        self._camera_thread_complete.wait()
        with self._camera_result_lock:
            result = self._camera_result.copy()
        return result

    def _call_camera_thread(self):
        # Get then next set of images
        self._camera_thread_complete.clear()
        with self._camera_result_lock:
            self._camera_result = self._camera_thread.get_stereo_images(1)
            self._camera_thread_complete.set()

    def get_machine_learning_result(self):
        self._machine_learning_thread_complete.wait()
        with self._machine_learning_result_lock:
            result = self._machine_learning_result.copy()
        return result

    def _call_machine_learning_thread(self, image):
        self._machine_learning_thread_complete.clear()
        with self._machine_learning_result_lock:
            self._machine_learning_result = self._machine_learning_thread.process_image(image)
            self._machine_learning_thread_complete.set()

    def get_depth_map(self):
        self._depth_map_thread_complete.wait()
        with self._depth_map_result_lock:
            result = self._depth_map_result.copy()
        return result

    def _call_depth_map_thread(self, images):
        # TODO: Need to fix
        self._depth_map_thread_complete.clear()
        with self._depth_map_result_lock:
            self._depth_map_result = None
            self._depth_map_thread_complete.set()

    def get_sql_result(self):
        self._sql_thread_complete.wait()
        with self._sql_result_lock:
            result = self._sql_result.copy()
        return result

    def _call_sql_thread(self):
        # TODO: Need to fix
        self._sql_thread_complete.clear()
        with self._sql_result_lock:
            self._sql_result = None
            self._sql_thread_complete.set()

    def _process_next_images(self):
        self._call_camera_thread()
        images = self.get_camera_images()

        ml_task_thread = threading.Thread(target=self._call_machine_learning_thread, args=[images[0].copy()])
        depth_map_task_thread = threading.Thread(target=self._call_depth_map_thread, args=[images.copy()])

        ml_task_thread.start()
        depth_map_task_thread.start()

        ml_task_thread.join()
        depth_map_task_thread.join()

        self._display_machine_learning_result(images[0])

    def _display_machine_learning_result(self, image):
        ml_result = self.get_machine_learning_result()
        result = MachineLearningThread.visualize_result(image, ml_result)
        cv2.imshow('GM Pick-Point', result)


if __name__ == '__main__':
    main_thread = Main()
    main_thread.main_loop()
