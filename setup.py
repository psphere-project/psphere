#!/usr/bin/env python

import os
import os.path
import subprocess
import time

from setuptools import setup
from setuptools.command.sdist import sdist as _sdist

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

VERSION = '0.5.2'
RELEASE = '1'

class sdist(_sdist):
    """ custom sdist command, to prep python-psphere.spec file """

    def run(self):
        global VERSION
        global RELEASE

        # Create a development release string for later use
        git_head = subprocess.Popen("git log -1 --pretty=format:%h",
                                    shell=True,
                                    stdout=subprocess.PIPE).communicate()[0].strip()
        date = time.strftime("%Y%m%d%H%M%S", time.gmtime())
        git_release = "%sgit%s" % (date, git_head)

        # Expand macros in python-psphere.spec.in
        spec_in = open('python-psphere.spec.in', 'r')
        spec = open('python-psphere.spec', 'w')
        for line in spec_in.xreadlines():
            if "@VERSION@" in line:
                line = line.replace("@VERSION@", VERSION)
            elif "@RELEASE@" in line:
                # If development release, include date+githash in %{release}
                if RELEASE.startswith('0'):
                    RELEASE += '.' + git_release
                line = line.replace("@RELEASE@", RELEASE)
            spec.write(line)
        spec_in.close()
        spec.close()

        # Run parent constructor
        _sdist.run(self)

setup(name="python-psphere",
      version=VERSION,
      description="vSphere SDK for Python",
      long_description=read("README.rst"),
      author="Jonathan Kinred",
      author_email="jonathan.kinred@gmail.com",
      url="https://github.com/jkinred/psphere",
      packages=["psphere"],
      package_data={"psphere": ["wsdl/*"]},
      install_requires=["suds", "PyYAML"],
      keywords=["vsphere", "vmware"],
      classifiers=["Development Status :: 4 - Beta",
                   "License :: OSI Approved :: Apache Software License"],
      cmdclass = {'sdist': sdist}
     )

