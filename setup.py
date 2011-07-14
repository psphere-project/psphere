#!/usr/bin/env python

import os

from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='psphere',
      version='0.1.3',
      description='vSphere SDK for Python',
      long_description=read('README'),
      author='Jonathan Kinred',
      author_email='jonathan.kinred@gmail.com',
      url='http://bitbucket.org/jkinred/psphere',
      packages=['psphere'],
      install_requires=['suds'],
      keywords=['vsphere', 'vmware'],
      classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: Apache Software License",
      ],
     )
