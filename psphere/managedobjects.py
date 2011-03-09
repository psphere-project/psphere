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

from psphere.errors import ObjectNotFoundError

class ReadOnlyCachedAttribute(object):
    """Retrieves attribute value from server and caches it in the instance.
    Source: Python Cookbook
    Author: Denis Otkidach http://stackoverflow.com/users/168352/denis-otkidach
    This decorator allows you to create a property which can be computed once
    and accessed many times.
    """
    def __init__(self, method, name=None):
        self.method = method
        self.name = name or method.__name__
        self.__doc__ = method.__doc__

    def __get__(self, inst, cls):
        # If we're being accessed from the class itself, not from an object
        if inst is None:
            print("inst is None")
            return self
        # Else if the attribute already exists, return the existing value
        elif self.name in inst.__dict__:
            print("Using cached value for %s" % self.name)
            return inst.__dict__[self.name]
        # Else, calculate the desired value and set it
        else:
            print("Retrieving and caching value for %s" % self.name)
            # TODO: Check if it's an array or a single value
            result = self.method(inst)
            # Set the object value to desired value
            inst.__dict__[self.name] = result
            return result

    def __set__(self, inst, value):
        raise AttributeError("%s is read-only" % self.name)

    def __delete__(self, inst):
        del inst.__dict__[self.name]


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
                print(dynprop.val.__class__.__name__)
                if (dynprop.val.__class__.__name__ ==
                    'ArrayOfManagedObjectReference'):
                    setattr(self, '_%s' % dynprop.name, dynprop.val[0])
                else:
                    setattr(self, dynprop.name, dynprop.val[0])
            else:
                print("-----------------")
                print(dynprop.val.__class__.__name__)
                print("-----------------")
                # At this point we should walk the entire "tree" and set
                # any MOR's to Python classes
                
                if (dynprop.val.__class__.__name__ in classmap or
                    dynprop.val.__class__.__name__ ==
                    "ManagedObjectReference" or 
                    dynprop.val.__class__.__name__ == "val"):
                    setattr(self, '_%s' % dynprop.name, dynprop.val)
                else:
                    setattr(self, dynprop.name, dynprop.val)


# First list the classes which directly inherit from ManagedObject
class AlarmManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.defaultExpression = []
        self.description = None
        ManagedObject.__init__(self, mo_ref, vim)


class AuthorizationManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.description = None
        self.privilegeList = []
        self.roleList = []
        ManagedObject.__init__(self, mo_ref, vim)


class CustomFieldsManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.field = []
        ManagedObject.__init__(self, mo_ref, vim)


class CustomizationSpecManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.encryptionKey = None
        self.info = []
        ManagedObject.__init__(self, mo_ref, vim)


class DiagnosticManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        ManagedObject.__init__(self, mo_ref, vim)


class DistributedVirtualSwitchManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        ManagedObject.__init__(self, mo_ref, vim)


class EnvironmentBrowser(ManagedObject):
    def __init__(self, mo_ref, vim):
        self._datastoreBrowser = None
        ManagedObject.__init__(self, mo_ref, vim)

    @ReadOnlyCachedAttribute
    def datastoreBrowser(self):
        # TODO: Implement
        pass


class EventManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.description = None
        self.latestEvent = None
        self.maxCollector = None
        ManagedObject.__init__(self, mo_ref, vim)


class ExtensibleManagedObject(ManagedObject):
    def __init__(self, mo_ref, vim):
        # Set the properties for this object
        self.availableField = []
        self.value = []
        ManagedObject.__init__(self, mo_ref, vim)


class Alarm(ExtensibleManagedObject):
    def __init__(self, mo_ref, vim):
        self.info = None
        ExtensibleManagedObject.__init__(self, mo_ref, vim)


class HostCpuSchedulerSystem(ExtensibleManagedObject):
    def __init__(self, mo_ref, vim):
        self.hyperthreadInfo = None
        ExtensibleManagedObject.__init__(self, mo_ref, vim)


