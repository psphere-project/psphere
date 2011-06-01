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

import logging

from suds import MethodNotFound
from psphere import soap
from psphere.errors import ObjectNotFoundError

logger = logging.getLogger("psphere")

class ManagedObject(object):
    """The base class which all managed object's derive from.
    
       :param mo_ref: The managed object reference used to create this instance
       :type mo_ref: ManagedObjectReference
       :param server: A reference back to the psphere server object, which \
       we use to make calls.
       :type server: Vim

    """
    attrs = {}
    def __init__(self, mo_ref, server):
        logger.debug("===== Have been passed %s as mo_ref: " % mo_ref)
        self.mo_ref = mo_ref
        self.server = server
        self.properties = {}
        if self.__class__.__name__ != "ManagedObject":
            parent_attrs = super(self.__class__, self).attrs
            self.properties = dict(self.attrs.items() + parent_attrs.items())
            print("Merged property list for %s: %s" % (self.__class__.__name__, self.properties))

    def update_view_data(self, properties=None):
        """Update the local object from the server-side object.
        
        >>> vm = VirtualMachine.from_server(server, "genesis")
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
        property_spec = soap.create(self.server.client, 'PropertySpec')
        property_spec.type = str(self.mo_ref._type)
        # Determine which properties to retrieve from the server
        if not properties and self.server.auto_populate:
            logger.debug("Retrieving all properties of the object")
            property_spec.all = True
        else:
            logger.debug("Retrieving %s properties" % len(properties))
            property_spec.all = False
            property_spec.pathSet = properties

        object_spec = soap.create(self.server.client, 'ObjectSpec')
        object_spec.obj = self.mo_ref

        pfs = soap.create(self.server.client, 'PropertyFilterSpec')
        pfs.propSet = [property_spec]
        pfs.objectSet = [object_spec]

        # Create a copy of the property collector and call the method
        pc = self.server.sc.propertyCollector
        object_content = pc.RetrieveProperties(specSet=pfs)[0]
        if not object_content:
            # TODO: Improve error checking and reporting
            logger.error("Nothing returned from RetrieveProperties!")

        self.set_view_data(object_content)

    def set_view_data(self, object_content):
        """Update the local object from the passed in object_content."""
        # A debugging convenience, allows inspection of the object_content
        # that was used to create the object
        logger.info("Setting view data for a %s" % self.__class__.__name__)
        self._object_content = object_content

        for dynprop in object_content.propSet:
            # If the class hasn't defined the property, don't use it
            if dynprop.name not in self.properties.keys():
                logger.error("Server returned a property '%s' but the object"
                             "hasn't defined it so it is being ignored." %
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
                self.properties[dynprop.name]["value"] = dynprop.val[0]
            else:
                logger.info("Setting value of a single-valued property")
                logger.debug("DynamicProperty value is a %s: " %
                             dynprop.val.__class__.__name__)
                logger.debug("%s being set to %s" % (dynprop.name,
                                                     dynprop.val))
                self.properties[dynprop.name]["value"] = dynprop.val

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
        logger.debug("Entering overriden built-in __getattribute__")
        # Built-ins always use the default behaviour
        if name.startswith("__"):
            logger.debug("Returning built-in attribute %s" % name)
            return object.__getattribute__(self, name)

        properties = object.__getattribute__(self, "properties")
        if name in properties.keys():
            # See if the value has already been retrieved an saved
            logger.debug("%s is a property of this object, checking if "
                         "attribute is already cached")
            if name in self.__dict__.keys():
                logger.debug("Using cached value for %s" % name)
                return object.__getattribute__(self, name)
            # Else, calculate the desired value and set it
            else:
                logger.debug("No cached value for %s. Retrieving..." % name)
                # TODO: Check if it's an array or a single value
                #result = self.method(inst)
                if self.properties[name]["MOR"] is True:
                    logger.debug("%s is a MOR" % name)
                    if isinstance(self.properties[name]["value"], list):
                        logger.debug("%s is a list of MORs" % name)
                        result = self.server.get_views(self.properties[name]["value"])
                    else:
                        logger.debug("%s is single-valued" % name)
                        result = self.server.get_view(self.properties[name]["value"])
                else:
                    # It's just a property, get it
                    logger.debug("%s is not a MOR" % name)
                    result = self.properties[name]["value"]
                    
                # Set the object value to returned value
                logger.debug("Retrieved %s for %s" % (result, name))
                self.__dict__[name] = result
                return result            
        else:
            try:
                # Here we must manually get the server object so we
                # don't get recursively called when the next method
                # call looks for it
                server = object.__getattribute__(self, "server")
                getattr(server.client.service, name)
                def func(**kwargs):
                    result = self.server.invoke(name, _this=self.mo_ref, **kwargs)
                    return result
        
                return func
            except MethodNotFound:
                return object.__getattribute__(self, name)

        def __set__(self, name, value):
            print("Setting %s to %s" % (name, value))
            self.__set__(name, value)

# First list the classes which directly inherit from ManagedObject
class AlarmManager(ManagedObject):
    attrs = {"defaultExpression": {"MOR": False, "value": list()},
             "description": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, server):
        super(AlarmManager, self).__init__(mo_ref, server)


class AuthorizationManager(ManagedObject):
    attrs = {"description": {"MOR": False, "value": None},
             "privilegeList": {"MOR": False, "value": list()},
             "roleList": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, server):
        super(AuthorizationManager, self).__init__(mo_ref, server)


class CustomFieldsManager(ManagedObject):
    attrs = {"field": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, server):
        super(CustomFieldsManager, self).__init__(mo_ref, server)
        self.field = []


class CustomizationSpecManager(ManagedObject):
    attrs = {"encryptionKey": {"MOR": False, "value": None},
             "info": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, server):
        super(CustomizationSpecManager, self).__init__(mo_ref, server)


class DiagnosticManager(ManagedObject):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(DiagnosticManager, self).__init__(mo_ref, server)


class DistributedVirtualSwitchManager(ManagedObject):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(DistributedVirtualSwitchManager, self).__init__(mo_ref, server)


class EnvironmentBrowser(ManagedObject):
    attrs = {"datastoreBrowser": {"MOR": True, "value": None}}
    def __init__(self, mo_ref, server):
        super(EnvironmentBrowser, self).__init__(mo_ref, server)


class EventManager(ManagedObject):
    attrs = {"description": {"MOR": False, "value": None},
             "latestEvent": {"MOR": False, "value": None},
             "maxCollector": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(EventManager, self).__init__(mo_ref, server)


class ExtensibleManagedObject(ManagedObject):
    attrs = {"availableField": {"MOR": False, "value": list()},
             "value": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, server):
        super(ExtensibleManagedObject, self).__init__(mo_ref, server)


class Alarm(ExtensibleManagedObject):
    attrs = {"info": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(Alarm, self).__init__(mo_ref, server)


class HostCpuSchedulerSystem(ExtensibleManagedObject):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(HostCpuSchedulerSystem, self).__init__(mo_ref, server)


class HostFirewallSystem(ExtensibleManagedObject):
    attrs = {"firewallInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(HostFirewallSystem, self).__init__(mo_ref, server)


class HostMemorySystem(ExtensibleManagedObject):
    attrs = {"consoleReservationInfo": {"MOR": False, "value": None},
             "virtualMachineReservationInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(HostMemorySystem, self).__init__(mo_ref, server)


class HostNetworkSystem(ExtensibleManagedObject):
    attrs = {"capabilites": {"MOR": False, "value": None},
             "consoleIpRouteConfig": {"MOR": False, "value": None},
             "dnsConfig": {"MOR": False, "value": None},
             "ipRouteConfig": {"MOR": False, "value": None},
             "networkConfig": {"MOR": False, "value": None},
             "networkInfo": {"MOR": False, "value": None},
             "offloadCapabilities": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(HostNetworkSystem, self).__init__(mo_ref, server)


class HostPciPassthruSystem(ExtensibleManagedObject):
    attrs = {"pciPassthruInfo": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, server):
        super(HostPciPassthruSystem, self).__init__(mo_ref, server)


class HostServiceSystem(ExtensibleManagedObject):
    attrs = {"serviceInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(HostServiceSystem, self).__init__(mo_ref, server)


class HostStorageSystem(ExtensibleManagedObject):
    attrs = {"fileSystemVolumeInfo": {"MOR": False, "value": None},
             "multipathStateInfo": {"MOR": False, "value": None},
             "storageDeviceInfo": {"MOR": False, "value": None},
             "systemFile": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(HostStorageSystem, self).__init__(mo_ref, server)


class HostVirtualNicManager(ExtensibleManagedObject):
    attrs = {"info": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(HostVirtualNicManager, self).__init__(mo_ref, server)
        self.info = None


class HostVMotionSystem(ExtensibleManagedObject):
    attrs = {"ipConfig": {"MOR": False, "value": None},
             "netConfig": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(HostVMotionSystem, self).__init__(mo_ref, server)
        self.ipConfig = None
        self.netConfig = None


class ManagedEntity(ExtensibleManagedObject):
    attrs = {"alarmActionsEnabled": {"MOR": False, "value": list()},
             "configIssue": {"MOR": False, "value": list()},
              "configStatus": {"MOR": False, "value": None},
              "customValue": {"MOR": False, "value": list()},
              "declaredAlarmState": {"MOR": False, "value": list()},
              "disabledMethod": {"MOR": False, "value": None},
              "effectiveRole": {"MOR": False, "value": list()},
              "name": {"MOR": False, "value": None},
              "overallStatus": {"MOR": False, "value": None},
              "parent": {"MOR": True, "value": None},
              "permission": {"MOR": False, "value": list()},
              "recentTask": {"MOR": True, "value": list()},
              "tag": {"MOR": False, "value": list()},
              "triggeredAlarmState": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, server):
        super(ManagedEntity, self).__init__(mo_ref, server)

    @classmethod
    def find(cls, vim, filter=None):
        """Find ManagedEntity's of this type using the given filter.
        
        :param filter: Find ManagedEntity's matching these key/value pairs
        :type filter: dict
        :returns: A list of ManagedEntity's matching the filter or None
        :rtype: list
        """
        return vim.find_entity_views(view_type=cls.__name__, filter=filter)

    @classmethod
    def find_one(cls, vim, filter=None):
        """Find a ManagedEntity of this type using the given filter.
        
        If multiple ManagedEntity's are found, only the first is returned.
        
        :param filter: Find ManagedEntity's matching these key/value pairs
        :type filter: dict
        :returns: A ManagedEntity's matching the filter or None
        :rtype: ManagedEntity
        """
        return vim.find_entity_view(view_type=cls.__name__, filter=filter)

    def find_datacenter(self, parent=None):
        """Find the datacenter which this ManagedEntity belongs to."""
        # If the parent hasn't been set, use the parent of the
        # calling instance, if it exists
        if not parent:
            if not self.parent:
                raise ObjectNotFoundError('No parent found for this instance')

            # Establish the type of object we need to create
            kls = classmapper(self.parent._type)
            parent = kls(self.parent, self.server)
            parent.update_view_data(properties=['name', 'parent'])

        if not parent.__class__.__name__ == 'Datacenter':
            # Create an instance of the parent class
            kls = classmapper(parent.parent._type)
            next_parent = kls(parent.parent, self.server)
            next_parent.update_view_data(properties=['name', 'parent'])
            # ...and recursively call this method
            parent = self.find_datacenter(parent=next_parent)

        if parent.__class__.__name__ == 'Datacenter':
            return parent
        else:
            raise ObjectNotFoundError('No parent found for this instance')


class ComputeResource(ManagedEntity):
    attrs = {"configurationEx": {"MOR": False, "value": None},
             "datastore": {"MOR": False, "value": list()},
             "environmentBrowser": {"MOR": False, "value": None},
             "host": {"MOR": False, "value": list()},
             "network": {"MOR": False, "value": list()},
             "resourcePool": {"MOR": False, "value": None},
             "summary": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(ComputeResource, self).__init__(mo_ref, server)

    def find_datastore(self, name):
        if not self.datastore:
            self.update_view_data(self.datastore)

        datastores = self.server.get_views(self.datastore,
                                           properties=['summary'])
        for datastore in datastores:
            if datastore.summary.name == name:
                if self.server.auto_populate:
                    datastore.update_view_data()
                return datastore

        raise ObjectNotFoundError(error='No datastore matching %s' % name)


class ClusterComputeResource(ComputeResource):
    attrs = {"actionHistory": {"MOR": False, "value": list()},
             "configuration": {"MOR": False, "value": None},
             "drsFault": {"MOR": False, "value": list()},
             "drsRecommendation": {"MOR": False, "value": list()},
             "migrationHistory": {"MOR": False, "value": list()},
             "recommendation": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, server):
        super(ClusterComputeResource, self).__init__(mo_ref, server)


class Datacenter(ManagedEntity):
    attrs = {"datastore": {"MOR": False, "value": list()},
             "datastoreFolder": {"MOR": False, "value": None},
             "hostFolder": {"MOR": False, "value": None},
             "network": {"MOR": False, "value": list()},
             "networkFolder": {"MOR": False, "value": None},
             "vmFolder": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(Datacenter, self).__init__(mo_ref, server)


class Datastore(ManagedEntity):
    attrs = {"browser": {"MOR": True, "value": None},
             "capability": {"MOR": False, "value": None},
             "host": {"MOR": False, "value": list()},
             "info": {"MOR": False, "value": None},
             "iormConfiguration": {"MOR": False, "value": None},
             "summary": {"MOR": False, "value": None},
             "vm": {"MOR": True, "value": list()}}
    def __init__(self, mo_ref, server):
        super(Datastore, self).__init__(mo_ref, server)

class DistributedVirtualSwitch(ManagedEntity):
    attrs = {"capability": {"MOR": False, "value": None},
             "config": {"MOR": False, "value": None},
             "networkResourcePool": {"MOR": False, "value": list()},
             "portgroup": {"MOR": True, "value": list()},
             "summary": {"MOR": False, "value": None},
             "uuid": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(DistributedVirtualSwitch, self).__init__(mo_ref, server)
        self.capability = None
        self.config = None
        self.networkResourcePool = []
        self._portgroup = []
        self.summary = None
        self.uuid = None


class VmwareDistributedVirtualSwitch(DistributedVirtualSwitch):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(VmwareDistributedVirtualSwitch, self).__init__(mo_ref, server)


class Folder(ManagedEntity):
    attrs = {"childEntity": {"MOR": True, "value": list()},
             "childType": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, server):
        super(Folder, self).__init__(mo_ref, server)


class HostSystem(ManagedEntity):
    attrs = {"capability": {"MOR": False, "value": None},
             "config": {"MOR": False, "value": None},
             "configManager": {"MOR": False, "value": None},
             "datastore": {"MOR": True, "value": list()},
             "datastoreBrowser": {"MOR": True, "value": None},
             "hardware": {"MOR": False, "value": None},
             "network": {"MOR": True, "value": list()},
             "runtime": {"MOR": False, "value": None},
             "summary": {"MOR": False, "value": None},
             "systemResources": {"MOR": False, "value": None},
             "vm": {"MOR": True, "value": list()}}
    def __init__(self, mo_ref, server):
        super(HostSystem, self).__init__(mo_ref, server)


class Network(ManagedEntity):
    attrs = {"host": {"MOR": True, "value": list()},
             "summary": {"MOR": False, "value": None},
             "vm": {"MOR": True, "value": list()}}
    def __init__(self, mo_ref, server):
        super(Network, self).__init__(mo_ref, server)


class DistributedVirtualPortgroup(Network):
    attrs = {"config": {"MOR": False, "value": None},
             "key": {"MOR": False, "value": None},
             "portKeys": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(DistributedVirtualPortgroup, self).__init__(mo_ref, server)


class ResourcePool(ManagedEntity):
    attrs = {"childConfiguration": {"MOR": False, "value": list()},
             "config": {"MOR": False, "value": None},
             "owner": {"MOR": True, "value": list()},
             "resourcePool": {"MOR": True, "value": list()},
             "runtime": {"MOR": False, "value": None},
             "summary": {"MOR": False, "value": None},
             "vm": {"MOR": True, "value": list()}}
    def __init__(self, mo_ref, server):
        super(ResourcePool, self).__init__(mo_ref, server)


class VirtualApp(ResourcePool):
    attrs = {"childLink": {"MOR": False, "value": list()},
             "datastore": {"MOR": True, "value": None},
             "network": {"MOR": True, "value": list()},
             "parentFolder": {"MOR": True, "value": None},
             "parentVApp": {"MOR": True, "value": None},
             "vAppConfig": {"MOR": True, "value": list()}}
    def __init__(self, mo_ref, server):
        super(VirtualApp, self).__init__(mo_ref, server)


class VirtualMachine(ManagedEntity):
    attrs = {}
    attrs["capability"] = {"MOR": False, "value": None}
    attrs["config"] = {"MOR": False, "value": None}
    attrs["datastore"] = {"MOR": True, "value": list()}
    attrs["environmentBrowser"] = {"MOR": True, "value": None}
    attrs["guest"] = {"MOR": False, "value": None}
    attrs["heartbeatStatus"] = {"MOR": False, "value": None}
    attrs["layout"] = {"MOR": False, "value": None}
    attrs["layoutEx"] = {"MOR": False, "value": None}
    attrs["network"] = {"MOR": True, "value": list()}
    attrs["parentVApp"] = {"MOR": False, "value": None}
    attrs["resourceConfig"] = {"MOR": False, "value": None}
    attrs["resourcePool"] = {"MOR": True, "value": None}
    attrs["rootSnapshot"] = {"MOR": False, "value": list()}
    attrs["runtime"] = {"MOR": False, "value": None}
    attrs["snapshot"] = {"MOR": False, "value": None}
    attrs["storage"] = {"MOR": False, "value": None}
    attrs["summary"] = {"MOR": False, "value": None}
    def __init__(self, mo_ref, server):
        super(VirtualMachine, self).__init__(mo_ref, server)

    @classmethod
    def from_server(cls, server, name):
        # The caller is expected to catch an ObjectNotFoundError
        obj = server.find_entity_view(cls.__name__, filter={'name': name})
        return obj


class ScheduledTask(ExtensibleManagedObject):
    attrs = {"info": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(ScheduledTask, self).__init__(mo_ref, server)


class Task(ExtensibleManagedObject):
    attrs = {"info": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(Task, self).__init__(mo_ref, server)

class VirtualMachineSnapshot(ExtensibleManagedObject):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(VirtualMachineSnapshot, self).__init__(mo_ref, server)
        self._childSnapshot = []
        self.config = None


class ExtensionManager(ManagedObject):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(ExtensionManager, self).__init__(mo_ref, server)
        self.extensionList = []


class FileManager(ManagedObject):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(FileManager, self).__init__(mo_ref, server)


class HistoryCollector(ManagedObject):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(HistoryCollector, self).__init__(self, mo_ref, server)
        self.filter = None


class EventHistoryCollector(HistoryCollector):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(EventHistoryCollector, self).__init__(mo_ref, server)
        self.latestPage = []


class TaskHistoryCollector(HistoryCollector):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(TaskHistoryCollector, self).__init__(mo_ref, server)
        self.latestPage = []


class HostAutoStartManager(ManagedObject):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(HostAutoStartManager, self).__init__(mo_ref, server)
        self.config = None


class HostBootDeviceSystem(ManagedObject):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(HostBootDeviceSystem, self).__init__(mo_ref, server)


class HostDatastoreBrowser(ManagedObject):
    attrs = {"datastore": {"MOR": True, "value": list()},
             "supportedType": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, server):
        super(HostDatastoreBrowser, self).__init__(mo_ref, server)


class HostDatastoreSystem(ManagedObject):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(HostDatastoreSystem, self).__init__(mo_ref, server)
        self.capabilities = None
        self._datastore = []


class HostDateTimeSystem(ManagedObject):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(HostDateTimeSystem, self).__init__(mo_ref, server)
        self.dateTimeInfo = None


class HostDiagnosticSystem(ManagedObject):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(HostDiagnosticSystem, self).__init__(mo_ref, server)
        self.activePartition = None


class HostFirmwareSystem(ManagedObject):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(HostFirmwareSystem, self).__init__(mo_ref, server)


class HostHealthStatusSystem(ManagedObject):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(HostHealthStatusSystem, self).__init__(mo_ref, server)
        self.runtime = None


class HostKernelModuleSystem(ManagedObject):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(HostKernelModuleSystem, self).__init__(mo_ref, server)


class HostLocalAccountManager(ManagedObject):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(HostLocalAccountManager, self).__init__(mo_ref, server)


class HostPatchManager(ManagedObject):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(HostPatchManager, self).__init__(mo_ref, server)


class HostSnmpSystem(ManagedObject):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(HostSnmpSystem, self).__init__(mo_ref, server)
        self.configuration = None
        self.limits = None


class HttpNfcLease(ManagedObject):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(HttpNfcLease, self).__init__(mo_ref, server)
        self.error = None
        self.info = None
        self.initializeProgress = None
        self.state = None


class IpPoolManager(ManagedObject):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(IpPoolManager, self).__init__(mo_ref, server)


class LicenseAssignmentManager(ManagedObject):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(LicenseAssignmentManager, self).__init__(mo_ref, server)


class LicenseManager(ManagedObject):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(LicenseManager, self).__init__(mo_ref, server)
        self.diagnostics = None
        self.evaluation = None
        self.featureInfo = []
        self._licenseAssignmentManager = None
        self.licensedEdition = None
        self.licenses = []
        self.source = None
        self.sourceAvailable = None


class LocalizationManager(ManagedObject):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(LocalizationManager, self).__init__(mo_ref, server)
        self.catalog = []


class OptionManager(ManagedObject):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(OptionManager, self).__init__(mo_ref, server)
        self.setting = []
        self.supportedOptions = []


class OvfManager(ManagedObject):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(OvfManager, self).__init__(mo_ref, server)


class PerformanceManager(ManagedObject):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(PerformanceManager, self).__init__(mo_ref, server)


class Profile(ManagedObject):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(Profile, self).__init__(mo_ref, server)
        self.complianceStatus = None
        self.config = None
        self.createdTime = None
        self.description = None
        self._entity = []
        self.modifiedTime = None
        self.name = None


class ClusterProfile(Profile):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(ClusterProfile, self).__init__(mo_ref, server)


class HostProfile(Profile):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(HostProfile, self).__init__(mo_ref, server)
        self._referenceHost = None


class ProfileComplianceManager(ManagedObject):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(ProfileComplianceManager, self).__init__(mo_ref, server)


class ProfileManager(ManagedObject):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(ProfileManager, self).__init__(mo_ref, server)
        self._profile = []


class ClusterProfileManager(ProfileManager):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(ClusterProfileManager, self).__init__(mo_ref, server)


class HostProfileManager(ProfileManager):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(HostProfileManager, self).__init__(mo_ref, server)


class PropertyCollector(ManagedObject):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(PropertyCollector, self).__init__(mo_ref, server)
        self._filter = []


class PropertyFilter(ManagedObject):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(PropertyFilter, self).__init__(mo_ref, server)
        self.partialUpdates = None
        self.spec = None


class ResourcePlanningManager(ManagedObject):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(ResourcePlanningManager, self).__init__(mo_ref, server)


class ScheduledTaskManager(ManagedObject):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(ScheduledTaskManager, self).__init__(mo_ref, server)
        self.description = None
        self._scheduledTask = []


class SearchIndex(ManagedObject):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(SearchIndex, self).__init__(mo_ref, server)


class ServiceInstance(ManagedObject):
    attrs = {"capability": {"MOR": True, "value": None},
             "content": {"MOR": True, "value": None},
             "serverClock": {"MOR": True, "value": None}}
    def __init__(self, mo_ref, server):
        super(ServiceInstance, self).__init__(mo_ref, server)


class SessionManager(ManagedObject):
    attrs = {"currentSession": {"MOR": False, "value": None},
             "defaultLocale": {"MOR": False, "value": None},
             "message": {"MOR": False, "value": None},
             "messageLocaleList": {"MOR": False, "value": None},
             "sessionList": {"MOR": False, "value": None},
             "supportedLocaleList": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(SessionManager, self).__init__(mo_ref, server)


class TaskManager(ManagedObject):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(TaskManager, self).__init__(mo_ref, server)
        self.description = None
        self.maxCollector = None
        self._recentTask = []


class UserDirectory(ManagedObject):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(UserDirectory, self).__init__(mo_ref, server)
        self.domainList = None


class View(ManagedObject):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(View, self).__init__(mo_ref, server)


class ManagedObjectView(View):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(ManagedObjectView, self).__init__(mo_ref, server)
        self.view = []


class ContainerView(ManagedObjectView):
    attrs = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, server):
        super(ContainerView, self).__init__(mo_ref, server)
        self._container = None
        self.recursive = None
        self.type = None


class InventoryView(ManagedObjectView):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(InventoryView, self).__init__(mo_ref, server)


class ListView(ManagedObjectView):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(ListView, self).__init__(mo_ref, server)


class ViewManager(ManagedObject):
    attrs = {"viewList": {"MOR": True, "value": list()}}
    def __init__(self, mo_ref, server):
        super(ViewManager, self).__init__(mo_ref, server)


class VirtualDiskManager(ManagedObject):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(VirtualDiskManager, self).__init__(mo_ref, server)


class VirtualizationManager(ManagedObject):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(VirtualizationManager, self).__init__(mo_ref, server)
        # TODO: raise DeprecatedWarning


class VirtualMachineCompatibilityChecker(ManagedObject):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(VirtualMachineCompatibilityChecker, self).__init__(mo_ref, server)


class VirtualMachineProvisioningChecker(ManagedObject):
    attrs = {}
    def __init__(self, mo_ref, server):
        super(VirtualMachineProvisioningChecker, self).__init__(mo_ref, server)


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
