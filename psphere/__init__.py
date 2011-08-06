import time                                                                     

import logging

from suds import MethodNotFound

logger = logging.getLogger("psphere")

__version__ = '0.5.0'
__released__ = '0.5.0 (hg)'

class cached_property(object):
    """Decorator for read-only properties evaluated only once within TTL period.

    It can be used to created a cached property like this::

        import random

        # the class containing the property must be a new-style class
        class MyClass(object):
            # create property whose value is cached for ten minutes
            @cached_property(ttl=600)
            def randint(self):
                # will only be evaluated every 10 min. at maximum.
                return random.randint(0, 100)

    The value is cached  in the '_cache' attribute of the object instance that
    has the property getter method wrapped by this decorator. The '_cache'
    attribute value is a dictionary which has a key for every property of the
    object which is wrapped by this decorator. Each entry in the cache is
    created only when the property is accessed for the first time and is a
    two-element tuple with the last computed property value and the last time
    it was updated in seconds since the epoch.

    The default time-to-live (TTL) is 300 seconds (5 minutes). Set the TTL to
    zero for the cached value to never expire.

    To expire a cached property value manually just do::
    
        del instance._cache[<property name>]

    """
    def __init__(self, fget, doc=None):
        self.ttl = 300
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__
        self.__module__ = fget.__module__

    def __get__(self, inst, owner):
        now = time.time()
        try:
            # Get the value from the cache
            value, last_update = inst._cache[self.__name__]
            # If the value in the cache exceeds the TTL then raise
            # AttributeError so that we retrieve the value again below
            if self.ttl > 0 and now - last_update > self.ttl:
                raise AttributeError
        except (KeyError, AttributeError):
            # We end up here if the value hasn't been cached
            # or the value exceeds the TTL. We call the decorated
            # function to get the value.
            value = self.fget(inst)
            try:
                # See if the instance has a cache attribute
                cache = inst._cache
            except AttributeError:
                # If it doesn't, initialise the attribute and use it
                cache = inst._cache = {}
            # Set the value in the cache dict to our values
            cache[self.__name__] = (value, now)
        # Finally, return either the value from the cache or the
        # newly retrieved value
        return value


