#!/usr/bin/env python


import os
import os.path
import subprocess
from distutils.core import setup, Extension
from distutils.command.sdist import sdist as _sdist

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

version_file_name = "version.txt"
try:
    if(not os.path.exists(version_file_name)):
        subprocess.call('/usr/bin/git describe --tags | tr - _ > %s' % (version_file_name, ), shell=True)
    version_file = open(version_file_name, "r")
    VERSION = version_file.read()[0:-1]
    version_file.close()
except Exception, e:
    raise RuntimeError("ERROR: version.txt could not be found.  Run 'git describe > version.txt' to get the correct version info.")

print "VERSION is set to %s" % (VERSION)

class sdist(_sdist):
    """ custom sdist command to prepare spec file """

    def run(self):
        cmd = (""" sed -e "s/@VERSION@/%s/g" < python-psphere.spec.in """ %
               VERSION) + " > python-psphere.spec"
        os.system(cmd)

        _sdist.run(self)

setup(name="python-psphere",
      version=VERSION,
      description="vSphere SDK for Python",
      long_description=read("README.rst"),
      author="Jonathan Kinred",
      author_email="jonathan.kinred@gmail.com",
      url="http://bitbucket.org/jkinred/psphere",
      packages=["psphere"],
      package_data={"psphere": ["wsdl/*"]},
      install_requires=["suds", "PyYAML"],
      keywords=["vsphere", "vmware"],
      classifiers=["Development Status :: 4 - Beta",
                   "License :: OSI Approved :: Apache Software License"],
      cmdclass = {'sdist': sdist}
     )
