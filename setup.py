# -*- coding: UTF-8 -*-

from setuptools import setup, find_packages
from os.path import join, dirname
import sys
# Fool distutils to accept more than ASCII
reload(sys).setdefaultencoding('utf-8')

version = '0.1'

setup(name='BeakerHelpers',
    version=version,
    description="An extendable Beaker helpers package to manage Beaker sessions",
    long_description=open(join(dirname(__file__), 'README.rst')).read(),
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='paste beaker session database active',
    author=u'Linas Juškevičius',
    author_email='linas.juskevicius@gmail.com',
    url='',
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'tests']),
    include_package_data=True,
    namespace_packages=['beakerhelpers'],
    zip_safe=False,
    tests_require=['Nose>=0.11',],
    test_suite='nose.collector',
    install_requires=[
        'PasteScript',
        'PasteDeploy',
        'SQLAlchemy>=0.5.5',
    ],
    entry_points="""
    [paste.global_paster_command]
    beakersessions = beakerhelpers.sessions:ShowSessionsCommand
    beakercleanup = beakerhelpers.sessions:CleanupSessionsCommand
    """,
)
