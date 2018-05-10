import logging
import logging.handlers
import os
import sys
import traceback
import fast_json
from logging.handlers import MemoryHandler
from enum import IntEnum
from types import MappingProxyType
from typing import Union

from colorlog import ColoredFormatter


class LogFormat(IntEnum):
    stream = 0
    color = 1
    json = 2
    syslog = 3

    @classmethod
    def choices(cls):
        return tuple(cls._member_names_)


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

    def format(self, record):
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
            'level': self.LEVELS[record.levelno]
        }

        if record.exc_info:
            payload['stackTrace'] = "\n".join(
                traceback.format_exception(*record.exc_info)
            )

        return fast_json.dumps(payload, ensure_ascii=False)


def json_formatter(stream=None):
    stream = stream or sys.stdout
    formatter = JSONLogFormatter()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)
    return handler


def color_formatter(stream=None):
    stream = stream or sys.stderr
    handler = logging.StreamHandler(stream)
    handler.setFormatter(ColoredFormatter(
        "%(blue)s[T:%(threadName)s]%(reset)s "
        "%(log_color)s%(levelname)s:%(name)s%(reset)s: "
        "%(message_log_color)s%(message)s",
        datefmt=None,
        reset=True,
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
        style='%'
    ))

    return handler


def create_logging_handler(log_format: LogFormat=LogFormat.color):
    if log_format == LogFormat.stream:
        return logging.StreamHandler()
    elif log_format == LogFormat.json:
        return json_formatter()
    elif log_format == LogFormat.color:
        return color_formatter()
    elif log_format == LogFormat.syslog:
        if os.path.exists('/dev/log'):
            return logging.handlers.SysLogHandler(address='/dev/log')
        return logging.handlers.SysLogHandler()

    raise NotImplementedError


def wrap_logging_handler(handler: logging.Handler, buffer_size: int = 1024,
                         logger_class=MemoryHandler,
                         flush_level=logging.ERROR) -> logging.Handler:

    buffered_handler = logger_class(buffer_size, target=handler,
                                    flushLevel=flush_level)

    return buffered_handler


def basic_config(level: int=logging.INFO,
                 log_format: Union[str, LogFormat]=LogFormat.color,
                 buffered=False, buffer_size: int=1024,
                 flush_level=logging.ERROR):

    if isinstance(level, str):
        level = getattr(logging, level.upper())

    logging.basicConfig()
    logger = logging.getLogger()
    logger.handlers.clear()

    if isinstance(log_format, str):
        log_format = LogFormat[log_format]

    handler = create_logging_handler(log_format)

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
