
from datetime import datetime, timedelta
import os
import pickle
import sys

from paste.deploy.loadwsgi import ConfigLoader, APP
from paste.script.command import Command
import sqlalchemy as sa

__all__ = ['get_sessions', 'show_sessions', 'cleanup_sessions',
    'ShowSessionsCommand', 'CleanupSessionsCommand']


def get_sessions(sessions_table, timeout=None):
    sdata = []

    st = sessions_table
    active_sessions = st.select(order_by=st.c.accessed)
    if timeout is not None:
        active_sessions.append_whereclause(
            st.c.accessed >= datetime.now() - timedelta(seconds=timeout))
    for s in active_sessions.execute():
        ses = pickle.loads(s.data).get('session', {})
        if not ses:
            continue
        for key, value in ses.iteritems():
            if key in ('_accessed_time', '_creation_time'):
                value = datetime.fromtimestamp(value)
            else:
                value = unicode(value)
            ses[key] = value
        sdata.append(ses)

    return sdata


def show_sessions(*args, **kargs):
    sdata = get_sessions(*args, **kargs)
    if not sdata:
        return 'No sessions found'

    output = []
    columns = {}

    for d in sdata:
        for key, value in d.iteritems():
            if isinstance(value, datetime):
                value = d[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            column = columns.get(key)
            if column is None:
                column = columns[key] = dict(title=key, width=len(key))
            if column['width'] < len(value):
                column['width'] = len(value)

    keys = sorted(columns.keys())

    header = []
    for key in keys:
        fmt = '%%%is' % columns[key]['width']
        header.append(fmt % key)
    header = ' | '.join(header)
    dashes = '-' * len(header)
    output.append(dashes)
    output.append(header)
    output.append(dashes)

    for d in sdata:
        row = []
        for key in keys:
            fmt = '%%%is' % columns[key]['width']
            value = d.get(key)
            row.append(fmt % value)
        output.append(' | '.join(row))

    output.append(dashes)

    return '\n'.join(output)


def cleanup_sessions(sessions_table, timeout):
    st = sessions_table
    age = datetime.now() - timedelta(seconds=timeout)
    st.delete(st.c.accessed < age).execute()


class _SessionsCommand(Command):
    group_name = 'beaker'

    def get_conf(self, loader):
        # Taken from paste.deploy.loadwsgi.ConfigLoader.get_context
        section = loader.find_config_section(APP)
        global_conf = {}
        defaults = loader.parser.defaults()
        global_conf.update(defaults)
        local_conf = {}
        global_additions = {}
        get_from_globals = {}
        for option in loader.parser.options(section):
            if option.startswith('set '):
                name = option[4:].strip()
                global_additions[name] = global_conf[name] = (
                    loader.parser.get(section, option))
            elif option.startswith('get '):
                name = option[4:].strip()
                get_from_globals[name] = loader.parser.get(section, option)
            else:
                if option in defaults:
                    # @@: It's a global option (?), so skip it
                    continue
                local_conf[option] = loader.parser.get(section, option)
        for local_var, glob_var in get_from_globals.items():
            local_conf[local_var] = global_conf[glob_var]
        return global_conf, local_conf

    def parse_config(self, accept_zero_timeout=False):
        loader = ConfigLoader(self.args[0])
        g_conf, l_conf = self.get_conf(loader)

        dburi_name = '%s.url' % self.options.prefix
        dburi = g_conf.get(dburi_name, l_conf.get(dburi_name))

        timeout = self.options.timeout
        if timeout is None:
            timeout_name = '%s.timeout' % self.options.prefix
            timeout = g_conf.get(timeout_name, l_conf.get(timeout_name))
            self.timeout = int(timeout)
        elif accept_zero_timeout and timeout == '0':
            self.timeout = None
        else:
            measure = timeout[-1]
            self.timeout = int(timeout[:-1])
            if measure.endswith('s'):
                # Seconds
                pass
            elif measure.endswith('m'):
                # Minutes
                self.timeout *= 60
            elif measure.endswith('h'):
                # Hours
                self.timeout *= 60 * 60
            elif measure.endswith('d'):
                # Days
                self.timeout *= 24 * 60 * 60
            else:
                print('Timeout must be seconds, minutes, hours or days. E.g. ' \
                    '20s, 1m, 4h, 1d')
                sys.exit(1)

        table_name = '%s.table_name' % self.options.prefix
        table_name = g_conf.get(table_name, l_conf.get(table_name))
        if not table_name:
            table_name = 'beaker_cache'

        md = sa.MetaData(dburi)
        self.session_table = sa.Table(table_name, md, autoload=True)


class ShowSessionsCommand(_SessionsCommand):
    min_args = max_args = 1

    usage = 'project.ini'
    summary = '''Show beaker sessions stored in database'''

    parser = Command.standard_parser(verbose=True)
    parser.add_option('-p', '--prefix', dest='prefix', default='beaker.session',
        help='Prefix for beaker session parameters in the config file')
    parser.add_option('-t', '--timeout', dest='timeout',
        help='Show sessions newer than timeout. Default - <prefix>.timeout. ' \
            '0 - show all sessions regardless of the config')
    
    def command(self):
        r"""Run the show sessions action.
        """
        self.parse_config(accept_zero_timeout=True)
        print(show_sessions(self.session_table, self.timeout))


class CleanupSessionsCommand(_SessionsCommand):
    min_args = max_args = 1

    usage = 'project.ini'
    summary = '''Clean old beaker sessions stored in database'''

    parser = Command.standard_parser(verbose=True)
    parser.add_option('-p', '--prefix', dest='prefix', default='beaker.session',
        help='Prefix for beaker session parameters in the config file')
    parser.add_option('-t', '--timeout', dest='timeout',
        help='Remove sessions older than timeout. Default - <prefix>.timeout.')
    
    def command(self):
        r"""Run the cleanup sessions action.
        """
        self.parse_config()
        cleanup_sessions(self.session_table, self.timeout)

