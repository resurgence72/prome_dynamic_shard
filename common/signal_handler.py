import signal


class SignalHandler(object):
    signal_list = [signal.SIGINT, signal.SIGTERM, signal.SIGHUP]

    def __init__(self):
        for sig in self.signal_list:
            signal.signal(sig, self.handler)

    @staticmethod
    def handler(signum, frame):
        print("start breake ")
        print("end breake ")
        exit()
