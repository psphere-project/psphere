Datastore examples
==================

WARNING!!!! Not updated for new API!

This page provides examples for working with datastores.


Finding a datastore
-------------------

You can find a datastore in a ComputeResource using the **find_datastore**
convenience method::

    >>> from psphere.client import Client
    >>> from psphere.managedobjects import Datastore
    >>> client = Client("server.esx.com", "Administrator", "strongpass")
    >>> datastore = Datastore.get(name="nas03")
    >>> print(datastore.summary.name)
    nas03
    >>> print("%iGB" % (datastore.summary.freeSpace/1073741824))
    13203GB


Finding all VMs attached to a datastore
---------------------------------------

Just look at the vm property of the Datastore managed object::

    >>> for vm in datastore.vm:
    >>>     try:
    >>>         print(vm.name)
    >>>         print(vm.summary.config.guestId)
    >>>     except AttributeError:
    >>>         print("Unknown")
    >>>     print("----------")
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
