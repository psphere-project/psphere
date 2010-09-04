Datastore examples
==================

This page provides examples for working with datastores.


Finding a datastore in a ComputeResource
-----------------------------------------

You can find a datastore in a ComputeResource using the **find_datastore**
convenience method::

    >>> from psphere.vim25 import Vim
    >>> vim = Vim('https://localhost/sdk')
    >>> vim.login('Administrator', 'none')
    >>> compute_resource = vim.find_entity_view(view_type='ComputeResource', filter={'name': 'My Cluster'})
    >>> datastore = compute_resource.find_datastore(name='nas03')
    >>> print(datastore.summary.name)
    nas03
    >>> print('%sGB' % (int(datastore.summary.freeSpace)/1024/1024/1024))
    13203GB


Finding all VMs attached to a datastore
---------------------------------------

It's quite easy to find all virtual machines attached to a **Datastore** by
using the same **get_views** technique with an instances *vm* managed object
reference array::

    >>> vms = vim.get_views(mo_refs=datastore.vm, properties=['name', 'summary'])
    >>> for vm in vms:
    >>>     try:
    >>>         print(vm.name)
    >>>         print(vm.summary.config.guestId)
    >>>     except AttributeError:
    >>>         print('Unknown')
    >>>     print('----------')
    sdi3extapp01
    sles10_64Guest
    ----------
    sdi3ppcapp01
    sles10_64Guest
    ----------
    sdi3oamapp01
    sles10_64Guest
    ----------
    hudmas01
    rhel5Guest
    ----------
    sandbox5
    rhel5Guest
    ----------



Finding and querying all datastores in a ComputeResource
--------------------------------------------------------

You can find all datastores attached to a ComputeResource and iterate through
them::

    >>> compute_resource.update_view_data(properties=['datastore'])
    >>> datastores = vim.get_views(mo_refs=compute_resource.datastore, properties=['summary'])
    >>> for datastore in datastores:
    >>>     try:
    >>>         print(datastore.summary.name)
    >>>         print('%sGB' % (int(datastore.summary.freeSpace)/1024/1024/1024))
    >>>     except AttributeError:
    >>>         print('Unknown')
    >>>     print('----------')
    nas03
    13203GB
    -----------
    sonder:storage1
    128GB
    -----------
    bogong:storage2
    237GB
    -----------

