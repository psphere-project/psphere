# Copyright 2010 Jonathan Kinred <jonathan.kinred@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# he Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import time
from psphere.soap import VimSoap, VimFault, ManagedObjectReference

class ObjectNotFoundError(Exception):
    def __init__(self, error):
        self.error = error
    def __str__(self):
        return repr(self.error)

class Vim(object):
    def __init__(self, url, username, password):
        self.vsoap = VimSoap(url)
        self.si = ServiceInstance(vim=self)
        self.sc = self.si.content
        self.pc = PropertyCollector(mor=self.sc.propertyCollector, vim=self)
        self.vsoap.invoke('Login', _this=self.sc.sessionManager,
                          userName=username, password=password)

    def invoke(self, method, **kwargs):
        result = self.vsoap.invoke(method, **kwargs)
        return result

    def create_object(self, type):
        """Create a SOAP object of the requested type."""
        return self.vsoap.create(type)

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

    def get_views(self, mors, properties=None):
        """Get a list of local view's for multiple managed objects.

        Parameters
        ----------
        mors : ManagedObjectReference
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
        # FIXME: Makes assumption about mors being a list
        property_spec.type = str(mors[0]._type)
        if properties:
            property_spec.all = False
            property_spec.pathSet = properties
        else:
            property_spec.all = True

        object_specs = []
        for mor in mors:
            object_spec = self.create_object('ObjectSpec')
            object_spec.obj = mor
            object_specs.append(object_spec)

        pfs = self.create_object('PropertyFilterSpec')
        pfs.propSet = [property_spec]
        pfs.objectSet = object_specs

        object_contents = self.pc.RetrieveProperties(specSet=pfs)
        views = []
        for object_content in object_contents:
            # Instantiate the class in the obj_content
            view = eval(str(object_content.obj._type))(mor=object_content.obj,
                                                       vim=self)
            # Update the instance with the data in object_content
            view.set_view_data(object_content=object_content,
                               properties=properties)
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
        selection_specs = []
        for ss_string in ss_strings:
            selection_spec = self.create_object('SelectionSpec')
            selection_spec.name = ss_string
            selection_specs.append(selection_spec)

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

    def wait_for_task(self, task_mor):
        """Execute a task and wait for it to complete."""
        task = Task(mor=task_mor, vim=self)
        task.update_view_data(properties=['info'])
        result = {}
        # TODO: This returns true when there is an error
        while True:
            if task.info.state == 'success':
                result['error_message'] = None
                return result
            elif task.info.state == 'error':
                # TODO: Handle error checking properly
                result['error_message'] = task.info.error.localizedMessage
                return result

            # TODO: Implement progresscallbackfunc
            # Sleep two seconds and then refresh the data from the server
            time.sleep(2)
            task.update_view_data(properties=['info'])

    def CreateVM(self, **kwargs):
        try:
            result = self.invoke('CreateVM_Task', **kwargs)
        except VimFault:
            raise

        return self.wait_for_task(result)

    def find_entity_view(self, view_type, begin_entity=None, filter=None):
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
            begin_entity = self.sc.rootFolder

        property_spec = self.create_object('PropertySpec')
        property_spec.all = False
        property_spec.type = str(view_type)
        if filter:
            property_spec.pathSet = filter.keys()
        pfs = self.get_search_filter_spec(begin_entity, property_spec)

        # Retrieve properties from server and update entity
        obj_contents = self.pc.RetrieveProperties(specSet=pfs)

        # TODO: Implement filtering
        if not filter:
            print('No filter specified')
            print(obj_contents[0].obj)
            # If no filter is specified we just return the first item
            # in the list of returned objects
            return kls(mor=obj_contents[0].obj, vim=self)

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
                        filtered_obj = obj_content.obj
                        matched = True
                        break

            # If we've matched something at this point, there
            # is no reason to continue
            if matched:
                break

        if matched:
            return kls(mor=filtered_obj, vim=self)
        else:
            # There were no matches
            raise ObjectNotFoundError(error="No matching objects for filter")

class ServiceInstance(object):
    def __init__(self, vim):
        self.vim = vim
        self.mor = ManagedObjectReference(type='ServiceInstance',
                                          value='ServiceInstance')
        self.content = self.vim.vsoap.invoke('RetrieveServiceContent',
                                             _this=self.mor)

class ManagedObject(object):
    """The base class which all managed object's derive from."""
    def __init__(self, mor, vim):
        """Create a new instance.
        
        Parameters
        ----------
        mor : ManagedObjectReference
            The managed object reference used to create this instance
        vim: Vim
            A reference back to the Vim object, which we use to make calls

        """
        self.mor = mor
        self.vim = vim

    def update_view_data(self, properties=None):
        """Update the local object from the server-side object."""
        property_spec = self.vim.create_object('PropertySpec')
        property_spec.type = str(self.mor._type)
        if properties:
            property_spec.all = False
            property_spec.pathSet = properties
        else:
            property_spec.all = True

        object_spec = self.vim.create_object('ObjectSpec')
        object_spec.obj = self.mor

        pfs = self.vim.create_object('PropertyFilterSpec')
        pfs.propSet = [property_spec]
        pfs.objectSet = [object_spec]

        object_contents = self.vim.pc.RetrieveProperties(specSet=pfs)
        if not object_contents:
            # TODO: Improve error checking and reporting
            print('The view could not be updated.')
        for object_content in object_contents:
            self.set_view_data(object_content, properties)

    def set_view_data(self, object_content, properties=None):
        """Update the local object from the passed in obj_content array."""
        self.ent = object_content
        props = {}
        for dyn_prop in object_content.propSet:
            # Kludgy way of finding if the dyn_prop contains a collection
            prop_type = str(dyn_prop.val.__class__)[
                str(dyn_prop.val.__class__).rfind('.')+1:]

            if prop_type.startswith('Array'):
                # We assume it's a collection, the real list is
                # found in the first slot
                props[dyn_prop.name] = dyn_prop.val[0]
            else:
                props[dyn_prop.name] = dyn_prop.val

        for prop in props:
            # We're not interested in empty values
            if not len(props[prop]):
                continue

            # If the property hasn't been initialised in this class
            if prop in dir(self):
                if type(prop) == 'list':
                    for item in props[prop]:
                        vars(self)[prop].append(item)
                else:
                    vars(self)[prop] = props[prop]
            else:
                print('WARNING: Skipping undefined property "%s" '
                      'with value "%s"' % (prop, props[prop]))
                    
