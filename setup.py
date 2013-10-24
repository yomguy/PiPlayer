#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


CLASSIFIERS = [
    'Programming Language :: Python',
    'Topic :: Multimedia :: Sound/Audio',
    'Topic :: Multimedia :: Sound/Audio :: Players',
    ]

KEYWORDS = 'audio video media player raspberry pi'

setup(
  name = "PiPlayer",
  url='https://github.com/yomguy/PiPlayer',
  description = "a gstreamer based media sample player for the Raspberry Pi trigerred by GPIO or OSC callbacks",
  long_description = open('README.md').read(),
  author = "Guillaume Pellerin",
  author_email = "yomguy@parisson.com",
  version = '0.3',
  install_requires = [
        'setuptools',
        'pyliblo',
        'RPi.GPIO',
        ],
  platforms=['OS Independent'],
  license='Gnu Public License V2',
  classifiers = CLASSIFIERS,
  keywords = KEYWORDS,
  packages = find_packages(),
  include_package_data = True,
  zip_safe = False,
  scripts = ['scripts/piplayer'],
)
