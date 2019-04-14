#!/usr/bin/env python
"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

Generic Neural Network Class
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'


import tensorflow as tf
import logging
import datetime
import cv2
import numpy as np
import copy

from Item import Item

FONT = cv2.FONT_HERSHEY_SIMPLEX
LABEL_MAP_BY_NAME = dict(bird_eye=1, bird_mouth=2, bird_wing=3, bird_body=4, bird_seeds=5, cat_eyes=6, cat_mouth=7,
                         cat_body=8, cat_ear=9, cat_food=10, dog_ear=11, dog_eyes=12, dog_mouth=13, dog_body=14,
                         dog_tail=15, dog_food=16)
LABEL_MAP_BY_ID = dict((value, key) for key, value in LABEL_MAP_BY_NAME.items())
MIN_SCORE = 0.5


class Network:

    def __init__(self, frozen_graph, log_dir):
        """
        Constructor Method
        :param frozen_graph: Path the frozen TF Graph
        """
        # init the logger
        self._logger = logging.getLogger('GM_Pick_Point.' + self.__class__.__name__)
        self._log_dir = log_dir

        # Read in Graph
        self._logger.info('Reading in Graph...')
        self._session = None                                # TF Session
        with tf.gfile.FastGFile(frozen_graph, 'rb') as f:
            self._graph_def = tf.GraphDef()
            self._graph_def.ParseFromString(f.read())
        self._logger.info('Reading in Graph - COMPLETE')

        self._logger.info('Restoring Graph...')
        self._init_session()
        self._session.graph.as_default()
        tf.import_graph_def(self._graph_def, name='')
        self._logger.info('Restoring Graph - COMPLETE')

    def __del__(self):
        """
        Deconstructor Method
        """
        self._close_session()

    def _init_session(self):
        """
        Initialize a new TensorFlow Session
        """
        self._logger.info('Initializing Tensorflow Session...')
        self._session = tf.Session()
        self._logger.info('Initializing Tensorflow Session - COMPLETE')

    def _close_session(self):
        """
        Terminatethe current TensorFlow Session
        """
        self._logger.info('Closing Tensorflow Session...')
        self._session.close()
        self._logger.info('Closing Tensorflow Session - COMPLETE')

    def setup_tf_logging(self):
        """
        Setup the log file for Tensorflow
        """
        self._logger.info('Setup Tensorflow Logging...')

        # get TF logger
        tf_log = logging.getLogger('tensorflow')
        tf_log.setLevel(logging.DEBUG)

        # create log file
        tf_file_handler = logging.FileHandler(self._log_dir + '/TensorFlow- %s.log' %
                                              datetime.datetime.now().strftime("%Y.%m.%d-%H.%M.%S"))
        tf_file_handler.setLevel(logging.DEBUG)

        # Format Log
        tf_log_formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(name)s - %(message)s')
        tf_file_handler.setFormatter(tf_log_formatter)

        # Add outputs to main logger
        tf_log.addHandler(tf_file_handler)

        self._logger.info('Setup Tensorflow Logging - COMPLETE')

    def feed_image(self, img):
        """
        Feeds an image to the current model and returns the result matrix
        :param img: The image to be processed
        :return: the TF result matrix
        """
        self._logger.info('Processing Image...')
        img = np.array(img)
        inp = cv2.resize(img, (300, 300))
        inp = inp[:, :, [2, 1, 0]]  # BGR2RGB

        out = self._session.run([self._session.graph.get_tensor_by_name('num_detections:0'),
                                 self._session.graph.get_tensor_by_name('detection_scores:0'),
                                 self._session.graph.get_tensor_by_name('detection_boxes:0'),
                                 self._session.graph.get_tensor_by_name('detection_classes:0')],
                                feed_dict={'image_tensor:0': inp.reshape(1, inp.shape[0], inp.shape[1], 3)})

        self._logger.info('Processing Image - COMPLETE')
        return out

    @staticmethod
    def get_num_objects_detected(network_output):
        """
        Get a dict containing the number of each type of object detected
        :param network_output: The output of the NN
        :return: A dict
        """
        result = dict()
        for key in LABEL_MAP_BY_NAME.keys():
            result[key] = 0

        num_detections = int(network_output[0][0])
        for i in range(num_detections):
            class_id = int(network_output[3][0][i])
            score = float(network_output[1][0][i])
            if score >= MIN_SCORE:
                class_name = LABEL_MAP_BY_ID[class_id]
                result[class_name] += 1
        return result

    @staticmethod
    def get_item_locations(network_output):
        result = []
        num_detections = int(network_output[0][0])

        for i in range(num_detections):
            class_id = int(network_output[3][0][i])
            score = float(network_output[1][0][i])
            bbox = [float(v) for v in network_output[2][0][i]]

            if score >= MIN_SCORE:
                class_name = LABEL_MAP_BY_ID[class_id]

                x = (bbox[1] + bbox[3]) / 2.0
                y = (bbox[0] + bbox[2]) / 2.0
                result.append(Item(class_name, x=x, y=y))
        return result

    @staticmethod
    def visualize_output(img, network_output, label="ALL", max_labels=float('inf'),
                         display_class_name=True, display_score=True):
        """
        Draws boxes and labels all found object in the image
        :param img: image to draw on
        :param network_output: the TF result matrix
        :param label: The class to label (by default all classes are labeled)
        :param max_labels: The maximum number of labels to display (by default it is infinity)
        :param display_class_name: If true then the class name is also displayed on the resulting image
        :param display_score: : If true then the score is also displayed on the resulting image
        :return: labeled image
        """
        rows = img.shape[0]
        cols = img.shape[1]
        result_img = copy.deepcopy(img)
        num_detections = int(network_output[0][0])
        display_all = label == "ALL"
        num_labels = 0
        for i in range(num_detections):
            class_id = int(network_output[3][0][i])
            score = float(network_output[1][0][i])
            bbox = [float(v) for v in network_output[2][0][i]]
            if score >= MIN_SCORE and (display_all or LABEL_MAP_BY_ID[class_id] == label):
                x = bbox[1] * cols
                y = bbox[0] * rows
                right = bbox[3] * cols
                bottom = bbox[2] * rows
                cv2.rectangle(result_img, (int(x), int(y)), (int(right), int(bottom)), (125, 255, 51), thickness=2)

                if display_class_name:
                    class_name = LABEL_MAP_BY_ID[class_id]
                else:
                    class_name = ""

                if display_score:
                    score_txt = "%0.2f" % (score * 100)
                else:
                    score_txt = ""
                class_text = "%s %s" % (class_name, score_txt)
                cv2.putText(result_img, class_text, (int(x), int(y)), FONT, 1, (255, 255, 255), 2, cv2.LINE_AA)

                # check max labels
                num_labels += 1
                if num_labels > max_labels:
                    break

        return result_img
