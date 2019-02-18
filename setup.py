from __future__ import absolute_import, division, print_function

from setuptools import setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read().replace('.. :changelog:', '')

setup(
    name="psphere",
    version='0.6.0a',
    description="vSphere SDK for Python",
    long_description=readme + '\n\n' + history,
    author="Jonathan Kinred",
    author_email="jonathan.kinred@gmail.com",
    maintainer="Thomas Grainger",
    maintainer_email="psphere@graingert.co.uk",
    url="https://github.com/graingert/psphere",
    packages=["psphere"],
    package_data={"psphere": ["wsdl/*"]},
    install_requires=["six", "suds-jurko", "PyYAML"],
    keywords=["vsphere", "vmware"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
    ],
 )
