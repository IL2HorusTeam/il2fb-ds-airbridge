# coding: utf-8

import logging
import logging.handlers
import time

from functools import partial


LOG_FORMAT = "[%(levelname).1s %(asctime)s.%(msecs)03d] %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class NoTracebackFormatter(logging.Formatter):

    def format(self, record) -> str:
        record.message = record.getMessage()

        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)

        return self.formatMessage(record)


class ExceptionFilter(logging.Filter):

    def filter(self, record) -> bool:
        return record.exc_info or record.exc_text or record.stack_info


def get_file_handler_class(config):
    return (
        partial(
            logging.handlers.RotatingFileHandler,
            maxBytes=config.rotation.max_size,
            backupCount=config.rotation.max_backups,
            encoding=config.encoding,
        )
        if config.rotation.is_enabled
        else partial(
            logging.FileHandler,
            encoding=config.encoding,
        )
    )


def get_log_file_mode(keep_after_restart: bool) -> str:
    return 'a' if keep_after_restart else 'w'


def get_main_log_file_hangler(
    handler_class, level, file_path, time_converter, keep_after_restart,
    is_delayed,
):
    mode = get_log_file_mode(keep_after_restart)
    handler = handler_class(filename=file_path, mode=mode, delay=is_delayed)

    level = logging.getLevelName(level.upper())
    handler.setLevel(level)

    formatter = NoTracebackFormatter(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    formatter.converter = time_converter
    handler.setFormatter(formatter)

    return handler


def get_exceptions_log_file_hangler(
    handler_class, file_path, time_converter, keep_after_restart, is_delayed,
):
    mode = get_log_file_mode(keep_after_restart)
    handler = handler_class(filename=file_path, mode=mode, delay=is_delayed)
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    formatter.converter = time_converter
    handler.setFormatter(formatter)

    filter_ = ExceptionFilter()
    handler.addFilter(filter_)

    return handler


def setup_file_handlers(config):
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    handler_class = get_file_handler_class(config)
    time_converter = time.localtime if config.use_local_time else time.gmtime

    main_handler = get_main_log_file_hangler(
        handler_class=handler_class,
        time_converter=time_converter,
        **config.main
    )
    root_logger.addHandler(main_handler)

    exceptions_handler = get_exceptions_log_file_hangler(
        handler_class=handler_class,
        time_converter=time_converter,
        **config.exceptions
    )
    root_logger.addHandler(exceptions_handler)


def setup_logging(config):
    files_config = config.files
    if files_config:
        setup_file_handlers(files_config)
