import logging
from logging import Logger, getLogger, Formatter, StreamHandler, INFO


def setting_logger(logger: Logger) -> Logger:
    formatter = Formatter(
        datefmt='%Y-%m-%d %H:%M:%S',
        fmt='%(levelname)s - %(asctime)s - %(name)s - (Line: %(lineno)d) - [%(filename)s]: %(message)s'
    )

    stream_handler = StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.handlers = [stream_handler]
    logger.setLevel(INFO)
    logger.propagate = False

    return logger


bot_logger = setting_logger(getLogger('bot'))
db_logger = setting_logger(getLogger('db'))

logging.basicConfig(level=INFO)