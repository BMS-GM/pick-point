#!/usr/bin/env python
"""
--------------------------------------------------------------------
Michigan  Technological University: Blue Marble Security Enterprise
--------------------------------------------------------------------

GUI.py
Author: Max Hoglund, Alek Ertman
Date Last Modified: 12/2/20
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

# List of legal status codes
STATUS = dict(ERROR=0,
              SUCCESS=1,
              WAITING=2)


class GUI(threading.Thread):
    def __init__(self):
        """
        Constructor
        """

        # Threading
        threading.Thread.__init__(self)
        self._update_request_lock = threading.RLock()
        self._terminate_event = threading.Event()
        self._next_object_request_event = threading.Event()
        self._reset_gui_request_event = threading.Event()
        self._request_queue = queue.Queue()

        self._FONT = ("Times", 24)     # Defines standard font of Times New Roman 30pt
        self._BG = "gray"

        self._root = None           # Defines root of tkinter window

        # Setup logging
        self._logger = logging.getLogger('GM_Pick_Point.' + self.__class__.__name__)
        self._logger.debug('Setting up GUI')
        self._log_messages = []
        self._log_request_lock = threading.Lock()
        self.start()

    def run(self):
        """
        Main Thread function
        """

        self._logger.debug("Thread Started")
        try:
            self._setup_gui()
            self._main_loop()

        except Exception:
            tb = traceback.format_exc()
            self._logger.error('Unhandled Exception:\n%s' % str(tb))

        finally:
            self._logger.debug('Destroying GUI...')
            self._terminate_event.set()
            self._root.quit()
            self._logger.debug('Destroying GUI - COMPLETE')

        self._logger.info('Terminating Thread')
        return

    def terminate_thread(self):
        """
        Function for an external thread to request the termination of this thread
        """
        self._logger.debug('Termination Requested')
        self._terminate_event.set()

    def _main_loop(self):
        """
        Main Loop of the thread
        Exit on termination request set or on error
        """
        self._logger.debug('Starting Main Loop')
        while not self._terminate_event.is_set():
            if not self._request_queue.empty():             # Check is request is pending
                self._logger.debug('Processing Next Request')
                next_request = self._request_queue.get()    # Get Next Request
                next_request[0](*next_request[1])           # Call Request

            self._next_object_request_event.clear()
            self._root.update()

    def _setup_gui(self):
        """
        Function to setup the GUI and init all the fields
        This must be run by the thread that will control the GUI
        """
        self._logger.debug('Setting Up GUI...')
        self._root = tk.Tk()  # Defines root of tkinter window

        # Setup Window
        self._root.title("pick-point")  # Set title
        self._root.geometry("400x1100")  # Set fixed resolution to 400x1100
        self._root.resizable(0, 0)  # Don't allow resizing
        self._root.configure(background="gray")

        # Object Labels
        self._object_static = tk.Label(self._root, bg=self._BG, text="Object:", font=self._FONT, anchor="w")
        self._object = tk.Label(self._root, bg=self._BG, text="", font=self._FONT, anchor="w")
        self._object_static.grid(row=0, column=0)
        self._object.grid(row=0, column=1)

        # Bin labels
        self._bin_static = tk.Label(self._root, bg=self._BG, text="Placement:", font=self._FONT, anchor="w")
        self._bin = tk.Label(self._root, bg=self._BG, text="", font=self._FONT, anchor="w")
        self._bin_static.grid(row=1, column=0)
        self._bin.grid(row=1, column=1)

        # Coordinate Labels
        self._coord_static = tk.Label(self._root, bg=self._BG, text="Coordinates:", font=self._FONT, anchor="w")
        self._coord = tk.Label(self._root, bg=self._BG, text="X: \nY: \nZ: ", font=self._FONT, anchor="w")
        self._coord_static.grid(row=2, column=0)
        self._coord.grid(row=2, column=1)

        # Next Button
        self._next_button_text = tk.StringVar()
        self._update_button = tk.Button(self._root, bg="gray20", textvariable=self._next_button_text, font=self._FONT,
                                        fg="white", width=8, command=self._button_update)
        self._next_button_text.set("Update")
        self._update_button.grid(row=3, column=0)

        # Reset Button
        self._reset_button = tk.Button(self._root, bg="gray20", text="Reset", font=self._FONT,
                                       fg="white", width=8, command=self._button_reset)
        self._reset_button.grid(row=3, column=1)

        # Result Label
        self._result = tk.Label(self._root, bg="white", text="", font=self._FONT, fg="white")
        self._result.grid(row=4, columnspan=2, pady=10)
        
        '''
        # Arm Speed Label
        self._speed_static = tk.Label(self._root, bg=self._BG, text="Arm Speed %:", font=self._FONT, anchor="w")
        self._speed_static.grid(row=5, column=0)

        # Arm Speed Slider
        self._arm_speed_percentage = tk.IntVar()
        self._speed = tk.Scale(self._root, bg=self.BG, font=self._FONT, orient=HORIZONTAL, from_=0, to=100,
                               variable=self._arm_speed_percentage, resolution=5)
        self._speed.grid(row=5, column=1)

        # Stop Button
        self._stop_button_text = tk.StringVar()
        self._stop_button = tk.Button(self._root, bg="gray20", text=self._stop_button_text, font=self._FONT,
                                       fg="white", width=8, command=self._button_stop)
        self._next_button_text.set("Stop")
        self._stop_button.grid(row=6, columnspan=2)
        '''
        # Log Label
        self._log = tk.Label(self._root, bg=self._BG, font=("Times", 14), text="Log:", anchor="w")
        self._log.grid(row=7, columnspan=2, pady=10)
        self._logger.debug('Setting Up GUI - COMPLETE')

    def set_result(self, status, error='Unknown Error', item='None', placement='None', x=0, y=0, z=0):
        """
        External Facing Generic method to set the result of one loop through the main thread
        :param status:      The status code used to interpret the kward args
        :param error:       The error message
        :param item:        The name of the item
        :param placement:   The name of the location the item should be placed
        :param x:           The X coord of the object
        :param y:           The Y coord of the object
        :param z:           The Z coord of the object
        """
        self._logger.debug('Submitting request to update on event')
        if status == STATUS["SUCCESS"]:
            self._request_queue.put((self._on_success, (item, placement, x, y, z)))

        elif status == STATUS["ERROR"]:
            self._request_queue.put((self._on_fail, (error,)))

        elif status == STATUS["WAITING"]:
            self._request_queue.put((self._on_waiting, (item, placement, x, y, z)))

    def add_msg_to_log(self, msg):
        """
        Adds a passed message to the log output on the GUI
        :param msg: The message to add
        """
        with self._log_request_lock:
            if len(self._log_messages) == MAX_LOG_LENGTH:
                self._log_messages.pop()
            self._log_messages.append(msg)

        self._request_queue.put((self._update_log, tuple()))

    def _on_success(self, item, placement, x, y, z):
        """
        Internal facing method to process requests with the SUCCESS code
        :param item:        Name of the item
        :param placement:   The name of the location the item should be placed at
        :param x:           X coord of the item
        :param y:           Y coord of the item
        :param z:           Z coord of the item
        """
        self._result.configure(bg="green", text="Success")
        self._set_object(item)
        self._set_bin(placement)
        self._set_coordinates(x, y, z)
        self.add_msg_to_log("Object identified successfully")
        self._next_button_text.set("Next Object")

    def _on_fail(self, error):
        """
        Internal facing method to process requests with the ERROR code
        :param error: Error message to display
        """
        self._result.configure(bg="red", text="Error")
        self.add_msg_to_log(error)
        self._clear()

    def _on_waiting(self, item, placement, x, y, z):
        """
        Internal facing method to process requests with the WAITING code

        :param item:        Name of the item
        :param placement:   The name of the location the item should be placed at
        :param x:           X coord of the item
        :param y:           Y coord of the item
        :param z:           Z coord of the item
        """
        self._result.configure(bg="orange", text="Waiting")
        self._set_object(item)
        self._set_bin(placement)
        self._set_coordinates(x, y, z)
        self._next_button_text.set("Update")

    def check_next_object_request(self):
        """
        Check if the next object has been requested
        :return: True if a request has been sent, False otherwise
        """
        return self._next_object_request_event.is_set()

    def wait_on_next_object_request(self):
        """
        Force external classing thread to wait until the object request has been set
        """
        self._next_object_request_event.wait()

    def _button_update(self):
        """
        Function called by the update button
        """
        self._next_object_request_event.set()

    def _button_reset(self):
        """
        Function called by the reset button
        """
        self._reset_gui_request_event.set()

    def _button_stop(self):
        """
        Function called by the stop button
        """
        self._stop_arm_request_event.set()

    def _set_object(self, type_new):
        """
        Internal facing function to set the object name field
        :param type_new: the name of the object
        """
        self._object.configure(text=type_new)

    def _set_bin(self, bin_new):
        """
        internal facing function to set the bin name field
        :param bin_new: the new name of the bin
        """
        self._logger.debug('Setting bin to: ' + bin_new)
        self._bin.configure(text=bin_new)

    def _set_coordinates(self, x, y, z):
        """
        internal facing function to set the X, Y, and Z coord fields
        :param x: The x coord of the object
        :param y: The y coord of the object
        :param z: the z coord of the object
        """
        coords_new = "X: %s\nY: %s\nZ: %s" % (x, y, z)
        self._logger.debug('Setting Coordinates: ' + coords_new)
        self._coord.configure(text=coords_new)

    def _update_log(self):
        """
        Internal facing function to update the log
        """
        with self._log_request_lock:
            log_msg = ""
            for msg in self._log_messages:
                log_msg += msg + '\n'
            self._log.configure(text=log_msg)

    def _clear(self):
        """
        Internal facing function to clear all object related fields
        :return:
        """
        self._object.configure(text="")
        self._bin.configure(text="")
        self._coord.configure(text="X: \nY: \nZ: ")


if __name__ == '__main__':
    # =================================
    # Setup Logging
    # =================================
    # Create master logger and set global log level
    '''
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
    '''
    #logger.debug('Stating GUI Thread')
    gui_thread = GUI()
    #logger.debug('HERE')
    time.sleep(5)
    #logger.debug('GOT HERE')
    gui_thread.set_result(1, item="Sphere", placement="Bin A", x=3, y=4, z=5)
    time.sleep(5)
    gui_thread.terminate()
    gui_thread.join()
    #logger.debug('Child Thread is Dead')
    # test.set_image("image.PNG")
