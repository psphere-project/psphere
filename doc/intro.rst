Introduction
============

This is the documentation for psphere, native Python bindings for the
vSphere Web Services SDK/VMware Infrastructure SDK.

Notes
-----

psphere implements the following VMware SDKs:

    * VMware Infrastructure SDK 2.5
    * VMware vSphere Web Services SDK 4.0 and later

I'm currently developing against vCenter 4.1 so please raise any bugs for
other versions.

See the vSphere Web Services SDK Documentation for further information on 
VMware SDKs at http://www.vmware.com/support/developer/vc-sdk/.

Installing psphere
------------------

    # pip install -U psphere
    
Or if you want to use the latest development branch::

    $ hg clone https://jkinred@bitbucket.org/jkinred/psphere
    $ cd psphere
    $ sudo python setup.py install
    $ ./examples/connect.py --server yourserver.esx.com --username youruser --password yourpass
    Successfully connected to https://yourserver.esx.com/sdk
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
