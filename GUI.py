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


class GUIThread(threading.Thread):
    def __init__(self):
        super(GUIThread, self).__init__()
        self.gui = GUI()

    def run(self):
        self.gui.run()
        return


class GUI(threading.Thread):
    def __init__(self):

        # Threading
        self._update_request_lock = threading.Lock()
        self._updating_lock = threading.Lock()

        self._FONT = ("Times", 30)     # Defines standard font of Times New Roman 30pt
        self._BG = "gray"

        self._root = tk.Tk()           # Defines root of tkinter window

        # Setup logging
        self._logger = logging.getLogger('GM_Pick_Point.' + self.__class__.__name__)
        self._logger.debug('Setting up GUI')

        # Setup Window
        self._root.title("pick-point")   # Set title
        self._root.geometry("1400x700")  # Set fixed resolution to 1400x700
        self._root.resizable(0, 0)       # Don't allow resizing
        self._root.configure(background="gray")

        # Live Feed
        self._camera_image = tk.PhotoImage(master=self._root, file="start_image.png")
        self._camera = tk.Label(self._root, image=self._camera_image)
        self._camera.place(x=860, y=30)

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
        self._coord_static = tk.Label(self._root, bg=self._BG, text="Coordinates:", font=self._FONT, anchor="w", width=9)
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
        self._log.place(x=120, y=580)

    def run(self):
        try:
            self._root.mainloop()

        except Exception as e:
            print('Thread Terminated Unexpectedly')

        self._before_exit()
        print('Terminating Thread')
        return

    def _before_exit(self):
        try:
            self._root.destroy()
        except tk.TclError:
            pass

    # Takes 500x400 image as input
    def set_image(self, file):
        with self._update_request_lock:
            self._logger.debug('Updating live feed')
            image_new = tk.PhotoImage(master=self._root, file=file)
            self._set_image(image_new)

    def set_result(self, is_success, error='Unknown Error', item='None', placement='None', x=0, y=0, z=0):
        with self._update_request_lock:
            if is_success:
                self._result.configure(bg="green", text="Success")
                self._set_object(item)
                self._set_bin(placement)
                self._set_coordinates(x, y, z)
                self._set_log("Object identified successfully")
            else:
                self._result.configure(bg="red", text="Error")
                self._set_log(error)
                self._clear()

    def _button_next(self):
        raise NotImplementedError

    def _button_reset(self):
        raise NotImplementedError

    def _set_image(self, image):
        with self._updating_lock:
            self._camera.configure(image=image)
            self._camera_image = image

    def _set_object(self, type_new):
        with self._updating_lock:
            self._object.configure(text=type_new)

    def _set_bin(self, bin_new):
        with self._updating_lock:
            self._logger.debug('Setting bin to: ' + bin_new)
            self._bin.configure(text=bin_new)

    def _set_coordinates(self, x, y, z):
        coords_new = "X: {0}\nY: {1}\nZ: {2}".format(x, y, z)
        with self._update_request_lock:
            self._logger.debug('Setting Coordinates: ' + coords_new)
            self._coord.configure(text=coords_new)

    def _set_log(self, new_string):
        with self._update_request_lock:
            self._logger.debug('Log message: ' + new_string)
            self._log.configure(text="Log:\t" + new_string)

    def _clear(self):
        with self._updating_lock:
            self._object.configure(text="")
            self._bin.configure(text="")
            self._coord.configure(text="X: \nY: \nZ: ")


if __name__ == '__main__':
    gui_thread = GUIThread()
    print('HERE')
    gui_thread.run()
    print('GOT HERE')
    gui_thread.gui.set_result(1, item="Sphere", placement="Bin A", x=3, y=4, z=5)

    while gui_thread.is_alive():
        # Do Nothing
        pass

    print('Child Thread is Dead')
    # test.set_image("image.PNG")
