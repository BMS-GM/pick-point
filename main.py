import threading
import numpy as np
import cv2
import logging
import datetime
import traceback
import copy
import time

from CameraDriver.SpinStereoCameraDriver import SpinStereoCameraDriver
from NeuralNetwork import MachineLearningThread
from SQL_Driver import ObjectDB

LOG_DIR = 'Logs'
LEFT_CAMERA_SERIAL_NUM = '18585124'
RIGHT_CAMERA_SERIAL_NUM = '18585121'
GRAPH_TYPE = 'SSD_INCEPTION_V2'


class Main:

    def __init__(self):
        # =================================
        # Setup Logging
        # =================================
        # Create master logger and set global log level
        self._logger = logging.getLogger("GM_Pick_Point")
        self._logger.setLevel(logging.DEBUG)

        # create log file
        file_handler = logging.FileHandler(LOG_DIR + '/GM_Pick_Point - %s.log' %
                                           datetime.datetime.now().strftime("%Y.%m.%d-%H.%M.%S"))
        file_handler.setLevel(logging.DEBUG)

        # create console logger
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # Format Log
        log_formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(name)s - %(message)s')
        file_handler.setFormatter(log_formatter)
        console_handler.setFormatter(log_formatter)

        # Add outputs to main logger
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)
        # =====================================================================

        self._sql_db = ObjectDB.ObjectDB()

        # Setup Multi-threading
        self._logger.debug('Initializing Camera Thread')
        self._camera_thread = SpinStereoCameraDriver(LEFT_CAMERA_SERIAL_NUM, RIGHT_CAMERA_SERIAL_NUM)
        self._logger.debug('Initializing Machine Learning Thread')
        self._machine_learning_thread = MachineLearningThread.MachineLearningThread(LOG_DIR, graph_type=GRAPH_TYPE)
        self._logger.debug('Initializing SQL Thread')
        self._sql_thread = None
        self._logger.debug('Initializing Depth Map Thread')
        self._depth_map_thread = None
        self._logger.debug('Threads Initialized')

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
        try:
            self._logger.debug('Starting Machine Learning Thread')
            self._machine_learning_thread.start()
            self._logger.debug('Starting Camera Thread')
            self._camera_thread.start()

            while True:
                process_images_task_thread = threading.Thread(target=self._process_next_images())
                sql_task_thread = threading.Thread(target=self._call_sql_thread())
                try:
                  process_images_task_thread.start()
                  sql_task_thread.start()
                except Exception as e:
                  process_images_task_thread.join()
                  sql_task_thread.join()
                  raise Exception(e)
                else:
                  process_images_task_thread.join()
                  sql_task_thread.join()
        except Exception:
            tb = traceback.format_exc()
            self._logger.error('Unhandled Exception:\n%s' % str(tb))
        finally:
            # Request Termination of Threads
            self._logger.debug('Terminating Machine Learning Thread')
            self._machine_learning_thread.terminate_thread()
            self._logger.debug('Terminating Camera Thread')
            self._camera_thread.terminate_thread()
            # self._logger.debug('Terminating SQL Thread')
            # self._sql_thread.terminate_thread()

            # Join all threads
            self._logger.debug('Joining Machine Learning Thread')
            self._machine_learning_thread.join()
            self._logger.debug('Joining Camera Thread')
            self._camera_thread.join()

    def get_camera_images(self):
        self._logger.debug('Getting Camera Image...')
        self._camera_thread_complete.wait()
        with self._camera_result_lock:
            result = copy.deepcopy(self._camera_result)

        self._logger.debug('Getting Camera Image - COMPLETE')
        return result

    def _call_camera_thread(self):
        # Get then next set of images
        self._camera_thread_complete.clear()
        with self._camera_result_lock:
            self._camera_result = self._camera_thread.get_stereo_images(1)
            self._camera_thread_complete.set()

    def get_machine_learning_result(self):
        self._logger.debug('Getting Machine Learning Results...')
        self._machine_learning_thread_complete.wait()
        with self._machine_learning_result_lock:
            result = copy.deepcopy(self._machine_learning_result)

        self._logger.debug('Getting Machine Learning Results - COMPLETE')
        return result

    def _call_machine_learning_thread(self, image):
        self._machine_learning_thread_complete.clear()
        with self._machine_learning_result_lock:
            self._machine_learning_result = self._machine_learning_thread.process_image(image)
            self._machine_learning_thread_complete.set()

    def get_depth_map(self):
        self._logger.debug('Getting Depth Map...')
        self._depth_map_thread_complete.wait()
        with self._depth_map_result_lock:
            result = copy.deepcopy(self._depth_map_result)

        self._logger.debug('Getting Depth Map - COMPLETE')
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
            result =  copy.deepcopy(self._sql_result)
        return result

    def _call_sql_thread(self):
        self._sql_thread_complete.clear()
        with self._sql_result_lock:
            next_incomplete_job = self._sql_db.get_incomplete_job()
            if next_incomplete_job is None:
                raise ValueError("Database is empty")

            self._sql_result = self._sql_db.get_object_list(next_incomplete_job[1])
            self._sql_thread_complete.set()

    def _process_next_images(self):
        self._logger.debug('Calling Camera Thread...')
        self._call_camera_thread()
        images = self.get_camera_images()
        self._logger.debug('Calling Camera Thread - COMPLETE')

        left = images[0][0]
        right = images[0][1]
        self._logger.debug('Calling Machine Learning Thread...')
        ml_task_thread = threading.Thread(target=self._call_machine_learning_thread, args=[left])

        self._logger.debug('Calling Depth Map Thread Thread...')
        depth_map_task_thread = threading.Thread(target=self._call_depth_map_thread, args=[(left, right)])

        try:
            ml_task_thread.start()
            depth_map_task_thread.start()
        except Exception:
            tb = traceback.format_exc()
            self._logger.error('Unhandled Exception:\n%s' % str(tb))
            ml_task_thread.join()
            self._logger.debug('Calling Machine Learning Thread - COMPLETE')
            depth_map_task_thread.join()
            self._logger.debug('Calling Depth Map Thread - COMPLETE')
            raise Exception('Unhandled Exception')
        else:
            ml_task_thread.join()
            self._logger.debug('Calling Machine Learning Thread - COMPLETE')
            depth_map_task_thread.join()
            self._logger.debug('Calling Depth Map Thread - COMPLETE')

        self._display_machine_learning_result(left)

    def _display_machine_learning_result(self, image):
        ml_result = self.get_machine_learning_result()
        result = MachineLearningThread.visualize_result(image, ml_result)
        result = cv2.resize(result, (0, 0), fx=0.5, fy=0.5)
        cv2.imshow('GM Pick-Point', result)
        cv2.waitKey(1)                      # DO NOT REMOVE: For some reason this works


if __name__ == '__main__':
    main_thread = Main()
    main_thread.main_loop()
