import logging
from .constants import Color
from . import config


class CustomFormatter(logging.Formatter):
    LOG_LEVEL_FORMAT = "%(levelname)s"
    FORMATS = {
        logging.DEBUG: f"{LOG_LEVEL_FORMAT}",
        logging.INFO: f"{Color.GREEN}{LOG_LEVEL_FORMAT}{Color.RESET}",
        logging.WARNING: f"{Color.YELLOW}{LOG_LEVEL_FORMAT}{Color.RESET}",
        logging.ERROR: f"{Color.LIGHT_RED}{LOG_LEVEL_FORMAT}{Color.RESET}",
        logging.CRITICAL: f"{Color.BOLD}{Color.RED}{LOG_LEVEL_FORMAT}{Color.RESET}"
    }
    for log_level, log_format in FORMATS.items():
        FORMATS[log_level] = "%(asctime)s [{}] :: %(message)s".format(
            log_format)

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def set_log_level(log_level=None, return_loggers=False, external_only=False):
    if log_level is None:
        log_level = logging.ERROR
    all_loggers = {}
    for logger_name in logging.root.manager.loggerDict.keys():
        if external_only and logger_name.startswith("tweeterpy"):
            continue
        current_logger = logging.getLogger(logger_name)
        all_loggers[logger_name] = current_logger.level
        current_logger.setLevel(log_level)
    if return_loggers:
        return all_loggers


def disable_logger(original_function):
    def wrapper(*args, **kwargs):
        all_loggers = set_log_level(logging.ERROR, return_loggers=True)
        try:
            returned_output = original_function(*args, **kwargs)
        except Exception as error:
            raise error
        finally:
            if not config.DISABLE_LOGS:
                [logging.getLogger(current_logger).setLevel(all_loggers.get(
                    current_logger)) for current_logger in logging.root.manager.loggerDict.keys() if current_logger in list(all_loggers.keys())]
        return returned_output
    return wrapper


if __name__ == "__main__":
    pass
