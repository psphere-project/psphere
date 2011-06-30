"""                                                                             
:mod:`psphere.server` - vSphere server access
=============================================

.. module:: server

The main module for accessing a vSphere server.

.. moduleauthor:: Jonathan Kinred <jonathan.kinred@gmail.com>

"""
import time
import logging

from psphere import config
from psphere import soap
from psphere.errors import TaskFailedError
from psphere.managedobjects import *

logger = logging.getLogger("psphere")

class Server(object):
    """Represents a VirtualCenter/ESX/ESXi server instance.

    >>> from psphere.server import Server
    >>> server = Server(url="http//esx.foo.com/sdk")

    :param url: The url of the server. e.g. https://esx.foo.com/sdk
    :type url: str
    :param auto_populate: Whether to auto-populate all MOB properties.
    :type auto_populate: bool
    :param debug: Turn debug logging on.
    :type debug: bool

    """
    def __init__(self, url, auto_populate=True, debug=False):
        self.url = url
        self.auto_populate = auto_populate
        self.debug = debug
        self.config = config.get_config()
        # Setup logging
        self._init_logging()
        self.client = soap.get_client(url)
        si_mo_ref = soap.ManagedObjectReference(_type='ServiceInstance',
                                                value='ServiceInstance')
        self.si = ServiceInstance(si_mo_ref, self) 
        self.sc = self.si.RetrieveServiceContent()

    def _init_logging(self):
        """Initialize logging."""
        if self.config["logging"]["destination"] == "CONSOLE":
            lh = logging.StreamHandler()
        else:
            lh = logging.FileHandler(self.config["logging"]["destination"])
        lh.setLevel(self.config["logging"]["level"])
        logger.setLevel(self.config["logging"]["level"])
        logger.addHandler(lh)
        # Initialise logging for the SOAP module
        soap._init_logging(self.config["logging"]["level"], lh)
        logger.debug("Initialised logging")

    def login(self, username, password):
        """Login to a vSphere server.

        >>> server.login(username='Administrator', password='strongpass')

        :param username: The username to authenticate as.
        :type username: str
        :param password: The password to authenticate with.
        :type password: str

        """
        logger.debug("Logging into server")
        self.sc.sessionManager.Login(userName=username, password=password)

    def logout(self):
        """Logout of a vSphere server."""
        self.sc.sessionManager.Logout()

    def invoke(self, method, _this, **kwargs):
        """Invoke a method on the server.

        >>> server.invoke('CurrentTime', server.si)

        :param method: The method to invoke, as found in the SDK.
        :type method: str
        :param _this: The managed object against which to invoke the \
        method.
        :type _this: ManagedObject
        :param kwargs: The arguments to pass to the method, as \
        found in the SDK.
        :type kwargs: TODO

        """
        result = soap.invoke(self.client, method, _this=_this, **kwargs)
        if not hasattr(result, '__iter__'):
            logger.debug("Result is not iterable")
            return result

        # We must traverse the result and convert any ManagedObjectReference
        # to a psphere class, this will then be lazy initialised on use
        logger.debug(result.__class__)
        logger.debug("Result: %s" % result)
        logger.debug("Length: %s" % len(result))
        if type(result) == list:
            new_result = []
            for item in result:
                new_result.append(self.walk_and_convert_sudsobject(item))
        else:
            new_result = self.walk_and_convert_sudsobject(result)
            
        logger.debug("Finished in invoke.")
        #property = self.find_and_destroy(property)
        #print result
        # Return the modified result to the caller
        return new_result

    def walk_and_convert_sudsobject(self, sudsobject):
        """Walks a sudsobject and converts MORs to psphere objects."""
        import suds
        logger.debug("Processing:")
        logger.debug(sudsobject)
        logger.debug("...with keylist:")
        logger.debug(sudsobject.__keylist__)
        # If the sudsobject that we're looking at has a _type key
        # then create a class of that type and return it immediately
        if "_type" in sudsobject.__keylist__:
            logger.debug("sudsobject is a MOR, converting to psphere class")
            kls = classmapper(sudsobject._type)
            new_object = kls(sudsobject, self)
            return new_object

        new_object = sudsobject.__class__()
        for obj in sudsobject:
            if not issubclass(obj[1].__class__, suds.sudsobject.Object):
                logger.debug("Not a sudsobject subclass, skipping")
                setattr(new_object, obj[0], obj[1])
                continue

            logger.debug("Obj keylist: %s" % obj[1].__keylist__)
            if "_type" in obj[1].__keylist__:
                logger.debug("Would convert this node:")
                logger.debug(obj[1])
                kls = classmapper(obj[1]._type)
                setattr(new_object, obj[0], kls(obj[1], self))
            else:
                logger.debug("Didn't find _type in:")
                logger.debug(obj[1])
                setattr(new_object, obj[0], self.walk_and_convert_sudsobject(obj[1]))

        return new_object

    def create_object(self, type_, **kwargs):
        """Create a SOAP object of the requested type.

        >>> server.create_object('VirtualE1000')

        :param type_: The type of SOAP object to create.
        :type type_: str
        :param kwargs: TODO
        :type kwargs: TODO

        """
        obj = soap.create(self.client, type_)
        for key, value in kwargs.items():
            setattr(obj, key, value)
        return obj

