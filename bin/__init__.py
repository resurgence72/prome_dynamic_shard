import sys
import signal
from utils.logger import log
from config.config import loader

signal_list = [signal.SIGINT, signal.SIGTERM, signal.SIGHUP]


def exit_signal_handler(signum, frame):
    log.warning("before exit: {}-{}", signum, frame)
    # TODO deregister when prome_shard exit
    log.warning("after exit: {}-{}\n", signum, frame)
    sys.exit(0)


for sig in signal_list:
    signal.signal(sig, exit_signal_handler)
