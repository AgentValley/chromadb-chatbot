import inspect
import logging
import logging.handlers

from logging.handlers import TimedRotatingFileHandler


def _get_caller_info():
    stack = inspect.stack()
    try:
        # stack[0] is the current frame (inside format method)
        # stack[1] is the caller frame (the log function call frame)
        index = 1

        while index < len(stack):
            caller_frame = stack[index]
            caller_filename = caller_frame.filename
            caller_lineno = caller_frame.lineno
            if "logger" not in caller_filename and "logging" not in caller_filename:
                filename_parts = caller_filename.split('/')
                return filename_parts[-1], caller_lineno
            index += 1
    except Exception as e:
        print(e)
    finally:
        # Ensure the stack is released to prevent memory leaks
        del stack


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;5;248m"
    yellow = "\x1b[38;5;221m"
    red = "\x1b[38;5;203m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(caller_filename)s:%(caller_lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        record.caller_filename, record.caller_lineno = _get_caller_info()
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logger(filename):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create console handler with a different formatter (not JSON)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    color_formatter = CustomFormatter()
    ch.setFormatter(color_formatter)

    if not filename:
        filename = 'logs/chromadb.log'

    # Create rotating file handler
    fh = TimedRotatingFileHandler(filename, when='D', interval=1, backupCount=30)
    fh.setLevel(logging.INFO)

    # FIX: Use JsonFormatter for 3rd Party Tools
    # jfh = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(message)s')
    # jfh.setFormatter(file_formatter)

    fh.setFormatter(color_formatter)

    # Add the handlers to the logger
    logger.addHandler(ch)
    logger.addHandler(fh)


def construct_log_message(message, *args, **kwargs):
    log_message = "[vectordb-chat] " + message
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


def log_warn(message, *args, **kwargs):
    logger = logging.getLogger(__name__)
    logger.warn(construct_log_message(message, *args, **kwargs))
