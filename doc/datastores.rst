Datastore examples
==================

This page provides examples for working with datastores.


Finding a datastore in a ComputeResource
-----------------------------------------

You can find a datastore in a ComputeResource using the **find_datastore**
convenience method::

    >>> from psphere.vim25 import Vim, ComputeResource
    >>> vim = Vim('https://localhost/sdk', 'Administrator', 'none')
    >>> compute_resource = vim.find_entity_view(view_type='ComputeResource', filter={'name': 'My Cluster'})
    >>> datastore = compute_resource.find_datastore(name='nas03')
    >>> datastore.update_view_data(properties=['summary'])
    >>> datastore.summary.name
    nas03
    >>> datastore.summary.freeSpace
    14493557854208L


Finding and querying all datastores in a ComputeResource
--------------------------------------------------------

You can find all datastores attached to a ComputeResource and iterate through
them::

    >>> from psphere.vim25 import Vim, ComputeResource
    >>> vim = Vim('https://localhost/sdk', 'Administrator', 'none')
    >>> compute_resource = vim.find_entity_view(view_type='ComputeResource', filter={'name': 'My Cluster'})
    >>> datastore = compute_resource.find_datastore(name='nas03')
    >>> compute_resource.update_view_data(properties=['datastore'])
    >>> datastores = vim.get_views(mors=compute_resource.datastore, properties=['summary'])
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

It's quite easy to find all virtual machines attached to a **Datastore** by
using the same **get_views** technique with an instances *vm* managed object
reference array::

    >>> from psphere.vim25 import Vim, ComputeResource
    >>> vim = Vim('https://localhost/sdk', 'Administrator', 'none')
    >>> datastore = vim.find_entity_view(view_type='Datastore', filter={'name': 'nas03'})
    >>> vms = vim.get_views(mors=datastore.vm, properties=['name', 'summary', 'config'])
    >>> for vm in vms:
    >>>     vm.name
    >>>     vm.summary.guest.ipAddress
    >>>     vm.config.hardware.memoryMB
    hudmas01
    10.183.10.41
    1024
    hudsla02
    10.183.10.43
    2048
    sandbox5
    10.183.10.94
    1024
    maunaloa
    10.183.13.54
    4096
    sandbox2
    10.183.12.21
    1024

