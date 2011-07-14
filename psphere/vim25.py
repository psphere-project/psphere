# Copyright 2010 Jonathan Kinred
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at:
# 
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import time

from psphere.soap import VimSoap, ManagedObjectReference


class ObjectNotFoundError(Exception):
    pass

class TaskFailed(Exception):
    pass


class Vim(object):
    def __init__(self, url, auto_populate=True, debug=False):
        self.debug = debug
        if self.debug:
            import logging
            logging.basicConfig(level=logging.INFO)
            logging.getLogger('suds.client').setLevel(logging.DEBUG)
        self.auto_populate = auto_populate
        self.vsoap = VimSoap(url)
        self.service_instance = ManagedObjectReference(_type='ServiceInstance',
                                                       value='ServiceInstance')
        self.service_content = self.vsoap.invoke('RetrieveServiceContent',
                                                 _this=self.service_instance)
        self.property_collector = self.service_content.propertyCollector

    def login(self, username, password):
        self.vsoap.invoke('Login', _this=self.service_content.sessionManager,
                          userName=username, password=password)

    def logout(self):
        self.vsoap.invoke('Logout', _this=self.service_content.sessionManager)

    def invoke(self, method, _this, **kwargs):
        if issubclass(_this.__class__, ManagedObject):
            _this = _this.mo_ref

        result = self.vsoap.invoke(method, _this=_this, **kwargs)
        return result

    def create_object(self, type_, **kwargs):
        """Create a SOAP object of the requested type."""
        obj =  self.vsoap.create(type_)
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
        kls = classmapper(mo_ref._type)
        view = kls(mo_ref=mo_ref, vim=self)
        # Update the instance with the data in object_content
        view.update_view_data(properties=properties)

        return view

    def get_views(self, mo_refs, properties=None):
        """Get a list of local view's for multiple managed objects.

        Parameters
        ----------
        mo_refs : ManagedObjectReference
            The list of ManagedObjectReference's that views are to
            be created for.
        properties : list
            The properties to retrieve in the views.

        Returns
        -------
        entities : list of instances (ManagedObject subclasses)
            A list of local instances representing the server-side
            managed objects.

        See also
        --------
        get_view : Get the view for a single managed object.

        """
        property_spec = self.create_object('PropertySpec')
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
            object_spec = self.create_object('ObjectSpec')
            object_spec.obj = mo_ref
            object_specs.append(object_spec)

        pfs = self.create_object('PropertyFilterSpec')
        pfs.propSet = [property_spec]
        pfs.objectSet = object_specs

        object_contents = self.invoke('RetrieveProperties',
                                      _this=self.property_collector,
                                      specSet=pfs)
        views = []
        for object_content in object_contents:
            # Instantiate the class in the obj_content
            view = eval(str(object_content.obj._type))(mo_ref=object_content.obj,
                                                       vim=self)
            # Update the instance with the data in object_content
            view.set_view_data(object_content=object_content)
            views.append(view)

        return views
        
    def get_search_filter_spec(self, begin_entity, property_spec):
        """Build a PropertyFilterSpec capable of full inventory traversal.
        
        By specifying all valid traversal specs we are creating a PFS that
        can recursively select any object under the given enitity.

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
            self.create_object('SelectionSpec', name=ss_string)
            for ss_string in ss_strings
        ]

        # A traversal spec for deriving ResourcePool's from found VMs
        rpts = self.create_object('TraversalSpec')
        rpts.name = 'resource_pool_traversal_spec'
        rpts.type = 'ResourcePool'
        rpts.path = 'resourcePool'
        rpts.selectSet = [selection_specs[0], selection_specs[1]]

        # A traversal spec for deriving ResourcePool's from found VMs
        rpvts = self.create_object('TraversalSpec')
        rpvts.name = 'resource_pool_vm_traversal_spec'
        rpvts.type = 'ResourcePool'
        rpvts.path = 'vm'

        crrts = self.create_object('TraversalSpec')
        crrts.name = 'compute_resource_rp_traversal_spec'
        crrts.type = 'ComputeResource'
        crrts.path = 'resourcePool'
        crrts.selectSet = [selection_specs[0], selection_specs[1]]

        crhts = self.create_object('TraversalSpec')
        crhts.name = 'compute_resource_host_traversal_spec'
        crhts.type = 'ComputeResource'
        crhts.path = 'host'
         
        dhts = self.create_object('TraversalSpec')
        dhts.name = 'datacenter_host_traversal_spec'
        dhts.type = 'Datacenter'
        dhts.path = 'hostFolder'
        dhts.selectSet = [selection_specs[2]]

        dvts = self.create_object('TraversalSpec')
        dvts.name = 'datacenter_vm_traversal_spec'
        dvts.type = 'Datacenter'
        dvts.path = 'vmFolder'
        dvts.selectSet = [selection_specs[2]]

        hvts = self.create_object('TraversalSpec')
        hvts.name = 'host_vm_traversal_spec'
        hvts.type = 'HostSystem'
        hvts.path = 'vm'
        hvts.selectSet = [selection_specs[2]]
      
        fts = self.create_object('TraversalSpec')
        fts.name = 'folder_traversal_spec'
        fts.type = 'Folder'
        fts.path = 'childEntity'
        fts.selectSet = [selection_specs[2], selection_specs[3],
                          selection_specs[4], selection_specs[5],
                          selection_specs[6], selection_specs[7],
                          selection_specs[1]]

        obj_spec = self.create_object('ObjectSpec')
        obj_spec.obj = begin_entity
        obj_spec.selectSet = [fts, dvts, dhts, crhts, crrts,
                               rpts, hvts, rpvts]

        pfs = self.create_object('PropertyFilterSpec')
        pfs.propSet = [property_spec]
        pfs.objectSet = [obj_spec]
        return pfs

    def invoke_task(self, method, **kwargs):
        """Execute a task and wait for it to complete."""
        # Don't execute methods which don't return a Task object
        if not method.endswith('_Task'):
            print('ERROR: invoke_task can only be used for methods which '
                  'return a ManagedObjectReference to a Task.')
            return None

        task_mo_ref = self.invoke(method=method, **kwargs)
        task = Task(mo_ref=task_mo_ref, vim=self)
        task.update_view_data(properties=['info'])
        # TODO: This returns true when there is an error
        while True:
            if task.info.state == 'success':
                return task
            elif task.info.state == 'error':
                # TODO: Handle error checking properly
                raise TaskFailed(task.info.error.localizedMessage)

            # TODO: Implement progresscallbackfunc
            # Sleep two seconds and then refresh the data from the server
            time.sleep(2)
            task.update_view_data(properties=['info'])

    def find_entity_list(self, view_type, begin_entity=None, properties=[]):
        """
        Return a list of entities of the given type.

        Parameters
        ----------
        view_type : str
            The object for which we are retrieving the view.
        begin_entity : ManagedObjectReference
            If specified, the traversal is started at this MOR. If not
            specified the search is started at the root folder.
        """
        kls = classmapper(view_type)
        # Start the search at the root folder if no begin_entity was given
        if not begin_entity:
            begin_entity = self.service_content.rootFolder

        property_spec = self.create_object('PropertySpec')
        property_spec.type = view_type
        property_spec.all = False
        property_spec.pathSet = properties

        pfs = self.get_search_filter_spec(begin_entity, property_spec)

        # Retrieve properties from server and update entity
        obj_contents = self.invoke('RetrieveProperties',
                                   _this=self.property_collector,
                                   specSet=pfs)

        views = []
        for obj_content in obj_contents:
            view = kls(mo_ref=obj_content.obj, vim=self)
            view.update_view_data(properties=properties)
            views.append(view)

        return views

    def find_entity_view(self, view_type, begin_entity=None, filter={},
                         properties=[]):
        """Return a new instance based on the search filter.

        Traverses the MOB looking for an entity matching the filter.

        Parameters
        ----------
        view_type : str
            The object for which we are retrieving the view.
        begin_entity : ManagedObjectReference
            If specified, the traversal is started at this MOR. If not
            specified the search is started at the root folder.
        filter : dict
            Key/value pairs to filter the results. The key is a valid
            parameter of the object type. The value is what that
            parameter should match.

        Returns
        -------
        object : object
            A new instance of the requested object.

        """
        kls = classmapper(view_type)
        # Start the search at the root folder if no begin_entity was given
        if not begin_entity:
            begin_entity = self.service_content.rootFolder

        property_spec = self.create_object('PropertySpec')
        property_spec.type = view_type
        property_spec.all = False
        property_spec.pathSet = filter.keys()

        pfs = self.get_search_filter_spec(begin_entity, property_spec)

        # Retrieve properties from server and update entity
        obj_contents = self.invoke('RetrieveProperties',
                                   _this=self.property_collector,
                                   specSet=pfs)

        # TODO: Implement filtering
        if not filter:
            print('WARNING: No filter specified, returning first match.')
            # If no filter is specified we just return the first item
            # in the list of returned objects
            view = kls(mo_ref=obj_contents[0].obj, vim=self)
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
            raise ObjectNotFoundError(error="No matching objects for filter")

        view = kls(mo_ref=filtered_obj_content.obj, vim=self)
        view.update_view_data(properties=properties)
        return view


class ServiceInstance(object):
    def __init__(self):
        self.capability = None
        self.content = None
        self.serverClock = None


class ManagedObject(object):
    """The base class which all managed object's derive from."""
    def __init__(self, mo_ref, vim):
        """Create a new instance.
        
        Parameters
        ----------
        mo_ref : ManagedObjectReference
            The managed object reference used to create this instance
        vim: Vim
            A reference back to the Vim object, which we use to make calls

        """
        self.mo_ref = mo_ref
        self.vim = vim

    def update_view_data(self, properties=None):
        """Update the local object from the server-side object."""
        property_spec = self.vim.create_object('PropertySpec')
        property_spec.type = str(self.mo_ref._type)
        if not properties and self.vim.auto_populate:
            property_spec.all = True
        else:
            property_spec.all = False
            property_spec.pathSet = properties

        object_spec = self.vim.create_object('ObjectSpec')
        object_spec.obj = self.mo_ref

        pfs = self.vim.create_object('PropertyFilterSpec')
        pfs.propSet = [property_spec]
        pfs.objectSet = [object_spec]

        object_contents = self.vim.invoke('RetrieveProperties',
                                          _this=self.vim.property_collector,
                                          specSet=pfs)
        if not object_contents:
            # TODO: Improve error checking and reporting
            print('The view could not be updated.')
        for object_content in object_contents:
            self.set_view_data(object_content)

    def set_view_data(self, object_content):
        """Update the local object from the passed in list."""
        # This is a debugging entry that allows one to view the
        # ObjectContent that this instance was created from
        self._object_content = object_content
        for dynprop in object_content.propSet:
            # If the class hasn't defined the property, don't use it
            if dynprop.name not in dir(self):
                print('WARNING: Skipping undefined property "%s" '
                      'with value "%s"' % (dynprop.name, dynprop.val))
                continue

            if not len(dynprop.val):
                if self.vim.debug:
                    print('DEBUG: Skipping %s with empty value' % dynprop.name)
                continue

            # Values which contain classes starting with Array need
            # to be converted into a nicer Python list
            if dynprop.val.__class__.__name__.startswith('Array'):
                # suds returns a list containing a single item, which
                # is another list. Use the first item which is the real list
                setattr(self, dynprop.name, dynprop.val[0])
            else:
                setattr(self, dynprop.name, dynprop.val)


