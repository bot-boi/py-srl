from threading import Thread, Lock
from PIL import Image
from Xlib import X, error as Xerror
import time
import numpy as np
from ewmh import EWMH
ewmh = EWMH()


# check if window exists, only used in tests
def is_window(title: str) -> bool:
    clients = ewmh.getClientList()
    for client in clients:
        if title == ewmh.getWmName(client):
            return True
    return False


# stuff for getting client xwindow
# get xwindow object
def get_window(title: str):
    assert(type(title) == str)
    clients = ewmh.getClientList()
    for client in clients:
        if title == ewmh.getWmName(client):
            return client
    print('{} not found'.format(title))


# get frame of an xwindow object
# works for runelite, unsure for other apps
def get_frame(client):
    frame = client
    while frame.query_tree().parent != ewmh.root:
        frame = frame.query_tree().parent
    return frame


# get runelite canvas
def get_canvas(client):  # search osrs client children for canvas
    canvas_name = "sun-awt-X11-XCanvasPeer"
    for child in client.query_tree().children:   # tested for runelite only
        for child1 in child.query_tree().children:
            for child2 in child1.query_tree().children:
                assert(type(ewmh.getWmName(child2)) == str)
                if ewmh.getWmName(child2) == canvas_name:
                    return child2
    print('{} not found'.format(canvas_name))


# get frame of an xwindow, accepts name of window
def get_window_frame(title: str):
    return get_frame(get_window(title))


# Capture class, represents constant capture of a window
# init with Capture(ClientWindow("RuneLite"))
class Capture:
    def __init__(self, window_title: str):
        self.window = get_window(window_title)
        self.target = get_canvas(self.window)
        self.lock: Lock = Lock()    # mutex lock thing
        self.thread: Thread = None  # the capture thread (init w/ self.start())
        self.kill: bool = False     # used to kill thread capture thread
        self.image: Image = None

    # starts the capture thread
    def start(self):
        self.kill = False
        self.thread = Thread(target=self.capture_thread)
        self.thread.start()

    # terminates the capture thread
    def terminate(self):
        self.kill = True

    # thread capture job
    # TODO: it might make more sense to output arrays of pixels
    # instead of Image objects
    def capture_thread(self):
        while True:
            # t1 = time.time()
            if self.kill:  # check if killed
                return 0

            # get the shape of the window and reload canvas if it fails
            # canvas id changes on resize, other events cause this too ?
            try:
                g = self.target.get_geometry()
            except Xerror.BadDrawable or Xerror.BadMatch:
                print("bad drawable")
                self.target = get_canvas(self.window)
                g = self.target.get_geometry()
            # get raw img data of window NOTE: these are python xlib calls
            raw = self.target.get_image(0, 0, g.width, g.height, X.ZPixmap,
                                        0xffffffff)
            # convert raw to opencv image
            if type(raw.data) == str:
                # this means window is minimized or covered (not rendering)
                print('Window hidden, slowing capture to every 10 seconds',
                      flush=True)
                time.sleep(10)
            else:
                img = Image.frombytes("RGB", (g.width, g.height), raw.data,
                                      "raw", "BGRX")
                if img is None:
                    print('img grab failed')
                # output image
                self.lock.acquire()
                self.image = np.array(img.copy())
                self.lock.release()
                # t2 = time.time()
                # print("capture thread ran in {}".format(t2-t1))

    # returns latest capture
    def get_image(self) -> np.ndarray:
        self.lock.acquire()
        arr = self.image.copy()
        self.lock.release()
        return arr
