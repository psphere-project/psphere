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

"""
Contains client side classes representing the server
side managed objects.
"""

import time
from suds.sudsobject import Object
from psphere.mor import ManagedObjectReference

class ManagedObject(object):
    """The base class which all managed object's derive from."""
    def __init__(self, mo_ref, vim):
        self.mo_ref = mo_ref
        self.vim = vim
        self.properties = {}

    def get_property_filter_spec(self, mo_ref):
        """Create a PropertyFilterSpec for matching the current class.
        
        Called from derived classes, it's a simple way of creating
        a PropertySpec that will match the type of object that the
        method is called from. It returns a List, which is what
        PropertyFilterSpec expects.

        Returns:
            A list of one PropertySpec
        """
        property_spec = self.vim.create_object('PropertySpec')
        property_spec.all = True
        property_spec.type = self.mo_ref._type

        object_spec = self.vim.create_object('ObjectSpec')
        object_spec.obj = mo_ref

        property_filter_spec = self.vim.create_object('PropertyFilterSpec')
        property_filter_spec.propSet = [property_spec]
        property_filter_spec.objectSet = [object_spec]

        return property_filter_spec

    def update_view_data(self, properties=None):
        """Synchronise the local object with the server-side object."""
        pfs = self.get_property_filter_spec(self.mo_ref)
        # TODO: Use the properties argument to filter relevant props
        obj_contents = self.vim.vim_service.RetrieveProperties(
            _this=self.vim.service_content.propertyCollector, specSet=pfs)
        for entity in obj_contents:
            self.set_view_data(entity, properties)

    def set_view_data(self, entity, properties=None):
        """Set the objects properties from the ObjectContent propSet."""
        for dyn_prop in entity.propSet:
            if properties and (dyn_prop.name in properties):
                self.properties[dyn_prop.name] = dyn_prop.val
            else:
                self.properties[dyn_prop.name] = dyn_prop.val

    def invoke(self, method, **kwargs):
        return eval('self.vim_service.%s' % method)(_this=self.mo_ref, **kwargs)

    def wait_for_task(self, task_ref):
        """Execute a task and wait for it to complete."""
        task_view = self.vim.get_view(mo_ref=task_ref)
        while True:
            info = task_view.info
            if info.state.val == 'success':
                return info.result
            elif info.state.val == 'error':
                # TODO: Handle error checking properly
                fault = {}
                fault['name'] = info.error.fault
                fault['detail'] = info.error.fault
                fault['error_message'] = info.error.localizedMessage
                return fault
            else:
                print('Unknown state val')

            # TODO: Implement progresscallbackfunc
            time.sleep(2)
            task_view.update_view_data()

class ExtensibleManagedObject(ManagedObject):
    def __init__(self, mo_ref, vim):
        ManagedObject.__init__(self, mo_ref, vim)

class ManagedEntity(ExtensibleManagedObject):
    def __init__(self, mo_ref, vim):
        ExtensibleManagedObject.__init__(self, mo_ref, vim)
        self.alarmActionsEnabled = None
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

    def get_search_filter_spec(self, mo_ref, property_spec):
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
            selection_spec = self.vim.create_object('SelectionSpec')
            selection_spec.name = ss_string
            selection_specs.append(selection_spec)

        # A traversal spec for deriving ResourcePool's from found VMs
        rpts = self.vim.create_object('TraversalSpec')
        rpts.name = 'resource_pool_traversal_spec'
        rpts.type = 'ResourcePool'
        rpts.path = 'resourcePool'
        rpts.select_set = [selection_specs[0], selection_specs[1]]

        # A traversal spec for deriving ResourcePool's from found VMs
        rpvts = self.vim.create_object('TraversalSpec')
        rpvts.name = 'resource_pool_vm_traversal_spec'
        rpvts.type = 'ResourcePool'
        rpvts.path = 'vm'

        crrts = self.vim.create_object('TraversalSpec')
        crrts.name = 'compute_resource_rp_traversal_spec'
        crrts.type = 'ComputeResource'
        crrts.path = 'resourcePool'
        crrts.select_set = [selection_specs[0], selection_specs[1]]
   
        crhts = self.vim.create_object('TraversalSpec')
        crhts.name = 'compute_resource_host_traversal_spec'
        crhts.type = 'ComputeResource'
        crhts.path = 'host'
         
        dhts = self.vim.create_object('TraversalSpec')
        dhts.name = 'datacenter_host_traversal_spec'
        dhts.type = 'Datacenter'
        dhts.path = 'hostFolder'
        dhts.select_set = [selection_specs[2]]
   
        dvts = self.vim.create_object('TraversalSpec')
        dvts.name = 'datacenter_vm_traversal_spec'
        dvts.type = 'Datacenter'
        dvts.path = 'vmFolder'
        dvts.select_set = [selection_specs[2]]

        hvts = self.vim.create_object('TraversalSpec')
        hvts.name = 'host_vm_traversal_spec'
        hvts.type = 'HostSystem'
        hvts.path = 'vm'
        hvts.select_set = [selection_specs[2]]
      
        fts = self.vim.create_object('TraversalSpec')
        fts.name = 'folder_traversal_spec'
        fts.type = 'Folder'
        fts.path = 'childEntity'
        fts.select_set = [selection_specs[2], selection_specs[3],
                          selection_specs[4], selection_specs[5],
                          selection_specs[6], selection_specs[7],
                          selection_specs[1]]

        obj_spec = self.vim.create_object('ObjectSpec')
        obj_spec.obj = mo_ref
        obj_spec.select_set = [fts, dvts, dhts, crhts, crrts,
                               rpts, hvts, rpvts]
   
        pfs = self.vim.create_object('PropertyFilterSpec')
        pfs.prop_set = property_spec
        pfs.object_set = [obj_spec]
        return pfs

    def set_view_data(self, entity, properties):
        self.vim.foo = entity
        props = {}
        for dyn_prop in entity.propSet:
            # See if we're dealing with a suds Object
            if issubclass(dyn_prop.val, Object):
                # The real list is always found in the first slot
                props[dyn_prop.name] = dyn_prop.val[0]
            else:
                props[dyn_prop.name] = dyn_prop.val

        if 'alarmActionsEnabled' in props:
            self.alarmActionsEnabled = props['alarmActionsEnabled']
        if 'configIssue' in props:
            if isinstance(props['configIssue'], list):
                for ci in props['configIssue']:
                    self.configIssue.append(ci)
            else:
                self.configIssue = props['configIssue']
        self.configStatus = props['configStatus']
        if 'customValue' in props:
            if isinstance(props['customValue'], list):
                for ci in props['customValue']:
                    self.customValue.append(ci)
            else:
                self.customValue = props['customValue']
        for das in props['declaredAlarmState']:
            self.declaredAlarmState.append(das)
        for dm in props['disabledMethod']:
            self.disabledMethod.append(dm)
        for er in props['effectiveRole']:
            self.effectiveRole.append(er)
        self.name = props['name']
        self.overallStatus = props['overallStatus']
        if 'parent' in props:
            self.parent = props['parent']
        for permission in props['permission']:
            self.permission.append(permission)
        for rt in props['recentTask']:
            mo_ref = ManagedObjectReference(rt.value, rt._type)
            self.recentTask.append(mo_ref)
        for tag in props['tag']:
            self.tag.append(tag)
        for tas in props['triggeredAlarmState']:
            self.triggeredAlarmState.append(tas)