class HostFirewallSystem(ExtensibleManagedObject):
    def __init__(self, mo_ref, vim):
        self.firewallInfo = None
        ExtensibleManagedObject.__init__(self, mo_ref, vim)


class HostMemorySystem(ExtensibleManagedObject):
    def __init__(self, mo_ref, vim):
        self.consoleReservationInfo = None
        self.virtualMachineReservationInfo = None
        ExtensibleManagedObject.__init__(self, mo_ref, vim)


class HostNetworkSystem(ExtensibleManagedObject):
    def __init__(self, mo_ref, vim):
        self.capabilites = None
        self.consoleIpRouteConfig = None
        self.dnsConfig = None
        self.ipRouteConfig = None
        self.networkConfig = None
        self.networkInfo = None
        self.offloadCapabilities = None
        ExtensibleManagedObject.__init__(self, mo_ref, vim)


class HostPciPassthruSystem(ExtensibleManagedObject):
    def __init__(self, mo_ref, vim):
        self.pciPassthruInfo = []
        ExtensibleManagedObject.__init__(self, mo_ref, vim)


class HostServiceSystem(ExtensibleManagedObject):
    def __init__(self, mo_ref, vim):
        self.serviceInfo = None
        ExtensibleManagedObject.__init__(self, mo_ref, vim)


class HostStorageSystem(ExtensibleManagedObject):
    def __init__(self, mo_ref, vim):
        self.fileSystemVolumeInfo = None
        self.multipathStateInfo = None
        self.storageDeviceInfo = None
        self.systemFile = None
        ExtensibleManagedObject.__init__(self, mo_ref, vim)


class HostVirtualNicManager(ExtensibleManagedObject):
    def __init__(self, mo_ref, vim):
        self.info = None
        ExtensibleManagedObject.__init__(self, mo_ref, vim)


class HostVMotionSystem(ExtensibleManagedObject):
    def __init__(self, mo_ref, vim):
        self.ipConfig = None
        self.netConfig = None
        ExtensibleManagedObject.__init__(self, mo_ref, vim)


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
        self._parent = None
        self.permission = []
        self._recentTask = []
        self.tag = []
        self.triggeredAlarmState = []
        ExtensibleManagedObject.__init__(self, mo_ref, vim)

    @ReadOnlyCachedAttribute
    def parent(self):
        result = self.vim.get_view(self._parent)
        return result

    @ReadOnlyCachedAttribute
    def recentTask(self):
        result = self.vim.get_views(self._recentTask)
        return result

    def find_datacenter(self, parent=None):
        """Find the datacenter which this ManagedEntity belongs to."""
        # If the parent hasn't been set, use the parent of the
        # calling instance, if it exists
        if not parent:
            if not self.parent:
                raise ObjectNotFoundError('No parent found for this instance')

            # Establish the type of object we need to create
            kls = classmapper(self.parent._type)
            parent = kls(self.parent, self.vim)
            parent.update_view_data(properties=['name', 'parent'])

        if not parent.__class__.__name__ == 'Datacenter':
            # Create an instance of the parent class
            kls = classmapper(parent.parent._type)
            next_parent = kls(parent.parent, self.vim)
            next_parent.update_view_data(properties=['name', 'parent'])
            # ...and recursively call this method
            parent = self.find_datacenter(parent=next_parent)

        if parent.__class__.__name__ == 'Datacenter':
            return parent
        else:
            raise ObjectNotFoundError('No parent found for this instance')


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
        self._browser = None
        self.capability = None
        self.host = []
        self.info = None
        self.iormConfiguration = None
        self.summary = None
        self._vm = []
        ManagedEntity.__init__(self, mo_ref, vim)

    @ReadOnlyCachedAttribute
    def browser(self):
        result = self.vim.get_view(self._browser)
        return result

    @ReadOnlyCachedAttribute
    def vm(self):
        result = self.vim.get_views(self._vm)
        return result


