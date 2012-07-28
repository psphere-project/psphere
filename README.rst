Introduction
============

psphere is a Python interface for the `VMware vSphere Web Services SDK`_, a 
powerful API for programatically managing your VMware infrastructure:

* Provision, clone and snapshot virtual machines
* Query and configure clusters, host systems and datastores
* Programatically configure ESXi hosts (i.e. for automation)

psphere can be used to create standalone Python scripts or used as a library
in larger Python applications (e.g. Django).

Usage
=====

    >>> from psphere.client import Client
    >>> client = Client("your.esxserver.com", "Administrator", "strongpass")
    >>> servertime = client.si.CurrentTime()
    >>> print(servertime)
    2010-09-04 18:35:12.062575
    >>> client.logout()

Installation
============

The latest stable version of psphere can be installed from PyPi:

# pip install -U psphere


Community
=========

Discussion and support can be found on the `psphere Google Group`_.

.. _psphere Google Group: https://groups.google.com/group/psphere

.. _VMware vSphere Web Services SDK: http://pubs.vmware.com/vsphere-50/index.jsp?topic=/com.vmware.wssdk.apiref.doc_50/right-pane.html
