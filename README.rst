FriendlyCaptcha CfP step
==========================

.. image:: https://raw.githubusercontent.com/pretalx/pretalx-friendlycaptcha/python-coverage-comment-action-data/badge.svg
   :target: https://htmlpreview.github.io/?https://github.com/pretalx/pretalx-friendlycaptcha/blob/python-coverage-comment-action-data/htmlcov/index.html
   :alt: Coverage

This is a plugin for `pretalx`_.
It adds a new, final CfP step with the FriendlyCaptcha captcha, in order to reduce spam, using
FriendlyCaptcha v0.9.17.

You need a FriendlyCaptcha account and subscription to use this plugin.

Development setup
-----------------

1. Make sure that you have a working `pretalx development setup`_.

2. Clone this repository, eg to ``local/pretalx-friendlycaptcha``.

3. Install the plugin and its development dependencies with ``uv pip install -e '.[dev]'``.

4. Restart your local pretalx server. This plugin should show up in the plugin list shown on startup in the console.
   You can now use the plugin from this repository for your events by enabling it in the 'plugins' tab in the settings.

Code style
----------

This plugin uses ruff for linting and formatting. To check and fix code style::

    just fmt

Testing
-------

To run the test suite::

    just test


License
-------

Copyright 2024 Tobias Kunze

Released under the terms of the Apache License 2.0


.. _pretalx: https://github.com/pretalx/pretalx
.. _pretalx development setup: https://docs.pretalx.org/en/latest/developer/setup.html
