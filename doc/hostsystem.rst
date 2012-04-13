HostSystem examples
===================

This page provides examples for working with **HostSystem** views. The
examples accumulate as they go so make sure you reference the previous examples.

Finding a single HostSystem by name
-----------------------------------

Connect to the server and find the **HostSystem** view::


    >>> from psphere.client import Client
    >>> from psphere.managedobjects import HostSystem
    >>> client = Client("server.esx.com", "Administrator", "strongpass")
    >>> hs = HostSystem.get(client, name="k2")
    >>> print(hs.name)
    k2
    >>> print(hs.summary.hardware.model)
    Sun Fire X4440


Finding all HostSystem's
------------------------

Use the .all() method which can be found on all objects extending
ManagedEntity::

    >>> hs_list = HostSystem.all(client)
    >>> len(hs_list)
    3
    >>> for hs in hs_list:
    >>>     print(hs.name)
    host1
    host2
    host3


How many VirtualMachine's on a HostSystem?
----------------------------------------------

Just count the number of **VirtualMachine**'s objects in the vm property::

    >>> len(host_system.vm)
    40


Listing VirtualMachine's on a HostSystem
----------------------------------------

The **HostSystem.vm** attribute contains a list of **VirtualMachine** objects.

    >>> for vm in host_system.vm:
    >>>     try:
    >>>         print(vm.name)
    >>>         print(vm.summary.config.memorySizeMB)
    >>>     except AttributeError:
    >>>         print('No value')
    >>>     print('---------')
    genesis
    2048
    ---------
    sdv1sdfsas04
    'No value'
    ---------
    pelmo
    4096
    ---------
    sdi2brmapp01
    4096
    ---------
    ssi5oamapp01
    4096
    ---------
    twynam
    1024
    ---------
