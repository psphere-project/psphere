Introduction
============

This is the documentation for pSphere, native Python bindings for the
vSphere Web Services SDK/VMware Infrastructure SDK.

Notes
-----

pSphere implements vSphere SDK 4.1, but my primary development environment is
VMware ESX Server 3.5 which is VI SDK 2.5.


Prerequisites
-------------

pSphere is developed with **Python 2.6**.

The suds SOAP library is used for comms with the vSphere server. The 0.4 beta
is required which isn't in PyPI at time of writing. You can download and
install it yourself from the `the suds website`_::

    $ wget https://fedorahosted.org/releases/s/u/suds/python-suds-0.4.tar.gz
    $ tar -zxf python-suds-0.4.tar.gz
    $ cd python-suds-0.4
    $ sudo python setup.py install

.. _the suds website: https://fedorahosted.org/suds/#Resources


Installing pSphere
------------------

Until I release to PyPI, you have to clone the hg repository and install it
manually (**make sure you read the notes above on suds 0.4**)::

    $ hg clone https://jkinred@bitbucket.org/jkinred/psphere
    $ cd psphere
    $ sudo python setup.py install
    $ ./examples/connect.py --url https://yourserver/sdk --username youruser --password yourpass
    Successfully connected to https://yourserver/sdk
    Server time is 2010-09-05 00:14:06.037575



Usage
-----

See :doc:`tutorial` for an introductory tutorial. It also contains links
to more advanced sections in this manual.


Examples
--------

* :doc:`hostsystem`
* :doc:`datastore`


Alternatives
------------

- `VMware VI Java API`_
- `VMware VI Java API with Jython`_
- `VMware vSphere SDK for Perl`_
- `VMware vSphere PowerCLI`_

.. _VMware VI Java API: http://vijava.sourceforge.net/
.. _VMware VI Java API with Jython: http://www.doublecloud.org/2010/03/using-vsphere-java-api-in-jython-and-other-jvm-languages/
.. _VMware vSphere SDK for Perl: http://www.vmware.com/support/developer/viperltoolkit/
.. _VMware vSphere PowerCLI: http://www.vmware.com/support/pubs/ps_pubs.html
