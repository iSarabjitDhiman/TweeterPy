import logging


class Color:
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    LIGHT_GRAY = "\033[0;37m"
    DARK_GRAY = "\033[1;30m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_GREEN = "\033[1;32m"
    YELLOW_2 = "\033[1;33m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_PURPLE = "\033[1;35m"
    LIGHT_CYAN = "\033[1;36m"
    LIGHT_WHITE = "\033[1;37m"
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"
    RESET = "\033[0m"


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
    if log_level and log_level not in logging._levelToName and log_level not in logging._levelToName.values():
        raise Exception("Invalid Log Level")
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
            [logging.getLogger(current_logger).setLevel(all_loggers.get(current_logger))
             for current_logger in logging.root.manager.loggerDict.keys() if current_logger in list(all_loggers.keys())]
        return returned_output
    return wrapper


if __name__ == "__main__":
    pass
