import threading

class StereoCameraThread(threading.Thread):

    CAMERA_SELECTION_TYPE = dict(RANDOM=0, RIGHT=1, LEFT=2)

    """
    Abstract Class
    """

    def __init__(self):
        super(StereoCameraThread, self).__init__()

    def get_stereo_images(self, num_images):
        """
        Outward facing abstract method to obtain stereo images from a stereo camera
        :param num_images: The number of stereo images to take
        :return: a list of stereo image pairs.
        """
        raise NotImplementedError('Methods get_stereo_images is not defined')

    def _get_stereo_images(self, num_images):
        """
        Inward facing abstract method to obtain stereo images from a stereo camera
        :param num_images: The number of stereo images to take
        :return: a list of stereo image pairs.
        """
        raise NotImplementedError('Methods get_stereo_images is not defined')

    def get_mono_images(self, num_images, camera_to_use='RANDOM'):
        """
        Outward facing abstract method to obtain mono images from a stereo camera
        :param num_images: The number of mono images to take
        :param camera_to_use: Which camera should be used to take the images
        :return: a list of mono images
        """
        raise NotImplementedError('Methods get_mono_images is not defined')

    def _get_mono_images(self, num_images, camera_to_use):
        """
        Inward facing abstract method to obtain mono images from a stereo camera
        :param num_images: The number of mono images to take
        :param camera_to_use: Which camera should be used to take the images
        :return: a list of mono images
        """
        raise NotImplementedError('Methods get_mono_images is not defined')
