# -*- coding: UTF-8 -*-

from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='BeakerHelpers',
      version=version,
      description="An extendable Beaker helpers package to manage Beaker sessions",
      long_description=open('README.txt').read(),
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='paste beaker session database active',
      author=u'Linas Juškevičius'.encode('utf-8'),
      author_email='linas@idiles.com',
      url='',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'tests', 'tests.testapp']),
      include_package_data=True,
      namespace_packages=['beakerhelpers'],
      zip_safe=False,
      tests_require=['Nose>=0.11',],
      test_suite='nose.collector',
      install_requires=[
          'PasteScript',
          'PasteDeploy',
          'SQLAlchemy',
      ],
      entry_points="""
      [paste.global_paster_command]
      beakersessions = beakerhelpers.sessions:ShowSessionsCommand
      beakercleanup = beakerhelpers.sessions:CleanupSessionsCommand
      """,
      )
