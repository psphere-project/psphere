First steps with pSphere
========================

pSphere is a convenience API for the vSphere Web Services SDK. As such,
the official documentation is valuable and relevant reference material.

Links to these documents can be found in the references section.

The Vim object
--------------
The Vim object is the entry point into the pSphere API. Creating a new
Vim instance logs you into a vSphere server and provides methods for 
obtaining local *views* of server-side objects.

After initialisation, the Vim object provides convenient access to a few
of the common managed objects:
* ServiceInstance through Vim.`si`
* ServiceContent through Vim.`sc`
* PropertyCollector through Vim.`pc`

The Vim object also provides:
* The `invoke` method for sending webservice calls
* A number of convenience methods for finding managed objects in the inventory
* Synchronous versions of a number of the \*_Task methods

Read more about the Vim object methods here.

Hello World in pSphere
----------------------
Not quite, but we can connect and print the servers time::

    >>> from psphere.vim25 import Vim
    >>> vim = Vim('https://localhost/sdk', 'Administrator', 'none')
    >>> vim.invoke('CurrentTime', _this=vim.si.mor)
    datetime.datetime(2010, 8, 27, 0, 25, 45, 9695)

General programming pattern
---------------------------
Create a new Vim instance:

::

    >>> from psphere.vim25 import Vim, Folder, Datacenter
    >>> vim = Vim('https://localhost/sdk', 'Administrator', 'none')

...instantiate a view a server-side managed object:

::

    >>> root_folder = Folder(mor=vim.sc.rootFolder, vim=vim)

...populate some attributes of the view instance (efficient):

::

    >>> root_folder.update_view_data(properties=['name'])
    >>> root_folder.name
    Datacenters

...populate all attributes of the view instance (convenient):

::

    >>> root_folder.update_view_data()
    >>> for attribute in root_folder.__dict__:
    >>>     print('%s: %s' % (attribute, getattr(root_folder, attribute)))
    childEntity: [(ManagedObjectReference){
       value = "ha-datacenter"
       _type = "Datacenter"
     }]
    childType: [Datacenter]
    configStatus: green
    ... (truncated)

...drill down through an instance's ManagedObjectReference:

::

    >>> dc = Datacenter(root_folder.childEntity[0])
    >>> dc.update_view_data(properties=['name', 'configStatus'])
    >>> dc.name
    Dalley St
    >>> dc.configStatus
    gray

Handling exceptions
-------------------
At time of writing, the vSphere SDK raises 435 types of exception. Rather
than duplicate these in pSphere, the API instead raises a single fault 
called `VimFault` when any vSphere related fault is detected. The `VimFault`
exception contains the following attributes:

* fault: The fault object
* fault_type: The class name of the fault (the name you will find in the vSphere documentation)

All other properties which are listed in the API reference will be available
as attributes of the fault object.

::

    >>> try:
    >>>     operation()
    >>> except VimFault, e:
    >>>     e.fault_code
    InvalidProperty
    >>>     e.fault.name
    name

Finding an entity and retrieving a view object
----------------------------------------------

::

    >>> from psphere.vim25 import Vim
    >>> vim = Vim('https://localhost/sdk', 'Administrator', 'none')
    >>> vm = VirtualMachine.from_filter(vim=vim, filter={'name': 'bennevis'})
    >>> vm.name
    bennevis
    >>> vm.update_view_data(['summary', 'config'])
    >>> vm.summary.guest.ipAddress
    10.183.11.85
    >>> vm.config.hardware.memoryMB
    4096

Finding a datastore on a ComputeResource
-----------------------------------------

::

    >>> from psphere.vim25 import Vim, ComputeResource
    >>> vim = Vim('https://localhost/sdk', 'Administrator', 'none')
    >>> host = vim.find_entity_view(view_type='HostSystem', filter={'name': 'k2'})
    >>> host.update_view_data(properties=['parent'])
    >>> cr = ComputeResource(mor=host.parent, vim=vim)
    >>> ds = cr.find_datastore(name='nas03')
    >>> ds.update_view_data(properties=['summary'])
    >>> ds.summary.name
    nas03
    >>> ds.summary.freeSpace
    14493557854208L

Querying all datastores in a ComputeResource
---------------------------------------------

::

    >>> from psphere.vim25 import Vim, ComputeResource
    >>> vim = Vim('https://localhost/sdk', 'Administrator', 'none')
    >>> host = vim.find_entity_view(view_type='HostSystem', filter={'name': 'k2'})
    >>> host.update_view_data(properties=['parent'])
    >>> cr = ComputeResource(mor=host.parent, vim=vim)
    >>> cr.update_view_data(properties=['datastore'])
    >>> datastores = vim.get_views(mors=cr.datastore, properties=['summary'])
    >>> for datastore in datastores:
    >>>     datastore.summary.name
    >>>     datastore.summary.freeSpace
    nas03
    14493557854208L
    k2:storage1
    137924444160L
    k2:storage2
    310702505984L

Finding all VMs attached to a datastore
---------------------------------------

::

    >>> from psphere.vim25 import Vim, ComputeResource
    >>> vim = Vim('https://localhost/sdk', 'Administrator', 'none')
    >>> cluster.update_view_data(properties=['datastore']
    >>> datastores = vim.get_views(mors=cluster.datastore, properties=['vm', 'summary'])
    >>> for datastore in datastores:
    >>>     if datastore.summary.name == 'nas03':
    >>>         ds = datastore
    >>>         break
    >>> vms = vim.get_views(mors=ds.vm, properties=['name', 'summary', 'config'])
    >>> for vm in vms:
    >>>     vm.name
    hudsla02
    hudmas01
    sandbox5
    maunaloa
    sandbox2


It is important to note that an object created using the `find_entity_view`
method will only contain the properties which are specified in the 
`filter` parameter. This is by design, so you must explicitly populate
the necessary properties, see TODO.

Populating view attributes
==========================

One aspect which new users might find confusing is the way in which
attributes are populated in a view instance.

vSphere best practice recommends that you only retrieve "what you need". The
significance of this can be seen by turning on logging and seeing how
much data passes between a client and server for a complex object like
`HostSystem`. Apart from the data transfer, there is also an overhead on
the server.

pSphere has been designed with efficiency and convenience in mind, which
one you choose and when is up to you.

#. All properties can be conveniently populated using the `update_view_data` method with no arguments.
#. Selected properties can be efficiently populated by passing a list of those properties to the `update_view_data` method.
#. If an object has been instantiated with the `find_entity_view` method, then the properties specified in the `filter` dictionary keys are pre-populated because they have already been retrieved for comparison.

Err... so which method should I use? 
------------------------------------

For maximum convenience, call the `update_view_data` method with no
parameters. For maximum efficiency call the `update_view_data` method
with the required items in the properties parameter.

