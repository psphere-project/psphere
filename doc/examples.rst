First steps with psphere
========================

Connecting and retrieving the current server time
-------------------------------------------------
::

    >>> from psphere.vim25 import Vim
    >>> vim = Vim('https://localhost/sdk', 'Administrator', 'none')
    >>> vim.service_instance.current_time()
    datetime.datetime(2010, 8, 27, 0, 25, 45, 9695)

Finding an entity and retrieving a view object
----------------------------------------------
::

    >>> from psphere.vim25 import Vim
    >>> vim = Vim('https://localhost/sdk', 'Administrator', 'none')
    >>> vm = vim.find_entity_view(view_type='VirtualMachine', filter={'name': 'bennevis'})
    >>> vm.name
    bennevis
    >>> vm.update_view_data(['summary', 'config'])
    >>> vm.summary.guest.ipAddress
    10.183.11.85
    >>> vm.config.hardware.memoryMB
    4096

It is important to note that a returned view will only be pre-populated
with properties specified in the `filter` parameter. Iterating through
all properties can be quite costly for some views, so vSphere SDK best
practice is to retrieve only relevant properties.

On the other hand, it is also quite costly to make many SOAP calls to
the server, so the use of getXXX() methods can also be inefficient. By 
specifying a list of properties to retrieve, you get full control and
the best of both worlds.

If you know you want all properties, you can use the
ManagedObject.update_all_properties() method.