class ManagedObject(object):
    """The base class which all managed object's derive from.
    
   :param mo_ref: The managed object reference used to create this instance
   :type mo_ref: ManagedObjectReference
   :param client: A reference back to the psphere client object, which \
   we use to make calls.
   :type client: Client

    """
    valid_attrs = set([])
    def __init__(self, mo_ref, client):
        self._cache = {}
        logger.debug("===== Have been passed %s as mo_ref: " % mo_ref)
        self.mo_ref = mo_ref
        self.client = client

    def _get_dataobject(self, name, multivalued):
        """This function only gets called if the decorated property
        doesn't have a value in the cache."""
        logger.debug("Querying server for uncached data object %s" % name)
        # This will retrieve the value and inject it into the cache
        self.update_view_data(properties=[name])
        return self._cache[name][0]

    def _get_mor(self, name, multivalued):
        """This function only gets called if the decorated property
        doesn't have a value in the cache."""
        logger.debug("Querying server for uncached MOR %s" % name)
        # This will retrieve the value and inject it into the cache
        if multivalued is True:
            self.update_view_data(properties=[name])
            logger.debug("Getting views for MOR")
            views = self.client.get_views(self._cache[name][0])
            return views

    def update_view_data(self, properties=None):
        """Update the local object from the server-side object.
        
        >>> vm = VirtualMachine.find_one(client, filter={"name": "genesis"})
        >>> # Update all properties
        >>> vm.update_view_data()
        >>> # Update the config and summary properties
        >>> vm.update_view_data(properties=["config", "summary"]

        :param properties: A list of properties to update.
        :type properties: list

        """
        if properties is None:
            properties = []
        logger.info("Updating view data for object of type %s" % self.mo_ref._type)
        property_spec = self.client.create('PropertySpec')
        property_spec.type = str(self.mo_ref._type)
        # Determine which properties to retrieve from the server
        if not properties and self.client.auto_populate:
            logger.debug("Retrieving all properties of the object")
            property_spec.all = True
        else:
            logger.debug("Retrieving %s properties" % len(properties))
            property_spec.all = False
            property_spec.pathSet = properties

        object_spec = self.client.create('ObjectSpec')
        object_spec.obj = self.mo_ref

        pfs = self.client.create('PropertyFilterSpec')
        pfs.propSet = [property_spec]
        pfs.objectSet = [object_spec]

        # Create a copy of the property collector and call the method
        pc = self.client.sc.propertyCollector
        object_content = pc.RetrieveProperties(specSet=pfs)[0]
        if not object_content:
            # TODO: Improve error checking and reporting
            logger.error("Nothing returned from RetrieveProperties!")

        self.set_view_data(object_content)

    def set_view_data(self, object_content):
        """Update the local object from the passed in object_content."""
        # A debugging convenience, allows inspection of the object_content
        # that was used to create the object
        logger.info("Setting view data for a %s" % self.__class__)
        self._object_content = object_content

        for dynprop in object_content.propSet:
            # If the class hasn't defined the property, don't use it
            if dynprop.name not in self.valid_attrs:
                logger.error("Server returned a property '%s' but the object"
                             " hasn't defined it so it is being ignored." %
                             dynprop.name)
                continue

            try:
                if not len(dynprop.val):
                    logger.info("Server returned empty value for %s" %
                                dynprop.name)
                    continue
            except TypeError:
                # This except allows us to pass over:
                # TypeError: object of type 'datetime.datetime' has no len()
                # It will be processed in the next code block
                logger.error("%s of type %s has no len!" % (dynprop.name,
                                                            type(dynprop.val)))
                pass

            # Values which contain classes starting with Array need
            # to be converted into a nicer Python list
            if dynprop.val.__class__.__name__.startswith('Array'):
                # suds returns a list containing a single item, which
                # is another list. Use the first item which is the real list
                logger.info("Setting value of an Array* property")
                logger.debug("%s being set to %s" % (dynprop.name,
                                                     dynprop.val[0]))
                now = time.time()
                self._cache[dynprop.name] = (dynprop.val[0], now)
            else:
                logger.info("Setting value of a single-valued property")
                logger.debug("DynamicProperty value is a %s: " %
                             dynprop.val.__class__.__name__)
                logger.debug("%s being set to %s" % (dynprop.name,
                                                     dynprop.val))
                now = time.time()
                self._cache[dynprop.name] = (dynprop.val, now)

    def __getattribute__(self, name):
        """Overridden so that SOAP methods can be proxied.

        This is overridden for two reasons:
        - To implement caching of ManagedObject properties
        - To each SOAP method can be accessed through the object without having to explicitly define it.
        
        It is achieved by checking if the method exists in the SOAP service.
        
        If it doesn't then the exception is caught and the default
        behaviour is executed.
        
        If it does, then a function is returned that will invoke
        the method against the SOAP service with _this set to the
        current objects managed object reference.
        
        :param name: The name of the method to call.
        :param type: str

        """
        logger.debug("Entering overridden built-in __getattribute__"
                     " with %s" % name)
        # Built-ins always use the default behaviour
        if name.startswith("__"):
            logger.debug("Returning built-in attribute %s" % name)
            return object.__getattribute__(self, name)

        try:
            # Here we must manually get the client object so we
            # don't get recursively called when the next method
            # call looks for it
            client = object.__getattribute__(self, "client")
            # TODO: This should probably be raised by Client.invoke
            getattr(client.service, name)
            logger.debug("Constructing func for %s", name)
            def func(**kwargs):
                result = client.invoke(name, _this=self.mo_ref,
                                            **kwargs)
                logger.debug("Invoke returned %s" % result)
                return result
    
            return func
        except MethodNotFound:
            return object.__getattribute__(self, name)
