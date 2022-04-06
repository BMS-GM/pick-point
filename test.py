import sl

# Constants in meters
DESK_DEPTH = 0.85  # Desk depth from sensor
ARM_OFFSET = 0.1  # Arm offset for correct picking
SHIFT_AMNT = 0.4  # Arm shift amount for returning


class ZEDMiniDriver:
    """
    Runs the ZED Mini depth sensor
    """

    def __init__(self) -> None:
        # Create a camera and a set of initial parameters
        self._zed_mini = sl.Camera()
        self._init_params = sl.InitParameters()

        # Establish the initial parameters
        self._init_params.depth_mode = sl.DEPTH_MODE.QUALITY
        self._init_params.camera_resolution = sl.RESOLUTION.HD720
        self._init_params.coordinate_units = sl.UNIT.MILLIMETER
        self._init_params.depth_minimum_distance = 300
        self._init_params.depth_maximum_distance = 2000

        # Create a 'Mat' to store the depth information later
        self._depth_map = sl.Mat()
        self._run_params = sl.RuntimeParameters()

        # Open the zed mini
        if not self._zed_mini.is_opened():
            print("Opening ZED Mini...")
            status = self._zed_mini.open(self._init_params)
            if status is not sl.ERROR_CODE.SUCCESS:
                print("  Failure")
                print(repr(status))
                exit()
            print("  Success")

    def get_object_height(self, x: float, y: float) -> float:
        """Collects the height of an object in the picking area"""

        # Collect the entire depth map and save the specified coordinate depth
        object_depth = 850
        if self._zed_mini.grab(self._run_params) == sl.ERROR_CODE.SUCCESS:
            self._zed_mini.retrieve_measure(self._depth_map, sl.MEASURE.DEPTH)
            object_depth = self._depth_map.get_value(x, y) / 1000

        return ARM_OFFSET + (DESK_DEPTH - object_depth)


if __name__ == "__main__":
    cam = ZEDMiniDriver()