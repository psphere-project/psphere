#!/usr/bin/env python

from setuptools import setup

setup(name='psphere',
      version='0.1.2',
      description='vSphere SDK for Python',
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
