.. highlight:: python

First steps with psphere
========================

This document is meant to give a tutorial-like overview of the main psphere
objects and the common tasks that psphere is used for.

The green arrows designate "more info" links leading to more detailed
sections about the described task.


Vendor documentation
--------------------

VMware provides very good documentation for the vSphere Web Services SDK. It is
suggested that you at least read the introductory documents to gain a conceptual
understanding of the SDK.

Throughout this documentation there are links to the API reference documentation.

|more| See :ref:`useful references <useful-references>`.


The Vim object
--------------

The Vim object is the entry point into psphere. Through it you can log into a
vSphere server, find managed objects, obtain views of those managed objects
and access information about them.

A brief overview of the most common methods:

* The **find_entity_view** method finds objects in the inventory
* The **get_view** and **get_views** methods create local *views* of server-side objects
* The **invoke** method sends SOAP calls to the vSphere web service

|more| Read more about the :ref:`Vim attributes and methods <vim-reference>`.


Hello World in psphere
----------------------

Not quite, but logging into the server and printing the current time is
probably the equivalent::

    >>> from psphere.vim25 import Vim
    >>> vim = Vim('https://localhost/sdk')
    >>> vim.login('Administrator', 'none')
    >>> servertime = vim.invoke(method='CurrentTime', _this=vim.service_instance)
    >>> print(servertime)
    2010-09-04 18:35:12.062575
    >>> vim.logout()

All vSphere API methods are invoked with a **_this** parameter, which is
the **ManagedObjectReference** that the method will be invoked for.

In this case, we have invoked the **CurrentTime** method of the
**ServiceInstance** managed object.


General programming pattern
---------------------------

Create a new Vim instance::

    >>> from psphere.vim25 import Vim, Folder, Datacenter
    >>> vim = Vim('https://localhost/sdk')

...log into the server::

    >>> vim.login('Administrator', 'mypassword')

...instantiate a *view* of a server-side managed object::

    >>> root_folder = vim.get_view(mo_ref=vim.sc.rootFolder)
    >>> root_folder.__class__
    <class 'psphere.vim25.Folder'>

...access properties of the view::

    >>> print(root_folder.name)
    Datacenters

...to follow vSphere best practise you can limit the properties retrieved to
the attributes you intend to use::

    >>> root_folder = vim.get_view(mo_ref=vim.sc.rootFolder,
                                   properties=['childType'])
    >>> type(root_folder.name)
    <type 'NoneType'>
    >>> print(root_folder.childType)
    [Folder, Datacenter]

...invoke a method::

    >>> new_folder_mor = vim.invoke('CreateFolder', _this=root_folder, name='New')
    >>> new_folder = vim.get_view(mo_ref=new_folder_mor)
    >>> print(new_folder.name)
    New

...log out of the server::

    >>> vim.logout()


Finding a ManagedEntity
-----------------------

Finding a **ManagedEntity** by name. Notice that we follow vSphere best
practise by specifying the properties we're going to use in the **properties**
parameter::

    >>> from psphere.vim25 import *
    >>> vim = Vim('https://localhost/sdk')
    >>> vim.login('Administrator', 'none')
    >>> vm = vim.find_entity_view(view_type='VirtualMachine',
                                  filter={'name': 'bennevis'},
                                  properties=['name', 'summary', 'config'])
    >>> vm.__class__
    <class 'psphere.vim25.VirtualMachine'>
    >>> vm.name
    bennevis
    >>> vm.summary.guest.ipAddress
    10.183.11.85
    >>> vm.config.hardware.memoryMB
    4096


.. |more| image:: more.png
          :align: middle
          :alt: more info    
