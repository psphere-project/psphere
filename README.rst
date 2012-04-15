Introduction
============

psphere is a Python interface for the `VMware vSphere Web Services SDK`_, a 
powerful API for programatically managing your VMware infrastructure.

psphere allows the creation of standalone Python scripts as well as integration
into larger Python applications (e.g. Django) to perform any operation in
your virtual infrastructure:

* Provision, clone and snapshot virtual machines
* Query and configure clusters, host systems and datastores
* Programatically configure ESXi hosts (i.e. for automation)

Usage
=====

    >>> from psphere.client import Client
    >>> client = Client("your.esxserver.com", "Administrator", "strongpass")
    >>> servertime = client.si.CurrentTime()
    >>> print(servertime)
    2010-09-04 18:35:12.062575
    >>> client.logout()

The aim of psphere is to implement a Pythonic API covering the entire
`VMware vSphere Web Services SDK`_. While many operations using the SDK are
straight-forward, there is definitely scope to provide convenient access to
common operations on virtual machines and other managed objects. This
convenient access is within the realm of higher level library written on top
of psphere. A project of this nature has always been my intention and remains
high on my wish/TODO list!

Installation
============

psphere is best installed using the official package:

# pip install -U psphere

This will fetch the latest stable release of psphere and it's dependencies
from PyPI.

.. _VMware vSphere Web Services SDK: http://pubs.vmware.com/vsphere-50/index.jsp?topic=/com.vmware.wssdk.apiref.doc_50/right-pane.html
