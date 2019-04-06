import tensorflow as tf
import logging
import datetime
import cv2
import PySpin
import sys
import os
import numpy as np

from CameraDriver.SpinCameraDriver import SpinCameraDriver


FONT = cv2.FONT_HERSHEY_SIMPLEX
LABEL_MAP = dict(bird_eye=1, bird_mouth=2, bird_wing=3, bird_body=4, bird_seeds=5, cat_eyes=6, cat_mouth=7, cat_body=8,
                 cat_ear=9, cat_food=10, dog_ear=11, dog_eyes=12, dog_mouth=13, dog_body=14, dog_tail=15, dog_food=16)
MIN_SCORE = 0.5
IMAGE_FOLDER = "C:\\Users\\jmjerred-adm\\PycharmProjects\\pick-point\\images\\capture\\mono_captures" \
               "\\Run_2019-04-01_17-15-04"
FROZEN_MODEL_PATH = "C:\\Users\\jmjerred-adm\\PycharmProjects\\pick-point\\NeuralNetwork\\export_model_faster_rcnn\\" \
                    "frozen_inference_graph.pb"
CAPTURE_PATH = "C:\\Users\\jmjerred-adm\\PycharmProjects\\pick-point\\NeuralNetwork\\captures\\"
LEFT_CAMERA_SERIAL_NUM = "18585124"


class Network:

    def __init__(self):
        # init the logger
        self._logger = logging.getLogger('GM_Pick_Point.' + self.__class__.__name__)

        self._session = None

        # Read in Graph
        self._logger.info('Reading in Graph...')
        with tf.gfile.FastGFile(FROZEN_MODEL_PATH, 'rb') as f:
            self._graph_def = tf.GraphDef()
            self._graph_def.ParseFromString(f.read())
        self._logger.info('Reading in Graph - COMPLETE')

        self._logger.info('Restoring Graph...')
        self._init_session()
        self._session.graph.as_default()
        tf.import_graph_def(self._graph_def, name='')
        self._logger.info('Restoring Graph - COMPLETE')

    def __del__(self):
        self._close_session()

    def _init_session(self):
        self._logger.info('Initializing Tensorflow Session...')
        self._session = tf.Session()
        self._logger.info('Initializing Tensorflow Session - COMPLETE')

    def _close_session(self):
        self._logger.info('Closing Tensorflow Session...')
        self._session.close()
        self._logger.info('Closing Tensorflow Session - COMPLETE')

    def setup_tf_logging(self):
        self._logger.info('Setup Tensorflow Logging...')

        # get TF logger
        tf_log = logging.getLogger('tensorflow')
        tf_log.setLevel(logging.DEBUG)

        # create log file
        tf_file_handler = logging.FileHandler('C:\\Users\\jmjerred-adm\\PycharmProjects\\pick-point\\Logs\\'
                                              'TensorFlow- %s.log' %
                                              datetime.datetime.now().strftime("%Y.%m.%d-%H.%M.%S"))
        tf_file_handler.setLevel(logging.DEBUG)

        # Format Log
        tf_log_formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(name)s - %(message)s')
        tf_file_handler.setFormatter(tf_log_formatter)

        # Add outputs to main logger
        tf_log.addHandler(tf_file_handler)

        self._logger.info('Setup Tensorflow Logging - COMPLETE')

    def feed_image(self, img):
        self._logger.info('Processing Image...')
        inp = cv2.resize(img, (300, 300))
        inp = inp[:, :, [2, 1, 0]]  # BGR2RGB

        out = self._session.run([self._session.graph.get_tensor_by_name('num_detections:0'),
                                 self._session.graph.get_tensor_by_name('detection_scores:0'),
                                 self._session.graph.get_tensor_by_name('detection_boxes:0'),
                                 self._session.graph.get_tensor_by_name('detection_classes:0')],
                                feed_dict={'image_tensor:0': inp.reshape(1, inp.shape[0], inp.shape[1], 3)})

        self._logger.info('Processing Image - COMPLETE')
        return out

    def visualize_output(self, img, network_output):
        self._logger.info('Visualizing Output on Image...')
        rows = img.shape[0]
        cols = img.shape[1]
        result_img = img.copy()
        num_detections = int(network_output[0][0])
        for i in range(num_detections):
            class_id = int(network_output[3][0][i])
            score = float(network_output[1][0][i])
            bbox = [float(v) for v in network_output[2][0][i]]
            if score >= MIN_SCORE:
                x = bbox[1] * cols
                y = bbox[0] * rows
                right = bbox[3] * cols
                bottom = bbox[2] * rows
                cv2.rectangle(result_img, (int(x), int(y)), (int(right), int(bottom)), (125, 255, 51), thickness=2)
                class_name = list(LABEL_MAP.keys())[list(LABEL_MAP.values()).index(class_id)]
                score_txt = "%0.2f" % (score * 100)
                class_text = "%s - %s" % (class_name, score_txt)
                cv2.putText(result_img, class_text, (int(x), int(y)), FONT, 1, (255, 255, 255), 2, cv2.LINE_AA)

        self._logger.info("Visualizing Output on Image - COMPLETE")
        return result_img