class ExtensibleManagedObject(ManagedObject):
    def __init__(self, mor, vim):
        # Init the base class
        ManagedObject.__init__(self, mor, vim)
        # Set the properties for this object
        self.availableField = []
        self.value = []

class ManagedEntity(ExtensibleManagedObject):
    def __init__(self, mor, vim):
        ExtensibleManagedObject.__init__(self, mor=mor, vim=vim)
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

    def find_datacenter(self, parent=None):
        """Find the datacenter which this ManagedEntity belongs to."""
        # If the parent hasn't been set, use the parent of the
        # calling instance, if it exists
        if not parent:
            if self.parent:
                # Establish the type of object we need to create
                kls = classmapper(self.parent._type)
                parent = kls(mor=self.parent, vim=self.vim)
                parent.update_view_data(properties=['name', 'parent'])
            else:
                raise ObjectNotFoundError('No parent found for this instance')

        if not parent.__class__.__name__ == 'Datacenter':
            # Create an instance of the parent class
            kls = classmapper(parent.parent._type)
            next_parent = kls(mor=parent.parent, vim=self.vim)
            next_parent.update_view_data(properties=['name', 'parent'])
            # ...and recursively call this method
            parent = self.find_datacenter(parent=next_parent)

        if parent.__class__.__name__ == 'Datacenter':
            return parent
        else:
            raise ObjectNotFoundError('No parent found for this instance')

class Alarm(ExtensibleManagedObject):
    def __init__(self, mor, vim):
        ExtensibleManagedObject.__init__(self, mor=mor, vim=vim)
        self.info = None
        
class AlarmManager(ManagedObject):
    def __init__(self, mor, vim):
        self.defaultExpression = []
        self.description = None

class AuthorizationManager(ManagedObject):
    def __init__(self, mor, vim):
        ManagedObject.__init__(self, mor, vim)
        self.description = None
        self.privilege_list = []
        self.role_list = []

class Folder(ManagedEntity):
    def __init__(self, mor, vim):
        ManagedEntity.__init__(self, mor=mor, vim=vim)
        self.childEntity = []
        self.childType = []

class PropertyCollector(ManagedObject):
    def __init__(self, mor, vim):
        ManagedObject.__init__(self, mor=mor, vim=vim)
        self.filter = None

    def RetrieveProperties(self, specSet):
        return self.vim.vsoap.invoke('RetrieveProperties', _this=self.mor,
                                     specSet=specSet)

class ComputeResource(ManagedEntity):
    def __init__(self, mor, vim):
        ManagedEntity.__init__(self, mor, vim)
        self.configurationEx = None
        self.datastore = []
        self.environmentBrowser = None
        self.host = []
        self.network = []
        self.resourcePool = None
        self.summary = None

    def find_datastore(self, name):
        if not self.datastore:
            self.update_view_data(self.datastore)

        datastores = self.vim.get_views(self.datastore, properties=['summary'])
        for datastore in datastores:
            if datastore.summary.name == name:
                return datastore

        raise ObjectNotFoundError(error='No datastore matching %s' % name)

