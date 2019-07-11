import logging
import logging.handlers
import os
import sys
import traceback
from enum import IntEnum, Enum
from logging.handlers import MemoryHandler
from types import MappingProxyType
from typing import Union

import fast_json
from colorlog import ColoredFormatter


DEFAULT_FORMAT = '%(levelname)s:%(name)s:%(message)s'


class LogFormat(IntEnum):
    stream = 0
    color = 1
    json = 2
    syslog = 3

    @classmethod
    def choices(cls):
        return tuple(cls._member_names_)


class DateFormat(Enum):
    color = '%Y-%m-%d %H:%M:%S'
    stream = '[%Y-%m-%d %H:%M:%S]'
    # Optimization: float value will be returned
    json = '%s'
    syslog = None


class JSONLogFormatter(logging.Formatter):
    LEVELS = MappingProxyType({
        logging.CRITICAL: "crit",
        logging.FATAL: "fatal",
        logging.ERROR: "error",
        logging.WARNING: "warn",
        logging.WARN: "warn",
        logging.INFO: "info",
        logging.DEBUG: "debug",
        logging.NOTSET: None,
    })

    FIELD_MAPPING = MappingProxyType({
        'filename': ('code_file', str),
        'funcName': ('code_func', str),
        'lineno': ('code_line', int),
        'module': ('code_module', str),
        'name': ('identifier', str),
        'msg': ('message_raw', str),
        'process': ('pid', int),
        'processName': ('process_name', str),
        'threadName': ('thread_name', str),
    })

    def __init__(self, fmt=None, datefmt=None, style='%'):
        super().__init__(
            datefmt=datefmt if datefmt is not Ellipsis else None,
            fmt=fmt, style=style
        )

    def format(self, record: logging.LogRecord):
        record_dict = MappingProxyType(record.__dict__)

        data = dict(errno=0 if not record.exc_info else 255)

        for key, value in self.FIELD_MAPPING.items():
            mapping, field_type = value

            v = record_dict.get(key)

            if not isinstance(v, field_type):
                v = field_type(v)

            data[mapping] = v

        for key in record_dict:
            if key in data:
                continue
            elif key[0] == "_":
                continue

            value = record_dict[key]

            if value is None:
                continue

            data[key] = value

        for idx, item in enumerate(data.pop('args', [])):
            data['argument_%d' % idx] = str(item)

        payload = {
            '@fields': data,
            'msg': record.getMessage(),
            'level': self.LEVELS[record.levelno],
        }

        if self.datefmt:
            payload['@timestamp'] = self.formatTime(record, self.datefmt)

        if record.exc_info:
            payload['stackTrace'] = "\n".join(
                traceback.format_exception(*record.exc_info)
            )

        return fast_json.dumps(payload, ensure_ascii=False)

    def formatTime(self, record, datefmt=None) -> Union[int, str]:
        if datefmt == '%s':
            return record.created
        return super().formatTime(record, datefmt=datefmt)


def json_formatter(stream=None, date_format=None):
    stream = stream or sys.stdout
    formatter = JSONLogFormatter(datefmt=date_format)
    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)
    return handler


def color_formatter(stream=None,
                    date_format=...) -> logging.Handler:

    date_format = (
        date_format if date_format is not Ellipsis else DateFormat.color.value
    )

    stream = stream or sys.stderr
    handler = logging.StreamHandler(stream)

    fmt = (
        "%(blue)s[T:%(threadName)s]%(reset)s "
        "%(log_color)s%(levelname)s:%(name)s%(reset)s: "
        "%(message_log_color)s%(message)s"
    )

    if date_format:
        fmt = "%(bold_white)s%(bg_black)s%(asctime)s%(reset)s {0}".format(fmt)

    handler.setFormatter(
        ColoredFormatter(
            fmt,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
            secondary_log_colors={
                'message': {
                    'WARNING': 'bold',
                    'ERROR': 'bold',
                    'CRITICAL': 'bold',
                },
            },
            datefmt=date_format,
            reset=True,
            style='%',
        )
    )

    return handler


def create_logging_handler(log_format: LogFormat = LogFormat.color,
                           date_format=None):

    if log_format == LogFormat.stream:
        handler = logging.StreamHandler()
        if date_format and date_format is not Ellipsis:
            formatter = logging.Formatter(
                "%(asctime)s " + DEFAULT_FORMAT, datefmt=date_format
            )
        else:
            formatter = logging.Formatter(DEFAULT_FORMAT)

        handler.setFormatter(formatter)
        return handler
    elif log_format == LogFormat.json:
        return json_formatter(date_format=date_format)
    elif log_format == LogFormat.color:
        return color_formatter(date_format=date_format)
    elif log_format == LogFormat.syslog:
        if date_format:
            sys.stderr.write("Can not apply \"date_format\" for syslog\n")
            sys.stderr.flush()

        formatter = logging.Formatter("%(message)s")

        if os.path.exists('/dev/log'):
            handler = logging.handlers.SysLogHandler(address='/dev/log')
        else:
            handler = logging.handlers.SysLogHandler()

        handler.setFormatter(formatter)
        return handler

    raise NotImplementedError


def wrap_logging_handler(handler: logging.Handler, buffer_size: int = 1024,
                         logger_class=MemoryHandler,
                         flush_level=logging.ERROR) -> logging.Handler:

    buffered_handler = logger_class(buffer_size, target=handler,
                                    flushLevel=flush_level)

    return buffered_handler


def basic_config(level: int = logging.INFO,
                 log_format: Union[str, LogFormat] = LogFormat.color,
                 buffered=False, buffer_size: int = 1024,
                 flush_level=logging.ERROR, date_format=...):

    if isinstance(level, str):
        level = getattr(logging, level.upper())

    logging.basicConfig()
    logger = logging.getLogger()
    logger.handlers.clear()

    if isinstance(log_format, str):
        log_format = LogFormat[log_format]

    if date_format is True:
        date_format = DateFormat[log_format.name].value

    handler = create_logging_handler(log_format, date_format=date_format)

    if buffered:
        handler = wrap_logging_handler(
            handler,
            buffer_size=buffer_size,
            flush_level=flush_level,
        )

    logging.basicConfig(
        level=level,
        handlers=[handler]
    )