class DistributedVirtualSwitch(ManagedEntity):
    def __init__(self, mo_ref, vim):
        self.capability = None
        self.config = None
        self.networkResourcePool = []
        self._portgroup = []
        self.summary = None
        self.uuid = None
        ManagedEntity.__init__(self, mo_ref, vim)


    @ReadOnlyCachedAttribute
    def portgroup(self):
        # TODO
        pass


class VmwareDistributedVirtualSwitch(DistributedVirtualSwitch):
    def __init__(self, mo_ref, vim):
        DistributedVirtualSwitch.__init__(self, mo_ref, vim)


class Folder(ManagedEntity):
    def __init__(self, mo_ref, vim):
        self.childEntity = []
        self.childType = []
        ManagedEntity.__init__(self, mo_ref, vim)


class HostSystem(ManagedEntity):
    def __init__(self, mo_ref, vim):
        self.capability = None
        self.config = None
        self.configManager = None
        self._datastore = []
        self._datastoreBrowser = None
        self.hardware = None
        self._network = []
        self.runtime = None
        self.summary = None
        self.systemResources = None
        self._vm = []
        ManagedEntity.__init__(self, mo_ref, vim)

    @ReadOnlyCachedAttribute
    def datastore(self):
        result = self.vim.get_views(self._datastore)
        return result

    @ReadOnlyCachedAttribute
    def datastoreBrowser(self):
        result = self.vim.get_views(self._datastoreBrowser)
        return result

    @ReadOnlyCachedAttribute
    def network(self):
        result = self.vim.get_views(self._network)
        return result

    @ReadOnlyCachedAttribute
    def vm(self):
        result = self.vim.get_views(self._vm)
        return result


class Network(ManagedEntity):
    def __init__(self, mo_ref, vim):
        self._host = []
        self.summary = None
        self._vm = []
        ManagedEntity.__init__(self, mo_ref, vim)

    @ReadOnlyCachedAttribute
    def host(self):
        result = self.vim.get_views(self._host)
        return result

    @ReadOnlyCachedAttribute
    def vm(self):
        result = self.vim.get_views(self._vm)
        return result


class DistributedVirtualPortgroup(Network):
    def __init__(self, mo_ref, vim):
        self.config = None
        self.key = None
        self.portKeys = None
        Network.__init__(self, mo_ref, vim)


class ResourcePool(ManagedEntity):
    def __init__(self, mo_ref, vim):
        self.config = None
        self.owner = None
        self.resource_pool = []
        self.runtime = None
        self.summary = None
        self.vm = []
        ManagedEntity.__init__(self, mo_ref, vim)


class VirtualApp(ResourcePool):
    def __init__(self, mo_ref, vim):
        self.childLink = []
        self._datastore = []
        self._network = []
        self._parentFolder = None
        self._parentVApp = None
        self.vAppConfig = None
        ResourcePool.__init__(self, mo_ref, vim)

    @ReadOnlyCachedAttribute
    def datastore(self):
        result = self.vim.get_views(self._datastore)
        return result

    @ReadOnlyCachedAttribute
    def network(self):
        result = self.vim.get_views(self._network)
        return result

    @ReadOnlyCachedAttribute
    def parentFolder(self):
        result = self.vim.get_view(self._parentFolder)
        return result

    @ReadOnlyCachedAttribute
    def parentVApp(self):
        result = self.vim.get_view(self._parentVApp)
        return result


class VirtualMachine(ManagedEntity):
    def __init__(self, mo_ref, vim):
        self.capability = None
        self.config = None
        self._datastore = []
        self._environmentBrowser = None
        self.guest = None
        self.guestHeartbeatStatus = None
        self.layout = None
        self.layoutEx = None
        self._network = []
        self._parentVApp = None
        self.resourceConfig = None
        self._resourcePool = None
        self._rootSnapshot = []
        self.runtime = None
        self.snapshot = None
        self.storage = None
        self.summary = None
        ManagedEntity.__init__(self, mo_ref, vim)

    @ReadOnlyCachedAttribute
    def datastore(self):
        result = self.vim.get_views(self._datastore)
        return result

    @ReadOnlyCachedAttribute
    def environmentBrowser(self):
        result = self.vim.get_view(self._environmentBrowser)
        return result

    @ReadOnlyCachedAttribute
    def network(self):
        result = self.vim.get_views(self._network)
        return result

    @ReadOnlyCachedAttribute
    def parentVApp(self):
        result = self.vim.get_view(self._parentVApp)
        return result

    @ReadOnlyCachedAttribute
    def resourcePool(self):
        result = self.vim.get_view(self._resourcePool)
        return result

    @ReadOnlyCachedAttribute
    def rootSnapshot(self):
        result = self.vim.get_views(self._rootSnapshot)
        return result