class Folder(ManagedEntity):
    def __init__(self, mo_ref, vim):
        ManagedEntity.__init__(self, mo_ref, vim)
        self.childEntity = []
        self.childType = []

    def set_view_data(self, entity, properties):
        ManagedEntity.set_view_data(self, entity, properties)
        props = {}
        for dyn_prop in entity.propSet:
            props[dyn_prop.name] = dyn_prop.val

        for ce in props['childEntity'][0]:
            mo_ref = ManagedObjectReference(ce.value, ce._type)
            self.childEntity.append(mo_ref)

        for ct in props['childType'][0]:
            self.childType.append(ct)

    def CreateFolder(self, name):
        result = self.vim.vim_service.CreateFolder(self.mo_ref, name)
        return result

class PropertyCollector(ManagedObject):
    def __init__(self, mo_ref, vim):
        ManagedObject.__init__(self, mo_ref, vim)

class ServiceInstance(ManagedObject):
    def __init__(self, mo_ref, vim):
        ManagedObject.__init__(self, mo_ref, vim)

    def CurrentTime(self):
        result = self.vim.vim_service.CurrentTime(self.mo_ref)
        return result

    def RetrieveServiceContent(self):
        sc = self.vim.vim_service.RetrieveServiceContent(mo_ref=self.mo_ref)
        return sc

class Datacenter(ManagedEntity):
    def __init__(self, mo_ref, vim):
        ManagedEntity.__init__(self, mo_ref, vim)

#    def set_view_data(self, entity, properties):
#        """Set the properties for the view."""
#        for dyn_prop in entity.propSet:
#                self.datastore = []
#                for datastore in entity.propSet.datastore:
#                    ds = Datastore(datastore, vim)
#                    self.datastore.append(ds)
#
#                self.datastoreFolder = Folder(mo_ref.datastoreFolder, vim)
#                self.datastoreFolder = Folder(mo_ref.hostFolder, vim)
#                self.network = []
#                for network in mo_ref.network:
#                    n = Network(network, vim)
#                    self.network.append(n)
#
#                self.networkFolder = Folder(mo_ref.networkFolder, vim)
#                self.vmFolder = Folder(mo_ref.vmFolder, vim)


    def PowerOnMultiVM_Task(self, vm):
        """Powers on multiple VMs in a data center.

        Arguments:
            vm:     ManagedObjectReference[] to a VirtualMachine[]
                    The virtual machines to power on.
        """

        response = self.invoke('PowerOnMultiVM_Task', vm)
        return response

    def PowerOnMultiVM(self, vm):
        return self.wait_for_task(self.PowerOnMultiVM_Task(vm))

class VirtualMachine(ManagedEntity):
    def __init__(self, mo_ref, vim):
        ManagedEntity.__init__(self, mo_ref, vim)

class ComputeResource(ManagedEntity):
    def __init__(self, mo_ref, vim):
        ManagedEntity.__init__(self, mo_ref, vim)

class ClusterComputeResource(ComputeResource):
    def __init__(self, mo_ref, vim):
        ComputeResource.__init__(self, mo_ref, vim)

class Datastore(ManagedEntity):
    def __init__(self, mo_ref, vim):
        ManagedEntity.__init__(self, mo_ref, vim)

#    def set_view_data(self, entity, properties=None):
#        self.browser = dyn_prop.
#        for dyn_prop in entity.propSet:
#            if properties and (dyn_prop.name in properties):
#                self.properties[dyn_prop.name] = dyn_prop.val
#            else:
#                self.properties[dyn_prop.name] = dyn_prop.val
