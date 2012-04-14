Introduction
============

psphere is a Python interface to the `VMware vSphere Web Services SDK`_.

The `VMware vSphere Web Services SDK`_ provides a powerful API for programatically managing your virtual infrastructure.

Using this module, you can perform all operations in your virtual
infrastructure using Python::
    * Query host systems, datastores and virtual machines
    * Provision, clone and snapshot virtual machines
    * Configure new ESXi hosts
    * Deploy templates


The primary aim of psphere is to provide access to the complete SDK in a Pythonic API. While psphere is capable of performing any SDK function, it is not intended to be a high-level or specialised API. That task is left to higher-level libraries (built on top of psphere) which can abstract operations such us snapshotting a VM. This is certainly on my wishlist of projects.

Installation
============

psphere is best installed using the official package:

# pip install -U psphere

This will fetch psphere and it's dependencies from PyPI.

.. _VMware vSphere Web Services SDK: http://pubs.vmware.com/vsphere-50/index.jsp?topic=/com.vmware.wssdk.apiref.doc_50/right-pane.html
