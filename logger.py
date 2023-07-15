import logging
import logging.handlers

from logging.handlers import TimedRotatingFileHandler
from pythonjsonlogger import jsonlogger


def setup_logger(filename):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create console handler with a different formatter (not JSON)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    ch.setFormatter(console_formatter)

    # Create rotating file handler with JSON formatter
    if not filename:
        filename = 'logs/chromadb.log'
    file_handler = TimedRotatingFileHandler(filename, when='D', interval=1, backupCount=30)
    file_handler.setLevel(logging.INFO)
    file_formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(message)s')
    file_handler.setFormatter(file_formatter)

    # Add the handlers to the logger
    logger.addHandler(ch)
    logger.addHandler(file_handler)


def construct_log_message(message, *args, **kwargs):
    log_message = message
    if args:
        log_message += f" - {args}"
    if kwargs:
        log_message += f" - {kwargs}"
    return log_message


def log_error(message, *args, **kwargs):
    logger = logging.getLogger(__name__)
    logger.error(construct_log_message(message, *args, **kwargs))


def log_info(message, *args, **kwargs):
    logger = logging.getLogger(__name__)
    logger.info(construct_log_message(message, *args, **kwargs))


def log_debug(message, *args, **kwargs):
    logger = logging.getLogger(__name__)
    logger.debug(construct_log_message(message, *args, **kwargs))