class ScheduledTask(ExtensibleManagedObject):
    def __init__(self, mo_ref, vim):
        self.info = None
        ExtensibleManagedObject.__init__(self, mo_ref, vim)


class Task(ExtensibleManagedObject):
    def __init__(self, mo_ref, vim):
        self.info = None
        ExtensibleManagedObject.__init__(self, mo_ref, vim)


class VirtualMachineSnapshot(ExtensibleManagedObject):
    def __init__(self, mo_ref, vim):
        self._childSnapshot = []
        self.config = None
        ExtensibleManagedObject.__init__(self, mo_ref, vim)

    @ReadOnlyCachedAttribute
    def childSnapshot(self):
        result = self.vim.get_views(self._childSnapshot)
        return result


class ExtensionManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.extensionList = []
        ManagedObject.__init__(self, mo_ref, vim)


class FileManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        ManagedObject.__init__(self, mo_ref, vim)


class HistoryCollector(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.filter = None
        ManagedObject.__init__(self, mo_ref, vim)


class EventHistoryCollector(HistoryCollector):
    def __init__(self, mo_ref, vim):
        self.latestPage = []
        HistoryCollector.__init__(self, mo_ref, vim)


class TaskHistoryCollector(HistoryCollector):
    def __init__(self, mo_ref, vim):
        self.latestPage = []
        HistoryCollector.__init__(self, mo_ref, vim)


class HostAutoStartManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.config = None
        ManagedObject.__init__(self, mo_ref, vim)


class HostBootDeviceSystem(ManagedObject):
    def __init__(self, mo_ref, vim):
        ManagedObject.__init__(self, mo_ref, vim)


class HostDatastoreBrowser(ManagedObject):
    def __init__(self, mo_ref, vim):
        self._datastore = []
        self.supportedType = []
        ManagedObject.__init__(self, mo_ref, vim)

    @ReadOnlyCachedAttribute
    def datastore(self):
        # TODO
        pass


class HostDatastoreSystem(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.capabilities = None
        self._datastore = []
        ManagedObject.__init__(self, mo_ref, vim)

    @ReadOnlyCachedAttribute
    def datastore(self):
        # TODO
        pass


class HostDateTimeSystem(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.dateTimeInfo = None
        ManagedObject.__init__(self, mo_ref, vim)


class HostDiagnosticSystem(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.activePartition = None
        ManagedObject.__init__(self, mo_ref, vim)


class HostFirmwareSystem(ManagedObject):
    def __init__(self, mo_ref, vim):
        ManagedObject.__init__(self, mo_ref, vim)


class HostHealthStatusSystem(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.runtime = None
        ManagedObject.__init__(self, mo_ref, vim)


class HostKernelModuleSystem(ManagedObject):
    def __init__(self, mo_ref, vim):
        ManagedObject.__init__(self, mo_ref, vim)


class HostLocalAccountManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        ManagedObject.__init__(self, mo_ref, vim)


class HostPatchManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        ManagedObject.__init__(self, mo_ref, vim)


class HostSnmpSystem(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.configuration = None
        self.limits = None
        ManagedObject.__init__(self, mo_ref, vim)


class HttpNfcLease(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.error = None
        self.info = None
        self.initializeProgress = None
        self.state = None
        ManagedObject.__init__(self, mo_ref, vim)


class IpPoolManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        ManagedObject.__init__(self, mo_ref, vim)


class LicenseAssignmentManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        ManagedObject.__init__(self, mo_ref, vim)


class LicenseManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.diagnostics = None
        self.evaluation = None
        self.featureInfo = []
        self._licenseAssignmentManager = None
        self.licensedEdition = None
        self.licenses = []
        self.source = None
        self.sourceAvailable = None
        ManagedObject.__init__(self, mo_ref, vim)

    @ReadOnlyCachedAttribute
    def licenseAssignmentManager(self):
        # TODO
        pass


class LocalizationManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.catalog = []
        ManagedObject.__init__(self, mo_ref, vim)


class OptionManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.setting = []
        self.supportedOptions = []
        ManagedObject.__init__(self, mo_ref, vim)


class OvfManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        ManagedObject.__init__(self, mo_ref, vim)


class PerformanceManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        ManagedObject.__init__(self, mo_ref, vim)


class Profile(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.complianceStatus = None
        self.config = None
        self.createdTime = None
        self.description = None
        self._entity = []
        self.modifiedTime = None
        self.name = None
        ManagedObject.__init__(self, mo_ref, vim)

    @ReadOnlyCachedAttribute
    def entity(self):
        # TODO
        pass


class ClusterProfile(Profile):
    def __init__(self, mo_ref, vim):
        Profile.__init__(self, mo_ref, vim)


class HostProfile(Profile):
    def __init__(self, mo_ref, vim):
        self._referenceHost = None
        Profile.__init__(self, mo_ref, vim)

    @ReadOnlyCachedAttribute
    def referenceHost(self):
        # TODO
        pass


class ProfileComplianceManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        ManagedObject.__init__(self, mo_ref, vim)


class ProfileManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        self._profile = []
        ManagedObject.__init__(self, mo_ref, vim)

    @ReadOnlyCachedAttribute
    def profile(self):
        # TODO
        pass


class ClusterProfileManager(ProfileManager):
    def __init__(self, mo_ref, vim):
        ProfileManager.__init__(self, mo_ref, vim)


class HostProfileManager(ProfileManager):
    def __init__(self, mo_ref, vim):
        ProfileManager.__init__(self, mo_ref, vim)


class PropertyCollector(ManagedObject):
    def __init__(self, mo_ref, vim):
        self._filter = []
        ManagedObject.__init__(self, mo_ref, vim)

    @ReadOnlyCachedAttribute
    def filter(self):
        # TODO
        pass


class PropertyFilter(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.partialUpdates = None
        self.spec = None
        ManagedObject.__init__(self, mo_ref, vim)


class ResourcePlanningManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        ManagedObject.__init__(self, mo_ref, vim)


class ScheduledTaskManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.description = None
        self._scheduledTask = []
        ManagedObject.__init__(self, mo_ref, vim)

    @ReadOnlyCachedAttribute
    def scheduledTask(self):
        # TODO
        pass


class SearchIndex(ManagedObject):
    def __init__(self, mo_ref, vim):
        ManagedObject.__init__(self, mo_ref, vim)


class ServiceInstance(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.capability = None
        self.content = None
        self.serverClock = None
        ManagedObject.__init__(self, mo_ref, vim)


class SessionManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.currentSession = None
        self.defaultLocale = None
        self.message = None
        self.messageLocaleList = None
        self.sessionList = None
        self.supportedLocaleList = None
        ManagedObject.__init__(self, mo_ref, vim)

    def __getattr__(self, name):
        # All vsphere methods start in uppercase
        if not name.istitle():
            return

        def func(*args, **kwargs):
            self.vim.invoke(name, self, *args, **kwargs)

        return func


class TaskManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.description = None
        self.maxCollector = None
        self._recentTask = []
        ManagedObject.__init__(self, mo_ref, vim)

    @ReadOnlyCachedAttribute
    def recentTask(self):
        # TODO
        pass


class UserDirectory(ManagedObject):
    def __init__(self, mo_ref, vim):
        self.domainList = None
        ManagedObject.__init__(self, mo_ref, vim)


class View(ManagedObject):
    def __init__(self, mo_ref, vim):
        ManagedObject.__init__(self, mo_ref, vim)


class ManagedObjectView(View):
    def __init__(self, mo_ref, vim):
        self.view = []
        View.__init__(self, mo_ref, vim)


class ContainerView(ManagedObjectView):
    def __init__(self, mo_ref, vim):
        self._container = None
        self.recursive = None
        self.type = None
        ManagedObjectView.__init__(self, mo_ref, vim)


class InventoryView(ManagedObjectView):
    def __init__(self, mo_ref, vim):
        ManagedObjectView.__init__(self, mo_ref, vim)


class ListView(ManagedObjectView):
    def __init__(self, mo_ref, vim):
        ManagedObjectView.__init__(self, mo_ref, vim)


class ViewManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        self._viewList = []
        ManagedObject.__init__(self, mo_ref, vim)

    @ReadOnlyCachedAttribute
    def viewList(self):
        # TODO
        pass


class VirtualDiskManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        ManagedObject.__init__(self, mo_ref, vim)


class VirtualizationManager(ManagedObject):
    def __init__(self, mo_ref, vim):
        # TODO: raise DeprecatedWarning
        ManagedObject.__init__(self, mo_ref, vim)


class VirtualMachineCompatibilityChecker(ManagedObject):
    def __init__(self, mo_ref, vim):
        ManagedObject.__init__(self, mo_ref, vim)


class VirtualMachineProvisioningChecker(ManagedObject):
    def __init__(self, mo_ref, vim):
        ManagedObject.__init__(self, mo_ref, vim)


classmap = dict((x.__name__, x) for x in (
    Alarm,
    AlarmManager,
    AuthorizationManager,
    ClusterComputeResource,
    ClusterProfile,
    ClusterProfileManager,
    ComputeResource,
    ContainerView,
    CustomFieldsManager,
    CustomizationSpecManager,
    Datacenter,
    Datastore,
    DiagnosticManager,
    DistributedVirtualPortgroup,
    DistributedVirtualSwitch,
    DistributedVirtualSwitchManager,
    EnvironmentBrowser,
    EventHistoryCollector,
    EventManager,
    ExtensibleManagedObject,
    ExtensionManager,
    FileManager,
    Folder,
    HistoryCollector,
    HostAutoStartManager,
    HostBootDeviceSystem,
    HostCpuSchedulerSystem,
    HostDatastoreBrowser,
    HostDatastoreSystem,
    HostDateTimeSystem,
    HostDiagnosticSystem,
    HostFirewallSystem,
    HostFirmwareSystem,
    HostHealthStatusSystem,
    HostKernelModuleSystem,
    HostLocalAccountManager,
    HostMemorySystem,
    HostNetworkSystem,
    HostPatchManager,
    HostPciPassthruSystem,
    HostProfile,
    HostProfileManager,
    HostServiceSystem,
    HostSnmpSystem,
    HostStorageSystem,
    HostSystem,
    HostVirtualNicManager,
    HostVMotionSystem,
    HttpNfcLease,
    InventoryView,
    IpPoolManager,
    LicenseAssignmentManager,
    LicenseManager,
    ListView,
    LocalizationManager,
    ManagedEntity,
    ManagedObjectView,
    Network,
    OptionManager,
    OvfManager,
    PerformanceManager,
    Profile,
    ProfileComplianceManager,
    ProfileManager,
    PropertyCollector,
    PropertyFilter,
    ResourcePlanningManager,
    ResourcePool,
    ScheduledTask,
    ScheduledTaskManager,
    SearchIndex,
    ServiceInstance,
    SessionManager,
    Task,
    TaskHistoryCollector,
    TaskManager,
    UserDirectory,
    View,
    ViewManager,
    VirtualApp,
    VirtualDiskManager,
    VirtualizationManager,
    VirtualMachine,
    VirtualMachineCompatibilityChecker,
    VirtualMachineProvisioningChecker,
    VirtualMachineSnapshot,
    VmwareDistributedVirtualSwitch,
))


def classmapper(name):
    return classmap[name]
