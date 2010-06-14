BeakerHelpers
=============

BeakerHelpers is a Beaker_ extension that can show the active sessions and clean
the old ones. Currently it only works with beaker.ext.database storage backend.

BeakerHelpers is also a namespace package so new plugins can be created under
this namespace_.

You can find the Git repository at github.com_

Installation
------------

easy_install_::

    $ <env>/bin/easy_install BeakerHelpers

pip_::

    $ <env>/bin/pip install BeakerHelpers

Get / Show Sessions Usage
-------------------------

You can call ``get_sessions`` to get a list of active sessions (dicts)::

    >>> import sqlalchemy
    >>> from beakerhelpers.sessions import get_sessions
    >>> sessions_table = sqlalchemy.Table('beaker_cache',
    ...     sqlalchemy.MetaData('sqlite:///my.db'), autoload=True)
    >>> get_sessions(sessions_table, timeout=3600)  # timeout in seconds
    [{
        '_accessed_time': datetime.datetime(2010, 1, 1, 10, 10, 10),
        '_creation_time': datetime.datetime(2010, 1, 1, 08, 40, 00),
        'user_name': u'john@doe.com',
    }]

The above form is suitable for Python access. If you want to provide this data
to the user you could use ``show_sessions`` with the same parameters instead::

    >>> print show_sessions(sessions_table, timeout=3600)
    --------------------------------------------------------
         _accessed_time |      _creation_time |    user_name
    --------------------------------------------------------
    2010-01-01 10:10:10 | 2010-01-01 08:40:00 | john@doe.com

However you can use ``paster beakersessions`` to call the ``show_sessions`` from
the console::

    $ <env>/bin/paster beakersessions cfg/prod.ini
    --------------------------------------------------------
         _accessed_time |      _creation_time |    user_name
    --------------------------------------------------------
    2010-01-01 10:10:10 | 2010-01-01 08:40:00 | john@doe.com

In this case the `cfg/prod.ini` file should be a `paste.deploy` loadable
configuration file. BeakerHelpers expects to find these keys in the `[app:main]`
section of `cfg/prod.ini`:

    - ``beaker.session.type`` = `ext:database` - the only supported backend (yet)
    - ``beaker.session.url`` - an `SQLAlchemy engine URL`_
    - ``beaker.session.timeout`` - session timeout in seconds
    - ``beaker.session.table_name`` - (optional) session storage table.
      According to beaker.ext.database_, defaults to `beaker_cache`.

``paster beakersessions`` command also takes two optional arguments:

    - ``--prefix, -p`` - beaker key prefix in the config file, defaults to
      `beaker.session`
    - ``--timeout, -t`` - do not show sessions older than the timeout. Timeout
      examples:

      - `3s` - 3 seconds
      - `14m` - 14 minutes
      - `36h` - 36 hours
      - `2d` - 2 days
      - `0` - show all sessions (ignore timeout even in the config file)

      If not provided the timeout will be taken from the config file,
      `<prefix>.timeout` (seconds).

Session Cleanup Usage
---------------------

You can use ``cleanup_sessions`` from your Python scripts to remove old
sessions::

    >>> import sqlalchemy
    >>> from beakerhelpers.sessions import cleanup_sessions
    >>> sessions_table = sqlalchemy.Table('beaker_cache',
    ...     sqlalchemy.MetaData('sqlite:///my.db'), autoload=True)
    >>> cleanup_sessions(sessions_table, timeout=3600)  # timeout in seconds

The sessions older than 1 hour would get cleaned. However, session cleanup is
particularly convenient to be called as a paste script::

    $ <env>/bin/paster beakercleanup cfg/prod.ini

It expects the same config file structure and takes the same optional arguments
as beakersessions. However, in this case sessions *older* than ``--timeout``
will be removed.

Attention - BeakerShowSessions and BeakerCleanup users
------------------------------------------------------

Due to namespace issues BeakerShowSessions and BeakerCleanup can not be
installed with pip and/or easy_install. Their functionality got merged into this
package and access became simpler. We strongly encourage to use BeakerHelpers
instead.

.. _Beaker: http://beaker.groovie.org
.. _beaker.ext.database: http://www.bitbucket.org/bbangert/beaker/src/554a46f4a946/beaker/ext/database.py#cl-35 
.. _SQLAlchemy engine URL: http://www.sqlalchemy.org/docs/05/dbengine.html#create-engine-url-arguments
.. _github.com: http://github.com/kaukas/BeakerHelpers
.. _namespace: http://peak.telecommunity.com/DevCenter/setuptools#namespace-packages
.. _easy_install: http://peak.telecommunity.com/DevCenter/EasyInstall 
.. _pip: http://pip.openplans.org/ 
