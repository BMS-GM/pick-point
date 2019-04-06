import threading
import numpy as np
import cv2
import tensorflow
import NeuralNetwork.NeuralNetwork

GRAPHS = dict(FASTER_RCNN_RESNET='NeuralNetwork/faster_rcnn_resnet101_coco/frozen_inference_graph.pb',
              SSD_INCEPTION_V2='NeuralNetwork/ssd_inception_v2_coco/frozen_inference_graph.pb')


class MachineLearningThread(threading.Thread):

    def __init__(self, graph_type="FASTER_RCNN_RESNET"):
        super(MachineLearningThread, self).__init__()
        self.name = graph_type


