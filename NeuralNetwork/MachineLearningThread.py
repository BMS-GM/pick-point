#!/usr/bin/env python
"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

Class to create a separate thread to run TF models in
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'

import threading
import logging
import datetime
import copy

from NeuralNetwork import NeuralNetwork as neuralNet

GRAPHS = dict(FASTER_RCNN_RESNET='C:\\Users\\jmjerred-adm\\PycharmProjects\\pick-point\\NeuralNetwork\\'
                                 'faster_rcnn_resnet101_coco\\frozen_inference_graph.pb',
              SSD_INCEPTION_V2='C:\\Users\\jmjerred-adm\\PycharmProjects\\pick-point\\NeuralNetwork\\'
                               'ssd_inception_v2_coco\\frozen_inference_graph.pb')

class MachineLearningThread(threading.Thread):

    def __init__(self, log_dir, graph_type="FASTER_RCNN_RESNET"):
        """
        Constructor for MachineLearningThread
        :param log_dir: director to place log files in
        :param graph_type: The type of graph to run
        """

        # Setup Threading
        super(MachineLearningThread, self).__init__()       # Initialize Thread
        self._request_lock = threading.Lock()               # Lock used by requesting threads
        self._terminate_thread_event = threading.Event()    # Event used to stop the thread
        self._request_processing_event = threading.Event()  # Event used to start processing an image
        self._result_is_ready_event = threading.Event()     # Event to notify a thread that the processing is complete
        self._input_image = None
        self._output_matrix = None

        # init the logger
        self._logger = logging.getLogger('GM_Pick_Point.' + self.__class__.__name__)

        # Start TF Model
        self._network = neuralNet.Network(GRAPHS[graph_type], log_dir)
        self._network.setup_tf_logging()

    def run(self):
        """
        Run the Thread
        """
        self._logger.info("Thread Started")
        self._main_loop()
        self._logger.info("Terminating Thread - COMPLETE")

    def _main_loop(self):
        """
        Main Thread Loop
        """
        self._logger.info("Main Loop Started")
        while not self._terminate_thread_event.is_set():                # Check if thread should be terminated
            pending_request = self._request_processing_event.\
                wait(timeout=0.5)                                       # Check if a request is pending or until 500ms
            if pending_request:                                         # Check if a timeout occurred or job is pending
                self._logger.info("Processing Image...")
                self._request_processing_event.clear()                  # Clear pending job event
                self._output_matrix = self._network.feed_image(self._input_image)   # Process the image
                self._result_is_ready_event.set()                       # Notify waiting thread the image is processed
                self._logger.info("Processing Image - COMPLETE")

    def process_image(self, image):
        """
        Request an image be processed
        :param image: image to be processed
        :return: TF result Matrix
        """
        with self._request_lock:                            # Acquire Lock
            self._input_image = copy.deepcopy(image)        # Deep copy of data
            self._result_is_ready_event.clear()             # Set result as not ready
            self._request_processing_event.set()            # Notify thread of pending job
            self._result_is_ready_event.wait()              # Wait for image to be processed
            result = copy.deepcopy(self._output_matrix)     # Deep copy of result

        return result

    def terminate_thread(self):
        """
        Request Thread Termination
        """
        self._logger.info("Terminating Thread...")
        self._terminate_thread_event.set()


if __name__ == "__main__":
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
    console_handler.setLevel(logging.INFO)

    # Format Log
    log_formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(name)s - %(message)s')
    file_handler.setFormatter(log_formatter)
    console_handler.setFormatter(log_formatter)

    # Add outputs to main logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    # =====================================================================

    logger.debug("Creating MachineLearningThread")
    thread = MachineLearningThread(log_dir)
    logger.debug("Starting MachineLearningThread")
    thread.start()
    logger.debug("Terminating MachineLearningThread")
    thread.terminate_thread()
    logger.debug("Joining MachineLearningThread")
    thread.join()
    logger.debug("DONE")