class ExtensibleManagedObject(ManagedObject):
    def __init__(self, mo_ref, vim):
        # Set the properties for this object
        self.availableField = []
        self.value = []
        # Init the base class
        ManagedObject.__init__(self, mo_ref, vim)


class ManagedEntity(ExtensibleManagedObject):
    def __init__(self, mo_ref, vim):
        self.alarmActionsEnabled = []
        self.configIssue = []
        self.configStatus = None
        self.customValue = []
        self.declaredAlarmState = []
        self.disabledMethod = None
        self.effectiveRole = []
        self.name = None
        self.overallStatus = None
        self.parent = None
        self.permission = []
        self.recentTask = []
        self.tag = []
        self.triggeredAlarmState = []
        ExtensibleManagedObject.__init__(self, mo_ref=mo_ref, vim=vim)

    def find_datacenter(self, parent=None):
        """Find the datacenter which this ManagedEntity belongs to."""
        # If the parent hasn't been set, use the parent of the
        # calling instance, if it exists
        if not parent:
            if not self.parent:
                raise ObjectNotFoundError('No parent found for this instance')

            # Establish the type of object we need to create
            kls = classmapper(self.parent._type)
            parent = kls(mo_ref=self.parent, vim=self.vim)
            parent.update_view_data(properties=['name', 'parent'])

        if not parent.__class__.__name__ == 'Datacenter':
            # Create an instance of the parent class
            kls = classmapper(parent.parent._type)
            next_parent = kls(mo_ref=parent.parent, vim=self.vim)
            next_parent.update_view_data(properties=['name', 'parent'])
            # ...and recursively call this method
            parent = self.find_datacenter(parent=next_parent)

        if parent.__class__.__name__ == 'Datacenter':
            return parent
        else:
            raise ObjectNotFoundError('No parent found for this instance')


