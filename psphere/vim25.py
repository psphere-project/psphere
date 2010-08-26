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
import psphere.soap

class Vim(object):
    def __init__(self, url, username, password):
        self.vsoap = psphere.soap.VimSoap(url)
        self.service_instance = ServiceInstance(vim=self)
        self.vsoap.invoke('Login',
                          _this=self.service_instance.content.sessionManager,
                          userName=username, password=password)

    def get_mo_view(self, mor, properties=None):
        """Get a local view of a single managed object.

        Parameters
        ----------
        mor : ManagedObjectReference
            The ManagedObjectReference to the managed object that
            a view is to be retrieved for.
        properties : list of str's
            The properties to retrieve in the view.

        Returns
        -------
        entity : instance (ManagedObject subclass)
            A local instance of the server-side managed object.

        Notes
        -----
        A view is a local, static representation of a managed object in
        the inventory. The view is not automatically synchronised with 
        the server-side object and can therefore be out of date a moment
        after it is retrieved.
        
        Retrieval of only the properties you intend to use -- through
        the use of the properties parameter -- is considered best
        practise as the properties of some managed objects can be
        costly to retrieve.

        """

        entity = eval(str(mor._type))(mor=mor, vim=self)
        entity.update_view_data(properties=properties)
        return entity

    def get_mo_views(self, mors, properties=None):
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
        get_mo_view : Get the view for a single managed object.

        """
        property_spec = self.vsoap.create_object('PropertySpec')
        # FIXME: Makes assumption about mors being a list
        property_spec.type = str(mors[0]._type)
        if properties:
            property_spec.all = False
            property_spec.pathSet = properties
        else:
            property_spec.all = True

        object_specs = []
        for mor in mors:
            object_spec = self.vsoap.create_object('ObjectSpec')
            object_spec.obj = mor
            object_specs.append(object_spec)

        pfs = self.vsoap.create_object('PropertyFilterSpec')
        pfs.propSet = [property_spec]
        pfs.objectSet = object_specs

        pc_mor = self.service_instance.content.propertyCollector
        property_collector = PropertyCollector(mor=pc_mor, vim=self)
 
        object_contents = property_collector.retrieve_properties(spec_set=pfs)
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
        
    def get_property_spec(self):
        """Return a PropertySpec for matching the class this is called from."""
        property_spec = self.vim.vsoap.create_object('PropertySpec')
        property_spec.all = True
        property_spec.type = self.mor._type

        return property_spec

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
            selection_spec = self.vsoap.create_object('SelectionSpec')
            selection_spec.name = ss_string
            selection_specs.append(selection_spec)

        # A traversal spec for deriving ResourcePool's from found VMs
        rpts = self.vsoap.create_object('TraversalSpec')
        rpts.name = 'resource_pool_traversal_spec'
        rpts.type = 'ResourcePool'
        rpts.path = 'resourcePool'
        rpts.selectSet = [selection_specs[0], selection_specs[1]]

        # A traversal spec for deriving ResourcePool's from found VMs
        rpvts = self.vsoap.create_object('TraversalSpec')
        rpvts.name = 'resource_pool_vm_traversal_spec'
        rpvts.type = 'ResourcePool'
        rpvts.path = 'vm'

        crrts = self.vsoap.create_object('TraversalSpec')
        crrts.name = 'compute_resource_rp_traversal_spec'
        crrts.type = 'ComputeResource'
        crrts.path = 'resourcePool'
        crrts.selectSet = [selection_specs[0], selection_specs[1]]

        crhts = self.vsoap.create_object('TraversalSpec')
        crhts.name = 'compute_resource_host_traversal_spec'
        crhts.type = 'ComputeResource'
        crhts.path = 'host'
         
        dhts = self.vsoap.create_object('TraversalSpec')
        dhts.name = 'datacenter_host_traversal_spec'
        dhts.type = 'Datacenter'
        dhts.path = 'hostFolder'
        dhts.selectSet = [selection_specs[2]]

        dvts = self.vsoap.create_object('TraversalSpec')
        dvts.name = 'datacenter_vm_traversal_spec'
        dvts.type = 'Datacenter'
        dvts.path = 'vmFolder'
        dvts.selectSet = [selection_specs[2]]

        hvts = self.vsoap.create_object('TraversalSpec')
        hvts.name = 'host_vm_traversal_spec'
        hvts.type = 'HostSystem'
        hvts.path = 'vm'
        hvts.selectSet = [selection_specs[2]]
      
        fts = self.vsoap.create_object('TraversalSpec')
        fts.name = 'folder_traversal_spec'
        fts.type = 'Folder'
        fts.path = 'childEntity'
        fts.selectSet = [selection_specs[2], selection_specs[3],
                          selection_specs[4], selection_specs[5],
                          selection_specs[6], selection_specs[7],
                          selection_specs[1]]

        obj_spec = self.vsoap.create_object('ObjectSpec')
        obj_spec.obj = begin_entity
        obj_spec.selectSet = [fts, dvts, dhts, crhts, crrts,
                               rpts, hvts, rpvts]

        pfs = self.vsoap.create_object('PropertyFilterSpec')
        pfs.propSet = [property_spec]
        pfs.objectSet = [obj_spec]
        return pfs

    def find_entity_view(self, view_type, begin_entity=None, filter=None):
        """Traverse the MOB looking for an entity matching the filter.

        Parameters
        ----------
        view_type : str
            The type of entity to find.
        begin_entity : ManagedObjectReference
            If specified, the traversal is started at this MOR. If not
            specified the search is started at the root folder.
        filter : dict
            Key/value pairs to filter the results. The key refers to a
            valid member of the `entity_type` parameter and the value
            is the `str` that the member should match.

        Returns
        -------
        view : Instance of an object derived from ManagedObject

        """
        view_types = ['ClusterComputeResource', 'ComputeResource',
                      'Datacenter', 'Folder', 'HostSystem',
                      'ResourcePool', 'VirtualMachine']

        if view_type not in view_types:
            print('Invalid view type specified.')
            return None

        # Start at the root folder if no begin_entity was specified
        if not begin_entity:
            begin_entity = self.service_instance.content.rootFolder

        property_spec = self.vsoap.create_object('PropertySpec')
        # TODO: Implement filtering
        property_spec.all = False
        property_spec.type = view_type
        property_spec.pathSet = filter.keys()
        pfs = self.get_search_filter_spec(begin_entity, property_spec)
        pc_mor = self.service_instance.content.propertyCollector
        property_collector = PropertyCollector(mor=pc_mor, vim=self)

        # Retrieve properties from server and update entity
        obj_contents = property_collector.retrieve_properties(spec_set=pfs)
        view = eval(view_type)(mor=obj_contents[0].obj, vim=self)
        view.update_view_data(properties=filter.keys())

        return view

class ServiceInstance(object):
    def __init__(self, vim):
        self.vim = vim
        self.mor = psphere.soap.ManagedObjectReference(type='ServiceInstance',
                                                       value='ServiceInstance')
        self.content = self.vim.vsoap.invoke('RetrieveServiceContent',
                                             _this=self.mor)

    def current_time(self):
        return self.vim.vsoap.invoke('CurrentTime', _this=self.mor)

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

    def get_property_filter_spec(self, mor):
        """Create a PropertyFilterSpec for matching the current class.
        
        Called from derived classes, it's a simple way of creating
        a PropertySpec that will match the type of object that the
        method is called from. It returns a List, which is what
        PropertyFilterSpec expects.

        Returns:
            A list of one PropertySpec
        """
        property_spec = self.vim.vsoap.create_object('PropertySpec')
        property_spec.all = True
        property_spec.type = self.mor._type

        object_spec = self.vim.vsoap.create_object('ObjectSpec')
        object_spec.obj = mor

        property_filter_spec = self.vim.vsoap.create_object('PropertyFilterSpec')
        property_filter_spec.propSet = [property_spec]
        property_filter_spec.objectSet = [object_spec]

        return property_filter_spec

    def update_view_data(self, properties=None):
        """Update the local object from the server-side object."""
        pfs = self.get_property_filter_spec(self.mor)
        if properties:
            pfs.propSet[0].all = False
            pfs.propSet[0].pathSet = properties

        pc_mor = self.vim.service_instance.content.propertyCollector
        property_collector = PropertyCollector(mor=pc_mor, vim=self.vim)
        object_contents = property_collector.retrieve_properties(spec_set=pfs)
        if not object_contents:
            # TODO: Improve error checking and reporting
            print('The view could not be updated.')
        for object_content in object_contents:
            self.set_view_data(object_content, properties)

    def update_view_all(self):
        """Update all properties of this view."""
        # TODO: Implement a method which updates all properties in one go
        pass

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
            if len(props[prop]) == 0:
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
                    
    def wait_for_task(self, task_mor):
        """Execute a task and wait for it to complete."""
        task_view = self.vim.get_mo_view(mor=task_mor, properties=['info'])
        result = {}
        while True:
            if task_view.info.state == 'success':
                result['error_message'] = None
                return result
            elif task_view.info.state == 'error':
                # TODO: Handle error checking properly
                result['error_message'] = task_view.info.error.localizedMessage
                return result

            # TODO: Implement progresscallbackfunc
            time.sleep(2)
            task_view.update_view_data(properties=['info'])

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

    def create_folder(self, name):
        """Create a new folder with the specified name.
        Arguments:
            name: The name of the folder to create.
        Returns:
            The newly created Folder object or None if an error was encountered.

        """
        result = self.vim.vsoap.invoke('CreateFolder', _this=self.mor,
                                       name=name)
        if not result:
            return None
        else:
            return Folder(mor=result, vim=self.vim)

    def create_vm(self, config, pool):
        result = self.wait_for_task(self.create_vm_task(config, pool))
        return result

    def create_vm_task(self, config, pool):
        return self.vim.vsoap.invoke('CreateVM_Task', _this=self.mor, config=config, pool=pool)
        
class PropertyCollector(ManagedObject):
    def __init__(self, mor, vim):
        ManagedObject.__init__(self, mor=mor, vim=vim)
        self.filter = None

    def retrieve_properties(self, spec_set):
        return self.vim.vsoap.invoke('RetrieveProperties', _this=self.mor,
                                     specSet=spec_set)

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

