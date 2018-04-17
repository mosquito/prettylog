prettylog
=========

Let's write beautiful logs:

.. code-block:: python

    import logging
    from prettylog import basic_config


    # Configure logging
    basic_config(level=logging.INFO, buffered=False, log_format='color')


Available formats
-----------------

* stream - default behaviour
* color - colored logs
* json - json representation
* syslog - writes to syslog

Quick start
-----------

Setting up json logs:

.. code-block:: python

    import logging
    from prettylog import basic_config


    # Configure logging
    basic_config(level=logging.INFO, buffered=False, log_format='json')


Buffered log handler
++++++++++++++++++++

Parameter `buffered=True` enables memory buffer which flushing logs delayed.

.. code-block:: python

    import logging
    from prettylog import basic_config

    basic_config(
        level=logging.INFO,
        buffered=True,
        buffer_size=10,             # flush each 10 log records
        flush_level=loggging.ERROR, # or when record with this level will be sent
        log_format='color',
    )
