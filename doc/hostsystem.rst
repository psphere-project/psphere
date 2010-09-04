HostSystem examples
===================

This page provides examples for working with **HostSystem**'s. The examples
accumulate as they go so make sure you reference the previous examples.

Finding a HostSystem
--------------------

Connect to the server and find the **HostSystem** view::


    >>> from psphere.vim25 import Vim, Folder, Datacenter
    >>> vim = Vim('https://localhost/sdk')
    >>> vim.login('Administrator', 'none')
    >>> host_system = vim.find_entity_view(view_type='HostSystem',
                                           filter={'name': 'k2.local'},
                                           properties=['name', 'summary', 'vm'])
    >>> host_system.name
    k2.local
    >>> host_system.summary.hardware.model
    Sun Fire X4440


How many VirtualMachine's on a HostSystem?
----------------------------------------------

Just count the number of **ManagedObjectReference**'s in the **HostSystem.vm**
property::

    >>> len(host_system.vm)
    40


Listing VirtualMachine's on a HostSystem
----------------------------------------

The **HostSystem.vm** attribute contains a list of **VirtualMachine** MOR's.
First we use this to create a list of **VirtualMachine** views using the
**Vim.get_views** method, populating the views with *name* and *summary*
using the *properties* parameter.

Then it's just a matter of using a for loop to iterate through them. Notice
though, that we except NameError to catch any attributes that the server
hasn't returned::

    >>> host_system = vim.find_entity_view(view_type='HostSystem',
                                           filter={'name': 'k2.local'},
                                           properties=['vm'])
    >>> vms = vim.get_views(mo_refs=host_system.vm, properties=['name', 'summary']
    >>> for vm in vms:
    >>> try:
    >>>     vm.name
    >>>     vm.summary.config.memorySizeMB
    >>> except NameError:
    >>>     'No value'
    genesis
    2048
    sdv1sdfsas04
    'No value'
    pelmo
    4096
    sdi2brmapp01
    4096
    ssi5oamapp01
    4096
    twynam
    1024
    <truncated>

