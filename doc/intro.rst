Introduction
============

This is the documentation for pSphere, native Python bindings for the
vSphere Web Services SDK and VMware Infrastructure SDK.

Installing pSphere
------------------

This document describes how to install pSphere. There is no release yet, so at
the moment you have to clone the hg repository and should be able to run::
    ./setup.py install


Prerequisites
-------------

All development is done against VMware ESX Server 3.5 which is VI SDK 2.5. I
have not tested it against ESXi, vSphere 4, etc. although I fully intend to.

The suds_ library is used for SOAP communication and at least version 0.4 is required.

pSphere is developed with **Python 2.6**. My intention is to ensure
pSphere is compatible with **Python 2.4** so that it can run on CentOS/RHEL 5.

.. _suds: http://fedorahosted.org/suds/


Usage
-----

See :doc:`tutorial` for an introduction.  It also contains links to more
advanced sections in this manual for the topics it discusses.


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
