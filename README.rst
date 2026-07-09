FriendlyCaptcha CfP step
==========================

.. image:: https://img.shields.io/pypi/v/pretalx-friendlycaptcha.svg
   :target: https://pypi.org/project/pretalx-friendlycaptcha/
   :alt: PyPI version

This is a plugin for `pretalx`_.
It adds a new, final CfP step with the FriendlyCaptcha captcha, in order to reduce spam, using
FriendlyCaptcha v0.9.17.

You need a FriendlyCaptcha account and subscription to use this plugin.

Installation
------------

Install the plugin with pip, in the same environment as your pretalx
installation::

    (env)$ python -m pip install pretalx-friendlycaptcha

Afterwards, run ``migrate`` and ``rebuild`` and restart your pretalx services,
just like after any pretalx update (see `performing updates`_ in the
administrator documentation).

You can then enable the plugin under "Settings → Plugins" in your event settings.

Development setup
-----------------

1. Make sure that you have a working `pretalx development setup`_.

2. Clone this repository, eg to ``local/pretalx-friendlycaptcha``.

3. Install the plugin and its development dependencies with ``uv pip install -e '.[dev]'``.

4. Restart your local pretalx server. This plugin should show up in the plugin list shown on startup in the console.
   You can now use the plugin from this repository for your events by enabling it in the 'plugins' tab in the settings.

Development commands
~~~~~~~~~~~~~~~~~~~~

This plugin uses `just`_ as a task runner and `uv`_ for dependency management.
Run ``just`` with no arguments to list every available command. The most useful ones
are:

``just fmt``
    Auto-format and lint the code.

``just test``
    Run the full test suite with pytest.

Installing pretalx
~~~~~~~~~~~~~~~~~~~~

The tests need pretalx installed in the environment. ``just test`` handles this for
you: if pretalx cannot be imported, it installs the latest version from git before
running the test suite.

If you already have a development version of pretalx around (for example if you want
to test your changes against a specific commit or branch of pretalx), you can also
install pretalx up front yourself:

``just install-pretalx-local /path/to/pretalx``
    Install pretalx from a local checkout as an editable install.

``just install-pretalx``
    Install the latest pretalx from git (runs before tests if no pretalx is installed).


License
-------

Copyright 2024 Tobias Kunze

Released under the terms of the Apache License 2.0


.. _pretalx: https://github.com/pretalx/pretalx
.. _pretalx development setup: https://docs.pretalx.org/en/latest/developer/setup.html
.. _just: https://just.systems/
.. _uv: https://docs.astral.sh/uv/
.. _performing updates: https://docs.pretalx.org/administrator/maintenance/#performing-updates
