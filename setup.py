# -*- coding: utf-8 -*-

from setuptools import setup
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

__version__ = None
with open(path.join(here, 'lawfactory_utils', '__version.py')) as __version:
    exec(__version.read())
assert __version__ is not None

with open(path.join(here, 'README.md')) as readme:
    LONG_DESC = readme.read()

setup(
    name='lawfactory_utils',
    version=__version__,

    description='Python utils for The Law Factory parsers',
    long_description=LONG_DESC,
    license="GPLv3+",

    url='https://github.com/regardscitoyens/lawfactory_utils',
    author='Regards Citoyens',
    author_email='contact@regardscitoyens.org',

    package_data={'': ['_redirects_cache.json']},
    include_package_data=True,

    classifiers=[
        'Development Status :: 1 - Planning',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
    ],

    keywords='scraping politics data',

    packages=['lawfactory_utils'],

)
