Error handling
==============

At time of writing, the vSphere SDK raises 435 types of exception. Rather
than duplicate these in psphere, the API instead raises a single fault 
called `VimFault` when any vSphere related fault is detected. The `VimFault`
exception contains the following attributes:

* fault: The fault object
* fault_type: The class name of the fault (the name you will find in the vSphere documentation)

All other properties which are listed in the API reference will be available
as attributes of the fault object.

Handling exceptions
-------------------

::

    >>> try:
    >>>     operation()
    >>> except VimFault, e:
    >>>     e.fault_code
    InvalidProperty
    >>>     e.fault.name
    name

