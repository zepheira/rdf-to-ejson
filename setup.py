#!/usr/bin/env python

import sys
import os
from setuptools import setup

_top_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_top_dir, "lib"))
import rdf_to_ejson
del sys.path[0]
README = open(os.path.join(_top_dir, 'README.md')).read()

setup(name='rdf_to_ejson',
    version=rdf_to_ejson.__version__ or None,
    description="Convert RDF into Exhibit JSON",
    long_description=README,
    classifiers=[c.strip() for c in """
        Development Status :: 1 - Planning
        Intended Audience :: Developers
        License :: OSI Approved :: Apache License
        Operating System :: OS Independent
        Programming Language :: Python :: 2
        Programming Language :: Python :: 2.4
        Programming Language :: Python :: 2.5
        Programming Language :: Python :: 2.6
        Programming Language :: Python :: 2.7
        Topic :: Software Development :: Libraries :: Python Modules
        """.split('\n') if c.strip()],
    keywords='rdf json exhibit',
    author='Mark Baker',
    author_email='mark@zepheira.com',
    maintainer='Mark Baker',
    maintainer_email='mark@zepheira.com',
    url='http://github.com/zepheira/rdf-to-ejson',
    license='Apache',
    py_modules=["rdf_to_ejson"],
    package_dir={"": "lib"},
)