class ClusterComputeResource(ComputeResource):
    def __init__(self, mor, vim):
        ComputeResource.__init__(self, mor, vim)
        self.actionHistory = []
        self.configuration = None
        self.drsFault = []
        self.drsRecommendation = []
        self.migrationHistory = []
        self.recommendation = []

class Datacenter(ManagedEntity):
    def __init__(self, mor, vim):
        ManagedEntity.__init__(self, mor, vim)
        self.datastore = []
        # TODO: vSphere API 4.0
        self.datastoreFolder = None
        self.hostFolder = None
        self.network = []
        # TODO: vSphere API 4.0
        self.networkFolder = None
        self.vmFolder = None


    def power_on_multi_vm_task(self, vm):
        """Powers on multiple VMs in a data center.

        Arguments:
            vm:     ManagedObjectReference[] to a VirtualMachine[]
                    The virtual machines to power on.
        """

        response = self.vim.vsoap.invoke('PowerOnMultiVM_Task', vm)
        return response

    def power_on_multi_vm(self, vm):
        return self.wait_for_task(self.PowerOnMultiVM_Task(vm))

class Datastore(ManagedEntity):
    def __init__(self, mor, vim):
        self.browser = None
        self.capability = None
        self.host = []
        self.info = None
        self.summary = None
        self.vm = []

        ManagedEntity.__init__(self, mor, vim)

        def refresh_datastore(self):
            """Explicitly refreshes free-space and capacity values."""
            self.vim.vsoap.invoke('RefreshDatastore', _this=self.mor)
            # Update the view data to get the new values
            self.update_view_data()

        # vSphere API 4.0
        def refresh_datastore_storage_info(self):
            self.vim.vsoap.invoke('RefreshDatastoreStorageInfo',
                                  _this=self.mor)
            # Update the view data to get the new values
            self.update_view_data()

class VirtualMachine(ManagedEntity):
    def __init__(self, mor, vim):
        self.capability = None
        self.config = None
        self.datastore = []
        self.environmentBrowser = None
        self.guest = None
        self.guestHeartbeatStatus = None
        self.layout = None
        # TODO: vSphere API 4.0
        self.layoutEx = None
        self.network = []
        self.resourceConfig = None
        self.resourcePool = None
        self.runtime = None
        self.snapshot = None
        # TODO: vSphere API 4.0
        self.storage = None
        self.summary = None

        ManagedEntity.__init__(self, mor, vim)

    def acquire_mks_ticket(self):
        return self.vim.vsoap.invoke('AcquireMksTicket', _this=self.mor)

    def answer_vm(self, question_id, answer_choice):
        """Responds to a question that is blocking this virtual machine."""
        self.vim.vsoap.invoke('AnswerVM', _this=self.mor,
                              questionId=question_id,
                              answerChoice=answer_choice)

class HostSystem(ManagedEntity):
    def __init__(self, mor, vim):
        ManagedEntity.__init__(self, mor, vim)
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

class Network(ManagedEntity):
    def __init__(self, mor, vim):
        ManagedEntity.__init__(self, mor, vim)
        self.host = []
        self.name = None
        self.summary = None
        self.vm = []

class Task(ExtensibleManagedObject):
    def __init__(self, mor, vim):
        ExtensibleManagedObject.__init__(self, mor=mor, vim=vim)
        self.info = None

    def CancelTask(self):
        pass

    def SetTaskDescription(self, description):
        pass

    def SetTaskState(self, state, result=None, fault=None):
        pass

    def UpdateProgress(self, percentDone):
        pass

class ResourcePool(ManagedEntity):
    def __init__(self, mor, vim):
        ExtensibleManagedObject.__init__(self, mor=mor, vim=vim)
        self.config = None
        self.owner = None
        self.resource_pool = []
        self.runtime = None
        self.summary = None
        self.vm = []

    def CreateChildVM_Task(self, config, host=None):
        pass

    def CreateResourcePool(self, name, spec):
        pass

    def CreateVApp(self, name, resSpec, configSpec, vmFolder=None):
        pass

    def DestroyChildren(self):
        pass

    def ImportVApp(self, spec, folder=None, host=None):
        pass

classmap = {
    'Folder': Folder,
    'ClusterComputeResource': ClusterComputeResource,
    'ComputeResource': ComputeResource,
    'Datacenter': Datacenter,
    'Datastore': Datastore,
    'HostSystem': HostSystem,
    'Network': Network,
    'ResourcePool': ResourcePool,
    'VirtualMachine': VirtualMachine,
}

def classmapper(name):
    return classmap[name]