class Alarm(ExtensibleManagedObject):
    def __init__(self, mo_ref, vim):
        self.info = None
        ExtensibleManagedObject.__init__(self, mo_ref=mo_ref, vim=vim)


class AlarmManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.defaultExpression = []
        self.description = None
        ManagedObject.__init__(self, mo_ref, vim)


class AuthorizationManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.description = None
        self.privilege_list = []
        self.role_list = []
        ManagedObject.__init__(self, mo_ref, vim)


class ComputeResource(ManagedEntity):
    def __init__(self, mo_ref, vim):
        self.configurationEx = None
        self.datastore = []
        self.environmentBrowser = None
        self.host = []
        self.network = []
        self.resourcePool = None
        self.summary = None
        ManagedEntity.__init__(self, mo_ref, vim)

    def find_datastore(self, name):
        if not self.datastore:
            self.update_view_data(self.datastore)

        datastores = self.vim.get_views(self.datastore, properties=['summary'])
        for datastore in datastores:
            if datastore.summary.name == name:
                if self.vim.auto_populate:
                    datastore.update_view_data()
                return datastore

        raise ObjectNotFoundError(error='No datastore matching %s' % name)


class ClusterComputeResource(ComputeResource):
    def __init__(self, mo_ref, vim):
        self.actionHistory = []
        self.configuration = None
        self.drsFault = []
        self.drsRecommendation = []
        self.migrationHistory = []
        self.recommendation = []
        ComputeResource.__init__(self, mo_ref, vim)


