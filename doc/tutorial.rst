.. highlight:: python

First steps with psphere
========================

This document is meant to give a tutorial-like overview of the main psphere
objects and the common tasks that psphere is used for.

The green arrows designate "more info" links leading to more detailed
sections about the described task.


Vendor documentation
--------------------

VMware provides very good documentation for the VMware vSphere API. It is
suggested that you at least read the introductory documents to gain a conceptual
understanding of the API.

Throughout this documentation there are links to the API reference
documentation.

|more| See :ref:`useful references <useful-references>`.


The Client object
-----------------

The Client object is the entry point into psphere. Through it you can login to a
vSphere server and obtain Python objects representing managed objects. You can
then access information about and execute methods on those objects.

|more| Read more about the :ref:`Vim attributes and methods <vim-reference>`.


Hello World in psphere
----------------------

Not quite, but logging into the server and printing the current time is close::

    >>> from psphere.client import Client
    >>> client = Client("your.esxserver.com", "Administrator", "strongpass")
    >>> servertime = client.si.CurrentTime()
    >>> print(servertime)
    2010-09-04 18:35:12.062575
    >>> client.logout()


General programming pattern
---------------------------

Create a new Client::

    >>> from psphere.client import Client
    >>> client = Client("your.esxserver.com", "Administrator", "strongpass")

...check out the rootFolder of the content attribute, it's a Python object::

    >>> client.si.content.rootFolder.__class__
    <class 'psphere.managedobjects.Folder'>

...access properties of it::

    >>> print(client.si.content.rootFolder.name)
    Datacenters

...invoke a method::

    >>> new_folder = client.si.content.rootFolder.CreateFolder(name="New")
    >>> print(new_folder.name)
    New
    >>> task = new_folder.Destroy_Task()
    >>> print(task.info.state)
    success

...log out of the server::

    >>> client.logout()


Finding a ManagedEntity
-----------------------

Managed Object's which extend the **ManagedEntity** class are the most
commonly used objects in the vSphere API. These include Managed Object's
such as HostSystem's and VirtualMachine's.

psphere makes it easy to find Managed Entity's by providing a get()
classmethod to find them::

    >>> from psphere.client import Client
    >>> from psphere.managedobjects import VirtualMachine
    >>> client = Client("your.esxserver.com", "Administrator", "strongpass")
    >>> vm = VirtualMachine.get(client, name="genesis")
    >>> vm.__class__
    <class 'psphere.managedobjects.VirtualMachine'>
    >>> vm.name
    bennevis
    >>> vm.summary.guest.ipAddress
    10.183.11.85
    >>> vm.config.hardware.memoryMB
    4096

There is also the all() method to get all entities of that type::

    >>> vms = VirtualMachine.all(client)

Lazy loading of properties and pre-loading properties
-----------------------------------------------------

At this point we have to delve into a more complicated aspect of vSphere and
how psphere handles it. You do not need to worry about this, psphere will just
work for you -- albeit inefficiently in some cases.

The vSphere SDK architecture provides abstract "views" of server side objects,
some of these objects can be quite substantial, both in size and server
resources required to collect them.

If you retrieve substantial objects then your scripts will be slow and you
will generate load on your vSphere server.

psphere deals with this by lazily loading objects on access. In most cases
this is fine, but you can achieve substantial speed-ups -- especially for
lists of managed objects -- by pre-loading objects you know that you are
going to access.

For example, a HostSystem has a "vm" property which is a list of
VirtualMachine objects on that host. If you know you are going to loop
over all those VM's and print their name, you can preload the name property
using the preload method::

    >>> hs = HostSystem.get(client, name="myhost")
    >>> hs.preload("vm", properties=["name"])
    >>> for vm in hs.vm:
    >>>     print(vm.name)
    >>> ...


Caching
-------

Once lazily loaded or pre-loaded, attributes will be cached for a pre-defined
time (5 minutes, which is not configurable but will be in the next release).

To update the cache for a specific property of an object, use the update()
method with the properties parameter::

    >>> hs.update(properties=["name"])

To update the cache for all cached properties of an object, use the update()
method with no parameters::

    >>> hs.update()

To clear the property cache for an object, use the flush_cache() method::

    >>> hs.flush_cache()


.. |more| image:: more.png
          :align: middle
          :alt: more info    
