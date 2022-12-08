import sl

# Constants in meters
DESK_DEPTH = 0.83  # Desk depth from sensor
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
        # Create another Mat for depth map printouts
        self._depth_image = sl.Mat()
        self._num_captures = 0
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

        # debug -- print the depth of the middle of the picture. If the 
        # workfield is empty, that's the depth of the desk
        if self._zed_mini.grab(self._run_params) == sl.ERROR_CODE.SUCCESS:
            self._zed_mini.retrieve_measure(self._depth_map, sl.MEASURE.DEPTH)
            #DESK_DEPTH = self._depth_map.get_value(1280/2, 720/2)[1] / 1000
            print(f"starting desk depth: {DESK_DEPTH}")
            self._zed_mini.retrieve_image(self._depth_image, sl.VIEW.DEPTH)
            for i in range(int((1280/2)-2),int((1280/2)+3)):
                for j in range(int((720/2)-2), int((720/2)+3)):
                    self._depth_image.set_value(i, j, [0, 0, 0, 0, 0])
            self._depth_image.write("images/depth_map/init.png")

    def get_object_height(self, x: float, y: float) -> float:
        """Collects the height of an object in the picking area"""

        print(f"zed x, y : {x}, {y}")

        # Collect the entire depth map and save the specified coordinate depth
        object_depth = 840
        if self._zed_mini.grab(self._run_params) == sl.ERROR_CODE.SUCCESS:
            self._zed_mini.retrieve_measure(self._depth_map, sl.MEASURE.DEPTH)
            object_depth = self._depth_map.get_value(x, y)[1] / 1000

        print(f"object depth: {object_depth}")

        # debug -- save a grayscale copy of the depthmap
        self._zed_mini.retrieve_image(self._depth_image, sl.VIEW.DEPTH)
        # add a dot on the map where the zed mini just polled the depth of
        for i in range(int(x-2),int(x+3)):
            for j in range(int(y-2), int(y+3)):
                self._depth_image.set_value(i, j, [0, 0, 0, 0, 0])
        
        self._depth_image.write("images/depth_map/" + str(self._num_captures) + ".png")
        self._num_captures = self._num_captures + 1

        return ARM_OFFSET + (DESK_DEPTH - object_depth)
