import threading
import numpy as np
import logging
import copy


class DepthMapThread(threading.Thread):

    def __init__(self, left_image, right_imaage):
        """
        Class Constructor. This also automatically starts the thread
        :param left_image: the left image in a stereo pair
        :param right_imaage: the right image in a stereo pair
        """
        # Setup Threading
        super(DepthMapThread, self).__init__()       # Initialize Thread
        self._image_ready_event = threading.Event()
        self._image_ready_event.clear()
        self._image_returned_event = threading.Event()
        self._image_returned_event.clear()

        self._left_image = left_image
        self._right_image = right_imaage
        self._result = None

        # init the logger
        self._logger = logging.getLogger('GM_Pick_Point.' + self.__class__.__name__)

        self.start()

    def run(self):
        self._logger.debug("Running Depth Map Thread...")

        rows = self._left_image.shape[0]
        cols = self._left_image.shape[1]

        self._result = np.zeros((rows, cols))
        self._image_ready_event.set()
        self._logger.debug("Depth Map - COMPLETE | Waiting for result to be requested")
        self._image_returned_event.wait()

    def get_image(self):
        self._logger.info("Requesting Depth Map Result")
        self._logger.info("Waiting For Image To Be Ready")
        self._image_ready_event.wait()
        image = copy.deepcopy(self._result)
        self._image_returned_event.set()
        self._logger.info("Retrieved Image")
        return image

    def terminate_thread(self):
        self._image_returned_event.set()
        self._image_ready_event.set()


