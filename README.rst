SmartInspect Python Library
===========================

.. image:: https://code-partners.com/wp-content/uploads/2020/11/smartinspect_logo_red_82x82_optim.png
    :target: https://code-partners.com/offerings/smartinspect/
    :alt: SmartInspect


``smartinspect-py`` is a client library to integrate SmartInspect logging into Python applications.
It also has a SmartInspect Handler which can be used to dispatch Python ``logging`` log records to
the destination defined by SmartInspect.

SmartInspect is an advanced logging tool for debugging and monitoring software applications.
It helps you identify bugs, find solutions to user-reported issues and gives you a precise picture of how
your software performs in different environments. Whether you need logging in the development phase, on production
systems or at customer sites, SmartInspect is the perfect choice.

Visit `SmartInspect website <https://code-partners.com/offerings/smartinspect/>`_.

Installation
============

You can install ``smartinspect-py`` with:

.. code-block:: console

    $ pip install smartinspect-py

Usage
=====

You can start using ``smartinspect-py`` like this:

.. code-block:: pycon

    from smartinspect import SiAuto

    # Enable SiAuto and it will be automatically ready to log via
    # named pipe on Windows or tcp on Linux/MacOs
    SiAuto.si.set_enabled(True)
    # Log simple messages, warnings and exceptions
    SiAuto.main.log_message("Processing Order 48843")
    SiAuto.main.log_warning("Connection refused")
    SiAuto.main.log_exception(e)

    # Log variable values, SQL cursor data or any other object
    SiAuto.main.log_int("index", index)
    SiAuto.main.log_object_value("order", order)
    SiAuto.main.log_cursor_data("Cursor data", cursor)
    SiAuto.si.dispose()

More Python examples available at `Code-Partners Github repository <https://github.com/Code-Partners/smartinspect-examples/tree/main/python>`_.
