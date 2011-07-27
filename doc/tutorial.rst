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

Throughout this documentation there are links to the API reference documentation.

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
    >>> client = Client('https://localhost/sdk', 'Administrator', 'none')
    >>> servertime = client.si.CurrentTime()
    >>> print(servertime)
    2010-09-04 18:35:12.062575
    >>> client.logout()


General programming pattern
---------------------------

Create a new Client::

    >>> from psphere.client import Client
    >>> client = Client('https://localhost/sdk', 'Administrator', 'mypassword')

...check out the rootFolder of the content attribute, it's a Python object::

    >>> root_folder = client.si.content.rootFolder
    >>> root_folder.__class__
    <class 'psphere.managedobjects.Folder'>

...access properties of a it::

    >>> print(root_folder.name)
    Datacenters

...invoke a method::

    >>> new_folder = root_folder.CreateFolder(name='New')
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

psphere makes it easy to find Managed Entity's by providing a find_one()
classmethod to find them::

    >>> from psphere.client import Client
    >>> from psphere.managedobjects import VirtualMachine
    >>> client = Client('https://localhost/sdk', 'Administrator', 'none')
    >>> vm = VirtualMachine.find_one(client=client, filter={'name': 'genesis'})
    >>> vm.__class__
    <class 'psphere.managedobjects.VirtualMachine'>
    >>> vm.name
    bennevis
    >>> vm.summary.guest.ipAddress
    10.183.11.85
    >>> vm.config.hardware.memoryMB
    4096


Some notes on attribute retrieval
---------------------------------

At this point we have to delve into a more complicated aspect of vSphere and
how psphere handles it. You do not need to worry about this, psphere will just
work for you -- albeit inefficiently in some cases.

The vSphere SDK architecture provides abstract "views" of server side objects,
some of these objects can be quite substantial, both in size and server
resources required to collect them.

For example a HostSystem has a xxx which has an xxx which has an xxx. If you
inefficiently retrieve these attributes and you retrieve substantial objects
then your scripts will be slow and you will generate load on your vSphere
server.

psphere deals with this using the following logic:

When a Managed Object is instantiated, it will not retrieve properties from
the server when it is instantiated. The property will be "lazily" retrieved
from the
server when it is accessed. Once accessed, it will be cached for future
use. This works well if you are accessing only a few properties, but it
requires a SOAP call for each property retrieval, so if you know ahead
of time which properties you will be accessing, then you can retrieve
those properties from the server with a single SOAP call by creating,
or updating the Managed Object with the properties you will be using::

    >>> vm = VirtualMachine.find_one(client=client, filter={"name": "genesis"}, properties=["name", "guest"])
    >>> vm.name
    genesis
    >>> vm.guest.ipAddress
    10.183.10.10
    >>> vm.update(properties="all")
    >>> vm.summary.overallStatus
    green

The vSphere API even allows you to do this extremely efficiently using
a "sub" property specification::

    >>> del(vm.config) # Deletes the cached property
    >>> vm = VirtualMachine.find_one(client=client, filter={"name": "genesis"}, properties=["config.guestId"])
    >>> print(vm.config.guestId)
    rhel5guest

The properties parameter is available in the Client.find_entity_view(),
Client.find_entity_views() methods and is implemented in the find(),
find_one() and update() methods of the ManagedObject class (which all
Managed Object's derive from).


.. |more| image:: more.png
          :align: middle
          :alt: more info    
