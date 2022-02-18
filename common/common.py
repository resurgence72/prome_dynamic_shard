import threading
from queue import Queue


class Common(object):
    que = Queue(maxsize=-1)
    lock = threading.Lock()


com = Common()
