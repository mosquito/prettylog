import json
import logging
import uuid

import pytest
from prettylog import basic_config, LogFormat, create_logging_handler


logging.basicConfig()


def test_choices():
    choices = LogFormat.choices()
    assert isinstance(choices, tuple)

    for i in ('stream', 'color', 'json', 'syslog'):
        assert i in choices


def test_configure_logging_json(capsys):
    capsys.readouterr()

    data = str(uuid.uuid4())

    basic_config(level='debug', log_format='json', buffered=False)
    logging.info(data)

    stdout, stderr = capsys.readouterr()

    json_result = json.loads(stdout.strip())
    assert json_result['msg'] == data

    logging.basicConfig(handlers=[], level=logging.INFO)


def test_configure_logging_stderr(capsys):
    data = str(uuid.uuid4())

    basic_config(level=logging.DEBUG, log_format='stream', buffered=False)

    logging.info(data)

    stdout, stderr = capsys.readouterr()

    assert data in stderr

    logging.basicConfig(handlers=[])


@pytest.mark.parametrize('fmt', LogFormat.choices())
def test_formats(fmt):
    basic_config(level='debug', log_format=fmt, buffered=False)

    logging.error("test")
    logging.info("foo %r", None)
    logging.debug({"foo": [None, 1]})

    try:
        raise Exception
    except Exception:
        logging.exception("Error")


def test_invalid_handler():
    with pytest.raises(NotImplementedError):
        create_logging_handler('example.com')


def test_buferred(capsys):
    capsys.readouterr()

    data = str(uuid.uuid4())

    basic_config(level='debug', log_format='json',
                 buffered=True, buffer_size=10)

    logging.info("0 %r", data)
    stdout, stderr = capsys.readouterr()
    assert not stdout

    logging.getLogger().handlers[0].flush()

    stdout, stderr = capsys.readouterr()

    assert data in stdout