if __name__ == "__main__":
    # =================================
    # Setup Logging
    # =================================
    # Create master logger and set global log level
    logger = logging.getLogger("GM_Pick_Point")
    logger.setLevel(logging.DEBUG)

    # create log file
    file_handler = logging.FileHandler('C:\\Users\\jmjerred-adm\\PycharmProjects\\pick-point\\Logs\\test-v2 - %s.log' %
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

    logger.info('Creating Network')
    network = Network()

    # Load Camera
    logger.info("Initializing Camera...")
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()

    drivers = []
    for camera in cam_list:
        drivers.append(SpinCameraDriver(camera))

    # Find Cameras
    left_driver = None

    # Find Left Camera
    for driver in drivers:
        info = driver.get_info()
        if info[1] == LEFT_CAMERA_SERIAL_NUM:
            left_driver = driver
            logger.info("Initializing Camera - COMPLETE\n"
                        "\t Serial Number: %s\n"
                        "\t Vendor Name  : %s\n"
                        "\t Display Name : %s"
                        % (info[1], info[2], info[3]))

    if left_driver is None:
        logger.error("Unable to find Left Camera - EXITING")
        logger.info("Cleaning Up System ...")
        for driver in drivers:
            del driver
        del drivers
        del left_driver

        for camera in cam_list:
            del camera
        del cam_list

        system.ReleaseInstance()
        del system
        logger.info("Cleaning Up System - COMPLETE")
        sys.exit()

    # Release Unused Cameras:
    for driver in drivers:
        if driver is not left_driver:
            del driver
    del drivers

    img = np.zeros((1024, 1280, 3), np.uint8)

    # Run Live Feed
    logger.info('Start Live Feed')
    iteration = 0
    while True:

        # Get img
        got_image = True
        try:
            img = left_driver.get_image(1)[0]
        except IndexError:
            got_image = False
            img = np.zeros((1024, 1280, 3), np.uint8)
            text = "LOST CONNECTION"
            textsize = cv2.getTextSize(text, FONT, 4, 4)[0]
            textX = int((img.shape[1] - textsize[0]) / 2)
            textY = int((img.shape[0] + textsize[1]) / 2)

            cv2.putText(img, text, (textX, textY), FONT, 4, (255, 255, 255), 4)
            cv2.line(img, (0, 0), (1280, 1024), (150, 150, 150), 5)
            cv2.line(img, (1280, 0), (0, 1024), (150, 150, 150), 5)

        if got_image:
            result = network.feed_image(img)
            img = network.visualize_output(img, result)
            # cv2.imwrite(CAPTURE_PATH + 'img_%d.png' % iteration, img)
            iteration += 1

        img = cv2.resize(img, (0, 0), fx=0.75, fy=0.75)
        cv2.imshow('TensorFlow Output', img)

        k = cv2.waitKey(1)
        if k % 256 == 27:
            # ESC pressed
            logger.info("Escape hit, exiting...")
            break

    # delete all references to the cameras
    logger.info("Cleaning Up System ...")

    try:
        for driver in drivers:
            del driver
        del drivers
    except NameError:
        # Drivers already deleted
        pass
    del left_driver

    for camera in cam_list:
        del camera
    del cam_list

    # clean up the system
    system.ReleaseInstance()
    del system

    # clean up network
    del network
    logger.info("Cleaning Up System - COMPLETE")
