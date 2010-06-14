from datetime import datetime, timedelta
import os
import pickle
from subprocess import Popen, PIPE
import sys
import time

from beaker.ext.database import DatabaseNamespaceManager
from beakerhelpers.sessions import (get_sessions, show_sessions,
    ShowSessionsCommand, CleanupSessionsCommand)
from paste.script.command import run
import sqlalchemy as sa

testdb = os.path.join(os.path.dirname(__file__), 'test.db')
cfg_file = os.path.join(os.path.dirname(__file__), 'testapp.cfg')

__all__ = ['setup', 'teardown', 'test_get_show_sessions']

def setup():
    """Use Beaker manager to create the session table"""
    dnm = DatabaseNamespaceManager('abc', url='sqlite:///%s' % testdb,
        lock_dir=os.getcwd())


def teardown():
    os.remove(testdb)


def test_get_show_sessions():
    r"""Test the show sessions functionality.

    Show Sessions takes a config file as a parameter, loads Beaker configuration
    and outputs contents of the database sessions.

    Load the table

        >>> engine = sa.create_engine('sqlite:///%s' % testdb)
        >>> md = sa.MetaData(bind=engine)
        >>> ses_table = sa.Table('beaker_cache', md, autoload=True)

    At first we have no sessions

        >>> get_sessions(ses_table)
        []
        >>> print(show_sessions(ses_table))
        No sessions found

    Let's create a sample session

        >>> psnow = time.mktime(datetime.now().timetuple()) # POSIX timestamp
        >>> now = datetime.fromtimestamp(psnow)
        >>> sdata = dict(
        ...     session=dict(_accessed_time=psnow, _creation_time=psnow,
        ...         user_name='john@doe.com'))
        >>> rp = ses_table.insert().values(namespace='abc', accessed=now,
        ...     created=now, data=pickle.dumps(sdata)).execute()

    And check that we get it back

        >>> sessions = get_sessions(ses_table)
        >>> len(sessions)
        1
        >>> assert sessions[0]['_accessed_time'] == now
        >>> assert sessions[0]['_creation_time'] == now
        >>> print(sessions[0]['user_name'])
        john@doe.com

    Check the pretty printed sessions

        >>> ppsessions = show_sessions(ses_table)
        >>> fmtnow = now.strftime('%Y-%m-%d %H:%M:%S')
        >>> ppsessions = ppsessions.replace(fmtnow, '       CURRENT TIME')
        >>> print(ppsessions)
        --------------------------------------------------------
             _accessed_time |      _creation_time |    user_name
        --------------------------------------------------------
               CURRENT TIME |        CURRENT TIME | john@doe.com
        --------------------------------------------------------
         
    Make the sessions 1 minute old now

        >>> rp = ses_table.update().values(
        ...     accessed=now - timedelta(seconds=60)).execute()

        >>> len(get_sessions(ses_table))
        1

    But if we set a timeout we should get no active sessions

        >>> get_sessions(ses_table, timeout=60)
        []

    Clean up

        >>> rp = ses_table.delete().execute()

    """


def test_showsessions_command():
    r"""Test the Show Sessions command.

    Load the sessions table

        >>> engine = sa.create_engine('sqlite:///%s' % testdb)
        >>> md = sa.MetaData(bind=engine)
        >>> ses_table = sa.Table('beaker_cache', md, autoload=True)

        >>> cmd = ShowSessionsCommand('beakersessions')

    At first we have no sessions

        >>> cmd.run([cfg_file])
        No sessions found
        0

    Create a sample session

        >>> psnow = time.mktime(datetime.now().timetuple()) # POSIX timestamp
        >>> now = datetime.fromtimestamp(psnow)
        >>> sdata = dict(
        ...     session=dict(user_name='john@doe.com', account='public'))
        >>> rp = ses_table.insert().values(namespace='abc', accessed=now,
        ...     created=now, data=pickle.dumps(sdata)).execute()

    Now call the show_sessions using PasteCall

        >>> cmd.run([cfg_file])
        ----------------------
        account |    user_name
        ----------------------
         public | john@doe.com
        ----------------------
        0

    Make the session 15 seconds old now

        >>> rp = ses_table.update().values(
        ...     accessed=now - timedelta(seconds=15)).execute()

        >>> cmd.run([cfg_file])
        ----------------------
        account |    user_name
        ----------------------
         public | john@doe.com
        ----------------------
        0

    Ask for a shorter timeout (under different session prefix)

        >>> cmd.run([cfg_file, '--prefix', 'bkr.session'])
        No sessions found
        0

    Set a custom timeout now

        >>> cmd.run([cfg_file, '--prefix', 'bkr.session', '--timeout', '15m'])
        ----------------------
        account |    user_name
        ----------------------
         public | john@doe.com
        ----------------------
        0

    Make the session even older now

        >>> rp = ses_table.update().values(
        ...     accessed=now - timedelta(days=3)).execute()

    Check again with the custom timeout (2 days)

        >>> cmd.run([cfg_file, '--prefix', 'bkr.session', '--timeout', '2d'])
        No sessions found
        0

    Special case - ignore the timeout altogether

        >>> cmd.run([cfg_file, '--prefix', 'bkr.session', '--timeout', '0'])
        ----------------------
        account |    user_name
        ----------------------
         public | john@doe.com
        ----------------------
        0

    Test wrong timeout parameter

        >>> cmd.run([cfg_file, '--timeout', '10'])
        Traceback (most recent call last):
        ...
        SystemExit: 1

    Clean up

        >>> rp = ses_table.delete().execute()
    """


def test_session_cleanup():
    r"""Test session cleanup.

    Load the table

        >>> engine = sa.create_engine('sqlite:///%s' % testdb)
        >>> md = sa.MetaData(bind=engine)
        >>> ses_table = sa.Table('beaker_cache', md, autoload=True)

        >>> cmd = CleanupSessionsCommand('beakersessions')

    Insert several sessions into it. The first one was accessed 5 seconds ago

        >>> now = datetime.now()
        >>> r = ses_table.insert().values(namespace='abc', created=now, data='',
        ...     accessed=now - timedelta(seconds=5)).execute()

    Another was accessed 70 minutes ago

        >>> r = ses_table.insert().values(namespace='bcd', created=now, data='',
        ...     accessed=now - timedelta(minutes=70)).execute()

    Then 3 hours ago

        >>> r = ses_table.insert().values(namespace='cde', created=now, data='',
        ...     accessed=now - timedelta(hours=3)).execute()

    And 1 day 15 minutes ago

        >>> r = ses_table.insert().values(namespace='def', created=now, data='',
        ...     accessed=now - timedelta(days=1, minutes=15)).execute()

    Now call the cleanup and ask it to clean the sessions older than 1 day

        >>> cmd.run([cfg_file, '--timeout', '1d'])
        0

    We should only have the sessions newer than 1 day left in the db

        >>> for c in ses_table.select(order_by='namespace').execute():
        ...     print c.namespace
        abc
        bcd
        cde

    Now cleanup the sessions older than 2 hours and check

        >>> cmd.run([cfg_file, '--timeout', '2h'])
        0
        >>> for c in ses_table.select(order_by='namespace').execute():
        ...     print c.namespace
        abc
        bcd

    Now cleanup the sessions older than 10 seconds (according to the config) and
    check

        >>> cmd.run([cfg_file, '--prefix', 'bkr.session'])
        0
        >>> for c in ses_table.select(order_by='namespace').execute():
        ...     print c.namespace
        abc

    """

