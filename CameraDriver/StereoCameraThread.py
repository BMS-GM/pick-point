import threading

class StereoCameraThread(threading.Thread):

    CAMERA_SELECTION_TYPE = dict(RANDOM=0, RIGHT=1, LEFT=2)

    """
    Abstract Class
    """

    def __init__(self):
        super(StereoCameraThread, self).__init__()

    def get_stereo_images(self, num_images, result):
        """
        Abstract method to obtain stereo images from a stereo camera
        :param num_images: The number of stereo images to take
        :param result: variable to hold the resulting images
        :return: a list of stereo image pairs.
        """
        raise NotImplementedError('Methods get_stereo_images is not defined')

    def get_mono_images(self, num_images, result, camera_to_use='RANDOM'):
        """
        Abstract method to obtain mono images from a stereo camera
        :param num_images: The number of mono images to take
        :param result: variable to hold the resulting images
        :param camera_to_use: Which camera should be used to take the images
        :return: a list of mono images
        """
        raise NotImplementedError('Methods get_mono_images is not defined')
