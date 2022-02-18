from loguru import logger


class MyLogger(object):

    def __init__(self, log_path):
        logger.add(
            # '/var/log/prome_shard.log',
            log_path,
            format="{time}|{level}|{message}",
            level="INFO",
            rotation="00:00",
            retention='20 days',
            compression="zip",
            enqueue=True,
            encoding='utf8',
        )
        self.logger = logger


log = MyLogger('/var/log/prome_shard/prome_shard_{time}.log').logger