#        Notes
#        -----
#        A view is a local, static representation of a managed object in
#        the inventory. The view is not automatically synchronised with 
#        the server-side object and can therefore be out of date a moment
#        after it is retrieved.
#        
#        Retrieval of only the properties you intend to use -- through
#        the use of the properties parameter -- is considered best
#        practise as the properties of some managed objects can be
#        costly to retrieve.

    def get_view(self, mo_ref, properties=None):
        """Get a view of a vSphere managed object.
        
        :param mo_ref: The MOR to get a view of
        :type mo_ref: ManagedObjectReference
        :param properties: A list of properties to retrieve from the \
        server
        :type properties: list
        :returns: A view representing the ManagedObjectReference.
        :rtype: ManagedObject

        """
        # This maps the mo_ref into a psphere class and then instantiates it
        kls = classmapper(mo_ref._type)
        view = kls(mo_ref, self)
        # Update the requested properties of the instance
        view.update_view_data(properties=properties)

        return view

    def get_views(self, mo_refs, properties=None):
        """Get a list of local view's for multiple managed objects.

        :param mo_refs: The list of ManagedObjectReference's that views are \
        to be created for.
        :type mo_refs: ManagedObjectReference
        :param properties: The properties to retrieve in the views.
        :type properties: list
        :returns: A list of local instances representing the server-side \
        managed objects.
        :rtype: list of ManagedObject's

        """
        property_spec = soap.create(self.client, 'PropertySpec')
        # FIXME: Makes assumption about mo_refs being a list
        property_spec.type = str(mo_refs[0]._type)
        if not properties and self.auto_populate:
            property_spec.all = True
        else:
            # Only retrieve the requested properties
            property_spec.all = False
            property_spec.pathSet = properties

        object_specs = []
        for mo_ref in mo_refs:
            object_spec = soap.create(self.client, 'ObjectSpec')
            object_spec.obj = mo_ref
            object_specs.append(object_spec)

        pfs = soap.create(self.client, 'PropertyFilterSpec')
        pfs.propSet = [property_spec]
        pfs.objectSet = object_specs

        object_contents = self.sc.propertyCollector.RetrieveProperties(
            specSet=pfs)
        print('@@@@@@@@@@@@@')
        print(object_contents)
        print('@@@@@@@@@@@@@')
        views = []
        for object_content in object_contents:
            # Update the instance with the data in object_content
            object_content.obj.set_view_data(object_content=object_content)
            views.append(object_content.obj)

        return views
        
    def get_search_filter_spec(self, begin_entity, property_spec):
        """Build a PropertyFilterSpec capable of full inventory traversal.
        
        By specifying all valid traversal specs we are creating a PFS that
        can recursively select any object under the given entity.

        :param begin_entity: The place in the MOB to start the search.
        :type begin_entity: ManagedEntity
        :param property_spec: TODO
        :type property_spec: TODO
        :returns: A PropertyFilterSpec, suitable for recursively searching \
        under the given ManagedEntity.
        :rtype: PropertyFilterSpec

        """
        # The selection spec for additional objects we want to filter
        ss_strings = ['resource_pool_traversal_spec',
                      'resource_pool_vm_traversal_spec',
                      'folder_traversal_spec',
                      'datacenter_host_traversal_spec',
                      'datacenter_vm_traversal_spec',
                      'compute_resource_rp_traversal_spec',
                      'compute_resource_host_traversal_spec',
                      'host_vm_traversal_spec']

        # Create a selection spec for each of the strings specified above
        selection_specs = [
            soap.create(self.client, 'SelectionSpec', name=ss_string)
            for ss_string in ss_strings
        ]

        # A traversal spec for deriving ResourcePool's from found VMs
        rpts = soap.create(self.client, 'TraversalSpec')
        rpts.name = 'resource_pool_traversal_spec'
        rpts.type = 'ResourcePool'
        rpts.path = 'resourcePool'
        rpts.selectSet = [selection_specs[0], selection_specs[1]]

        # A traversal spec for deriving ResourcePool's from found VMs
        rpvts = soap.create(self.client, 'TraversalSpec')
        rpvts.name = 'resource_pool_vm_traversal_spec'
        rpvts.type = 'ResourcePool'
        rpvts.path = 'vm'

        crrts = soap.create(self.client ,'TraversalSpec')
        crrts.name = 'compute_resource_rp_traversal_spec'
        crrts.type = 'ComputeResource'
        crrts.path = 'resourcePool'
        crrts.selectSet = [selection_specs[0], selection_specs[1]]

        crhts = soap.create(self.client, 'TraversalSpec')
        crhts.name = 'compute_resource_host_traversal_spec'
        crhts.type = 'ComputeResource'
        crhts.path = 'host'
         
        dhts = soap.create(self.client, 'TraversalSpec')
        dhts.name = 'datacenter_host_traversal_spec'
        dhts.type = 'Datacenter'
        dhts.path = 'hostFolder'
        dhts.selectSet = [selection_specs[2]]

        dvts = soap.create(self.client, 'TraversalSpec')
        dvts.name = 'datacenter_vm_traversal_spec'
        dvts.type = 'Datacenter'
        dvts.path = 'vmFolder'
        dvts.selectSet = [selection_specs[2]]

        hvts = soap.create(self.client, 'TraversalSpec')
        hvts.name = 'host_vm_traversal_spec'
        hvts.type = 'HostSystem'
        hvts.path = 'vm'
        hvts.selectSet = [selection_specs[2]]
      
        fts = soap.create(self.client, 'TraversalSpec')
        fts.name = 'folder_traversal_spec'
        fts.type = 'Folder'
        fts.path = 'childEntity'
        fts.selectSet = [selection_specs[2], selection_specs[3],
                          selection_specs[4], selection_specs[5],
                          selection_specs[6], selection_specs[7],
                          selection_specs[1]]

        obj_spec = soap.create(self.client, 'ObjectSpec')
        obj_spec.obj = begin_entity
        obj_spec.selectSet = [fts, dvts, dhts, crhts, crrts,
                               rpts, hvts, rpvts]

        pfs = soap.create(self.client, 'PropertyFilterSpec')
        pfs.propSet = [property_spec]
        pfs.objectSet = [obj_spec]
        return pfs

    def invoke_task(self, method, **kwargs):
        """Execute a \*_Task method and wait for it to complete.
        
        :param method: The \*_Task method to invoke.
        :type method: str
        :param kwargs: The arguments to pass to the method.
        :type kwargs: TODO

        """
        # Don't execute methods which don't return a Task object
        if not method.endswith('_Task'):
            print('ERROR: invoke_task can only be used for methods which '
                  'return a ManagedObjectReference to a Task.')
            return None

        task_mo_ref = self.invoke(method=method, **kwargs)
        task = Task(task_mo_ref, self)
        task.update_view_data(properties=['info'])
        # TODO: This returns true when there is an error
        while True:
            if task.info.state == 'success':
                return task
            elif task.info.state == 'error':
                # TODO: Handle error checking properly
                raise TaskFailedError(task.info.error.localizedMessage)

            # TODO: Implement progresscallbackfunc
            # Sleep two seconds and then refresh the data from the server
            time.sleep(2)
            task.update_view_data(properties=['info'])

    def find_entity_views(self, view_type, begin_entity=None, properties=None):
        """Find all ManagedEntity's of the requested type.

        :param view_type: The type of ManagedEntity's to find.
        :type view_type: str
        :param begin_entity: The MOR to start searching for the entity. \
        The default is to start the search at the root folder.
        :type begin_entity: ManagedObjectReference or None
        :returns: A list of ManagedEntity's
        :rtype: list

        """
        if properties is None:
            properties = []

        # Start the search at the root folder if no begin_entity was given
        if not begin_entity:
            begin_entity = self.sc.rootFolder.mo_ref

        property_spec = soap.create(self.client, 'PropertySpec')
        property_spec.type = view_type
        property_spec.all = False
        property_spec.pathSet = properties

        pfs = self.get_search_filter_spec(begin_entity, property_spec)

        # Retrieve properties from server and update entity
        obj_contents = self.sc.propertyCollector.RetrieveProperties(specSet=pfs)

        views = []
        for obj_content in obj_contents:
            logger.debug("In find_entity_view with object of type %s" % obj_content.obj.__class__.__name__)
            obj_content.obj.update_view_data(properties=properties)
            views.append(obj_content.obj)

        return views

    def find_entity_view(self, view_type, begin_entity=None, filter={},
                         properties=None):
        """Find a ManagedEntity of the requested type.

        Traverses the MOB looking for an entity matching the filter.

        :param view_type: The type of ManagedEntity to find.
        :type view_type: str
        :param begin_entity: The MOR to start searching for the entity. \
        The default is to start the search at the root folder.
        :type begin_entity: ManagedObjectReference or None
        :param filter: Key/value pairs to filter the results. The key is \
        a valid parameter of the ManagedEntity type. The value is what \
        that parameter should match.
        :type filter: dict
        :returns: If an entity is found, a ManagedEntity matching the search.
        :rtype: ManagedEntity

        """
        if properties is None:
            properties = []

        kls = classmapper(view_type)
        # Start the search at the root folder if no begin_entity was given
        if not begin_entity:
            begin_entity = self.sc.rootFolder.mo_ref
            logger.debug("Using %s" % self.sc.rootFolder.mo_ref)

        property_spec = soap.create(self.client, 'PropertySpec')
        property_spec.type = view_type
        property_spec.all = False
        property_spec.pathSet = filter.keys()

        pfs = self.get_search_filter_spec(begin_entity, property_spec)

        # Retrieve properties from server and update entity
        #obj_contents = self.propertyCollector.RetrieveProperties(specSet=pfs)
        obj_contents = self.sc.propertyCollector.RetrieveProperties(specSet=pfs)

        # TODO: Implement filtering
        if not filter:
            print('WARNING: No filter specified, returning first match.')
            # If no filter is specified we just return the first item
            # in the list of returned objects
            logger.debug("Creating class in find_entity_view (filter)")
            view = kls(obj_contents[0].obj, self)
            logger.debug("Completed creating class in find_entity_view (filter)")
            view.update_view_data(properties)
            return view

        matched = False
        # Iterate through obj_contents retrieved
        for obj_content in obj_contents:
            # If there are is no propSet, skip this one
            if not obj_content.propSet:
                continue

            # Iterate through each property in the set
            for prop in obj_content.propSet:
                # If the property name is in the defined filter
                if prop.name in filter:
                    # ...and it matches the value specified
                    # TODO: Regex this?
                    if prop.val == filter[prop.name]:
                        # We've found a match
                        filtered_obj_content = obj_content
                        matched = True
                        break

            # If we've matched something at this point, finish the loop
            if matched:
                break

        if not matched:
            # There were no matches
            raise ObjectNotFoundError("No matching objects for filter")

        logger.debug("Creating class in find_entity_view")
        view = kls(filtered_obj_content.obj.mo_ref, self)
        logger.debug("Completed creating class in find_entity_view")
        view.update_view_data(properties=properties)
        return view
