#!/usr/bin/env python
"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

Class for GUI
"""

__author__ = 'Blue Marble Security Enterprise'
__version__ = '1.0'

import tkinter as tk
import logging
import threading
import queue
import time
import datetime
import traceback

MAX_LOG_LENGTH = 5

STATUS = dict(SUCCESS=0,
              ERROR=1,
              WAITING=2)


class GUI(threading.Thread):
    def __init__(self):
        # Threading
        threading.Thread.__init__(self)
        self._update_request_lock = threading.RLock()
        self._terminate_event = threading.Event()
        self._next_object_request_event = threading.Event()
        self._reset_gui_request_event = threading.Event()
        self._request_queue = queue.Queue()

        self._FONT = ("Times", 30)     # Defines standard font of Times New Roman 30pt
        self._BG = "gray"

        self._root = None           # Defines root of tkinter window

        # Setup logging
        self._logger = logging.getLogger('GM_Pick_Point.' + self.__class__.__name__)
        self._logger.debug('Setting up GUI')
        self._log_messages = []
        self._log_request_lock = threading.Lock()
        self.start()

    def run(self):
        self._logger.debug("Thread Started")
        try:
            self._setup_gui()
            self._main_loop()

        except Exception:
            tb = traceback.format_exc()
            self._logger.error('Unhandled Exception:\n%s' % str(tb))

        finally:
            self._terminate_event.set()

        self._logger.info('Terminating Thread')
        return

    def terminate(self):
        self._logger.debug('Termination Requested')
        self._terminate_event.set()

    def _main_loop(self):
        self._logger.debug('Starting Main Loop')
        while not self._terminate_event.is_set():
            if not self._request_queue.empty():             # Check is request is pending
                self._logger.debug('Processing Next Request')
                next_request = self._request_queue.get()    # Get Next Request
                next_request[0](*next_request[1])           # Call Request

            self._root.update()
        self._logger.debug('Destroying GUI...')
        self._root.quit()
        self._logger.debug('Destroying GUI - COMPLETE')

    def _setup_gui(self):
        self._logger.debug('Setting Up GUI...')
        self._root = tk.Tk()  # Defines root of tkinter window

        # Setup Window
        self._root.title("pick-point")  # Set title
        self._root.geometry("1400x700")  # Set fixed resolution to 1400x700
        self._root.resizable(0, 0)  # Don't allow resizing
        self._root.configure(background="gray")

        '''
        # Live Feed
        self._camera_image = tk.PhotoImage(master=self._root, file="start_image.png")
        self._camera = tk.Label(self._root, image=self._camera_image)
        self._camera.place(x=860, y=30)
        '''

        # Object Labels
        self._object_static = tk.Label(self._root, bg=self._BG, text="Object:", font=self._FONT, anchor="w", width=8)
        self._object = tk.Label(self._root, bg=self._BG, text="", font=self._FONT, anchor="w", width=16)
        self._object_static.grid(row=0, column=0, padx=(100, 10), pady=(100, 10))
        self._object.grid(row=0, column=1, padx=(10, 100), pady=(100, 10))

        # Bin labels
        self._bin_static = tk.Label(self._root, bg=self._BG, text="Placement:", font=self._FONT, anchor="w", width=8)
        self._bin = tk.Label(self._root, bg=self._BG, text="", font=self._FONT, anchor="w", width=16)
        self._bin_static.grid(row=1, column=0, padx=(100, 10), pady=(0, 10))
        self._bin.grid(row=1, column=1, padx=(10, 100), pady=(0, 10))

        # Coordinate Labels
        self._coord_static = tk.Label(self._root, bg=self._BG, text="Coordinates:", font=self._FONT, anchor="w",
                                      width=9)
        self._coord = tk.Label(self._root, bg=self._BG, text="X: \nY: \nZ: ", font=self._FONT, anchor="w", width=16)
        self._coord_static.grid(row=2, column=0, padx=(120, 10), pady=(0, 65))
        self._coord.grid(row=2, column=1, padx=(10, 100), pady=(0, 65))

        # Next Button
        self._next_button = tk.Button(self._root, bg="gray20", text="Next", font=self._FONT,
                                      fg="white", width=8, command=self._button_next)
        self._next_button.grid(row=3, column=0, padx=(100, 0))

        # Reset Button
        self._reset_button = tk.Button(self._root, bg="gray20", text="Reset", font=self._FONT,
                                       fg="white", width=8, command=self._button_reset)
        self._reset_button.grid(row=3, column=1, padx=(0, 100))

        # Result Label
        self._result = tk.Label(self._root, bg="white", text="", font=self._FONT, fg="white", width=16, height=2)
        self._result.place(x=930, y=460)

        # Log Label
        self._log = tk.Label(self._root, bg=self._BG, font=("Times", 20), text="Log:", anchor="w", width=60)
        # self._log.place(x=120, y=580)
        self._log.place(x=860, y=30)
        self._logger.debug('Setting Up GUI - COMPLETE')

    # Takes 500x400 image as input
    def set_image(self, file):
        """
        Adds request to updated main image in GUI
        :param file: File location of the image
        """
        self._logger.debug('Submitting request to update image')
        image_new = tk.PhotoImage(master=self._root, file=file)
        self._request_queue.put((self._set_image, (image_new,)))

    def set_result(self, status, error='Unknown Error', item='None', placement='None', x=0, y=0, z=0):
        self._logger.debug('Submitting request to update on event')
        if status == STATUS["SUCCESS"]:
            self._request_queue.put((self._on_success, (item, placement, x, y, z)))

        elif status == STATUS["ERROR"]:
            self._request_queue.put((self._on_fail, (error,)))

        elif status == STATUS["WAITING"]:
            self._request_queue.put((self._on_waiting, (item, placement, x, y, z)))

    def add_msg_to_log(self, msg):
        with self._log_request_lock:
            if len(self._log_messages) == MAX_LOG_LENGTH:
                self._log_messages.pop()
            self._log_messages.append(msg)

        self._request_queue.put((self._update_log, tuple()))

    def _on_success(self, item, placement, x, y, z):
        self._result.configure(bg="green", text="Success")
        self._set_object(item)
        self._set_bin(placement)
        self._set_coordinates(x, y, z)
        self.add_msg_to_log("Object identified successfully")

    def _on_fail(self, error):
        self._result.configure(bg="red", text="Error")
        self.add_msg_to_log(error)
        self._clear()

    def _on_waiting(self, item, placement, x, y, z):
        self._result.configure(bg="orange", text="Waiting")
        self._set_object(item)
        self._set_bin(placement)
        self._set_coordinates(x, y, z)

    def check_next_object_request(self):
        return self._next_object_request_event.is_set()

    def wait_on_next_obeject_request(self):
            self._next_object_request_event.wait()

    def check_reset_reuqest(self):
        return self._reset_gui_request_event.is_set()

    def _button_next(self):
        self._next_object_request_event.set()

    def _button_reset(self):
        self._reset_gui_request_event.set()

    '''
    def _set_image(self, image):
        self._camera.configure(image=image)
        self._camera_image = image
    '''

    def _set_object(self, type_new):
        self._object.configure(text=type_new)

    def _set_bin(self, bin_new):
        self._logger.debug('Setting bin to: ' + bin_new)
        self._bin.configure(text=bin_new)

    def _set_coordinates(self, x, y, z):
        coords_new = "X: %s\nY: %s\nZ: %s" % (x, y, z)
        self._logger.debug('Setting Coordinates: ' + coords_new)
        self._coord.configure(text=coords_new)

    def _update_log(self):
        with self._log_request_lock:
            log_msg = ""
            for msg in self._log_messages:
                log_msg += msg + '\n'
            self._log.configure(text=log_msg)

    def _clear(self):
        self._object.configure(text="")
        self._bin.configure(text="")
        self._coord.configure(text="X: \nY: \nZ: ")


if __name__ == '__main__':
    # =================================
    # Setup Logging
    # =================================
    # Create master logger and set global log level
    log_dir = "C:\\Users\\jmjerred-adm\\PycharmProjects\\pick-point\\Logs"
    logger = logging.getLogger("GM_Pick_Point")
    logger.setLevel(logging.DEBUG)

    # create log file
    file_handler = logging.FileHandler(log_dir + '\\GUI - %s.log' %
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

    logger.debug('Stating GUI Thread')
    gui_thread = GUI()
    logger.debug('HERE')
    time.sleep(5)
    logger.debug('GOT HERE')
    gui_thread.set_result(1, item="Sphere", placement="Bin A", x=3, y=4, z=5)
    time.sleep(5)
    gui_thread.terminate()
    gui_thread.join()
    logger.debug('Child Thread is Dead')
    # test.set_image("image.PNG")
