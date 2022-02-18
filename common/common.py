from queue import Queue
import threading

que = Queue(maxsize=-1)

lock = threading.Lock()


