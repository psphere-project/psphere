Sunset Notice
=============

We strongly recommend that you start your VMware Python journey with the official `VMware pyvmomi`_ library.

psphere was created when no other client was available. It was a privilege to create something that was useful to others.

*"Death is only the end if you assume the story is about you."*
*― The Nightvale Podcast*

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

.. _VMware pyvmomi: https://pypi.org/project/pyvmomi/
.. _psphere Google Group: https://groups.google.com/group/psphere

.. _VMware vSphere Web Services SDK: http://pubs.vmware.com/vsphere-50/index.jsp?topic=/com.vmware.wssdk.apiref.doc_50/right-pane.html


Releasing
---------

To perform a release, you will need to be an admin for the project on
GitHub and on PyPI. Contact the maintainers if you need that access.

You will need to have a `~/.pypirc` with your PyPI credentials and
also the following settings::

    [zest.releaser]
    create-wheels = yes

To perform a release, run the following::

    python3.7 -m venv ~/.virtualenvs/dist
    workon dist
    pip install -U pip setuptools wheel
    pip install -U tox zest.releaser
    fullrelease  # follow prompts, use semver ish with versions.

The releaser will handle updating version data on the package and in
CHANGES.rst along with tagging the repo and uploading to PyPI.
