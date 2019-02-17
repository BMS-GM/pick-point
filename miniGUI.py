import tkinter as tk

class GUI:
    def __init__(self):
        self.root = tk.Tk()
        self.camera = None
        self.camera_image = None

        # Setup window
        self.root.title("pick-point")   # Set title
        self.root.geometry("1920x1080")  # Set fixed resolution to 1920x1080
        self.root.resizable(0, 0)       # Don't allow resizing

        # Camera image
        self.camera_image = tk.PhotoImage(file="test_image.png")
        self.camera = tk.Label(self.root, image=self.camera_image)
        self.camera.image = self.camera_image
        self.camera.place(relx=1.0, rely=0.0, anchor=tk.NE)

        # Close button
        self.close_button = tk.Button(self.root, text="Close", width="20", height="2", command=self.close_gui)
        self.close_button.grid(row=0, column=0)

        #Coordinate information
        self.set_data("~","~","~")

    def start_gui(self):
        self.root.mainloop()

    def close_gui(self):
        self.root.destroy()

    # Takes 1280x1024 image as input
    def set_image(self, image):
        img = tk.PhotoImage(file=image)
        self.camera.configure(image=img)
        self.camera.image = img

    def set_data(self, x, y, z):
        self.data = tk.Label(self.root, text="Object 1:\n\tX = {0}\n\tY = {1}\n\tZ = {2}".format(x, y, z))
        self.data.grid(row=1, column=0)

    def display_error(self, error):
        None


test = GUI()
test.start_gui()
test.set_image("test_image.png")