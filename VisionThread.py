import threading
import numpy as np
import logging
import copy
import cv2
import datetime
import time
import traceback

from CameraDriver.SpinStereoCameraDriver import SpinStereoCameraDriver
from NeuralNetwork import MachineLearningThread
from Item import Item
from NeuralNetwork.NeuralNetwork import Network
from DepthMapDriver.DepthMapThread import DepthMapThread


class VisionThread(threading.Thread):

    def __init__(self, left_camera_id, right_camera_id, network_model, log_dir):
        # Setup Threading
        super(VisionThread, self).__init__()       # Initialize Thread

        # init the logger
        self._logger = logging.getLogger('GM_Pick_Point.' + self.__class__.__name__)

        # Setup Multi-threading
        self._terminate_thread_event = threading.Event()  # Event used to stop the thread

        self._logger.debug('Initializing Camera Thread')
        self._camera_thread = SpinStereoCameraDriver(left_camera_id, right_camera_id)
        self._camera_result = None
        self._camera_result_lock = threading.Lock()

        self._logger.debug('Initializing Machine Learning Thread')
        self._machine_learning_thread = MachineLearningThread.MachineLearningThread(log_dir, graph_type=network_model)
        self._machine_learning_result = None
        self._last_object_count = dict()
        self._current_object_count = dict()
        self._machine_learning_result_lock = threading.Lock()

        self._logger.debug('Initializing Depth Map Thread')
        self._depth_map_thread = None
        self._depth_map_result = []
        self._depth_map_result_lock = threading.Lock()

        # visualization settings:
        self._visualization_settings_lock = threading.RLock()
        self._display_results = False
        self._class_label_to_show = "ALL"
        self._max_labels = 1
        self._display_class_name = False
        self._display_score = False


        self._item_list = []
        self._item_list_lock = threading.Lock()

        self._logger.debug('Threads Initialized')

    def run(self):
        self._logger.debug('Starting Thread')
        self._main_loop()
        self._logger.debug('Terminated Thread')

    def get_machine_learning_result(self):
        with self._machine_learning_result_lock:
            result = copy.deepcopy(self._machine_learning_result)
        return result

    def get_images(self):
        with self._camera_result_lock:
            result = copy.deepcopy(self._camera_result)
        return result

    def get_depth_map(self):
        with self._depth_map_result_lock:
            result = copy.deepcopy(self._depth_map_result)
        return result

    def get_items(self):
        with self._item_list_lock:
            result = copy.deepcopy(self._item_list)
        return result

    def terminate_thread(self):
        self._logger.debug("Requesting Termination")
        self._terminate_thread_event.set()

    def _main_loop(self):
        self._logger.debug('Starting Machine Learning Thread')
        self._machine_learning_thread.start()
        self._logger.debug('Starting Camera Thread')
        self._camera_thread.start()

        try:
            while not self._terminate_thread_event.is_set():

                # Get images
                images = self._camera_thread.get_stereo_images(1)
                left = images[0][0]
                right = images[0][1]

                with self._camera_result_lock:
                    self._camera_result = (left, right)

                # process images
                self._depth_map_thread = DepthMapThread(left, right)
                ml_result = self._machine_learning_thread.process_image(left)
                depth_map = self._depth_map_thread.get_image()

                with self._depth_map_result_lock:
                    self._depth_map_result = depth_map

                with self._machine_learning_result_lock:
                    self._machine_learning_result = ml_result

                self._process_results()

                with self._visualization_settings_lock:
                    if self._display_results:
                        self._display_machine_learning_result(left)

        except Exception:
            tb = traceback.format_exc()
            self._logger.error('Unhandled Exception:\n%s' % str(tb))
            self._logger.error('Terminating All Threads')

        finally:
            self._logger.debug('Joining Machine Learning Thread')
            self._machine_learning_thread.terminate_thread()
            self._machine_learning_thread.join()
            self._logger.debug('Joining Camera Thread')
            self._camera_thread.terminate_thread()
            self._camera_thread.join()
            self._logger.debug('Joining Depth Map Thread')
            if self._depth_map_thread is not None:
                self._depth_map_thread.terminate_thread()
                self._depth_map_thread.join()

    def _process_results(self):
        depth_map = self.get_depth_map()
        depth_map = np.array(depth_map)
        rows = depth_map.shape[0]
        cols = depth_map.shape[1]

        ml_results = self.get_machine_learning_result()

        ml_items = Network.get_item_locations(ml_results)
        items = []
        for item in ml_items:
            x = int(item.x * cols)
            y = int(item.y * rows)
            z = depth_map[y, x]
            item.z = z
            items.append(item)

        with self._item_list_lock:
            self._item_list = items

    def set_visualization_settings(self, disply_results, label_to_show, max_labels, dipslay_class_name, display_score):
        with self._visualization_settings_lock:
            self._display_results = disply_results
            self._class_label_to_show = label_to_show
            self._max_labels = max_labels
            self._display_class_name = dipslay_class_name
            self._display_score = display_score

    def _display_machine_learning_result(self, image):
        ml_result = self.get_machine_learning_result()

        with self._visualization_settings_lock:
            result = Network.visualize_output(image, ml_result, label=self._class_label_to_show, max_labels=self._max_labels,
                                              display_class_name=self._display_class_name, display_score=self._display_score)
            result = cv2.resize(result, (0, 0), fx=0.5, fy=0.5)
            cv2.imshow('GM Pick-Point', result)
            cv2.waitKey(1)                      # DO NOT REMOVE: For some reason this works


if __name__ == '__main__':
    # =================================
    # Setup Logging
    # =================================
    # Create master logger and set global log level
    log_dir = "C:\\Users\\jmjerred-adm\\PycharmProjects\\pick-point\\Logs"
    logger = logging.getLogger("GM_Pick_Point")
    logger.setLevel(logging.DEBUG)

    # create log file
    file_handler = logging.FileHandler(log_dir + 'MachineLearningThread - %s.log' %
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
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    # =====================================================================

    LOG_DIR = 'Logs'
    LEFT_CAMERA_SERIAL_NUM = '18585124'
    RIGHT_CAMERA_SERIAL_NUM = '18585121'
    GRAPH_TYPE = 'SSD_INCEPTION_V2'

    logger.debug('Initializing Vision Thread...')
    visionThread = VisionThread(LEFT_CAMERA_SERIAL_NUM, RIGHT_CAMERA_SERIAL_NUM, GRAPH_TYPE, LOG_DIR)
    logger.debug('Initializing Vision Thread - COMPLETE')

    logger.debug('Starting Vision Thread...')
    visionThread.start()
    visionThread.set_visualization_settings(True, "ALL", float("inf"), True, True)
    logger.debug('Starting Vision Thread - COMPLETE')

    logger.debug('Sleeping for 30 seconds')
    time.sleep(30)
    logger.debug('Woke Up')

    logger.debug('Terminating Vision Thread...')
    visionThread.terminate_thread()
    visionThread.join()
    logger.debug('Terminating Vision Thread - COMPLETE')