class Datacenter(ManagedEntity):
    def __init__(self, mo_ref, vim):
        self.datastore = []
        self.datastoreFolder = None
        self.hostFolder = None
        self.network = []
        self.networkFolder = None
        self.vmFolder = None
        ManagedEntity.__init__(self, mo_ref, vim)


class Datastore(ManagedEntity):
    def __init__(self, mo_ref, vim):
        self.browser = None
        self.capability = None
        self.host = []
        self.info = None
        self.summary = None
        self.vm = []
        ManagedEntity.__init__(self, mo_ref, vim)


class Folder(ManagedEntity):
    def __init__(self, mo_ref, vim):
        self.childEntity = []
        self.childType = []
        ManagedEntity.__init__(self, mo_ref=mo_ref, vim=vim)


class HostSystem(ManagedEntity):
    def __init__(self, mo_ref, vim):
        self.capability = None
        self.config = None
        self.configManager = None
        self.datastore = []
        self.datastoreBrowser = None
        self.hardware = None
        self.network = []
        self.runtime = None
        self.summary = None
        self.systemResources = None
        self.vm = []
        ManagedEntity.__init__(self, mo_ref, vim)


class Network(ManagedEntity):
    def __init__(self, mo_ref, vim):
        self.host = []
        self.summary = None
        self.vm = []
        ManagedEntity.__init__(self, mo_ref, vim)


class PropertyCollector(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.filter = None
        ManagedObject.__init__(self, mo_ref=mo_ref, vim=vim)


class ResourcePool(ManagedEntity):
    def __init__(self, mo_ref, vim):
        self.config = None
        self.owner = None
        self.resource_pool = []
        self.runtime = None
        self.summary = None
        self.vm = []
        ManagedEntity.__init__(self, mo_ref=mo_ref, vim=vim)


class Task(ExtensibleManagedObject):
    def __init__(self, mo_ref, vim):
        self.info = None
        ExtensibleManagedObject.__init__(self, mo_ref=mo_ref, vim=vim)


class VirtualMachine(ManagedEntity):
    def __init__(self, mo_ref, vim):
        self.capability = None
        self.config = None
        self.datastore = []
        self.environmentBrowser = None
        self.guest = None
        self.guestHeartbeatStatus = None
        self.layout = None
        self.layoutEx = None
        self.network = []
        self.resourceConfig = None
        self.resourcePool = None
        self.runtime = None
        self.snapshot = None
        self.storage = None
        self.summary = None
        ManagedEntity.__init__(self, mo_ref, vim)


classmap = dict((x.__name__, x) for x in (
    ClusterComputeResource,
    ComputeResource,
    Datacenter,
    Datastore,
    Folder,
    HostSystem,
    Network,
    ResourcePool,
    VirtualMachine,
))


def classmapper(name):
    return classmap[name]
