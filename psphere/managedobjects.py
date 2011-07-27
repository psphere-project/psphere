"""Defines the Managed Object's found in the vSphere API."""

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


import logging

from suds import MethodNotFound
from psphere import soap
from psphere.errors import ObjectNotFoundError

logger = logging.getLogger("psphere")

class ManagedObject(object):
    """The base class which all managed object's derive from.
    
   :param mo_ref: The managed object reference used to create this instance
   :type mo_ref: ManagedObjectReference
   :param client: A reference back to the psphere client object, which \
   we use to make calls.
   :type client: Client

    """
    props = {}
    def __init__(self, mo_ref, client):
        logger.debug("===== Have been passed %s as mo_ref: " % mo_ref)
        self.mo_ref = mo_ref
        self.client = client
        logger.debug("Merged property list for %s: %s" %
                     (self.__class__, self.props))

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
            property_spec.pathSet = passroperties

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
            if dynprop.name not in self.props.keys():
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
            if dynprop.val.__name__.startswith('Array'):
                # suds returns a list containing a single item, which
                # is another list. Use the first item which is the real list
                logger.info("Setting value of an Array* property")
                logger.debug("%s being set to %s" % (dynprop.name,
                                                     dynprop.val[0]))
                self.props[dynprop.name]["value"] = dynprop.val[0]
            else:
                logger.info("Setting value of a single-valued property")
                logger.debug("DynamicProperty value is a %s: " %
                             dynprop.val.__name__)
                logger.debug("%s being set to %s" % (dynprop.name,
                                                     dynprop.val))
                self.props[dynprop.name]["value"] = dynprop.val

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
        if name.startswith("__") or name == "props":
            logger.debug("Returning built-in attribute %s" % name)
            return object.__getattribute__(self, name)

        props = object.__getattribute__(self, "props")
        if name in props.keys():
            # See if the value has already been retrieved an saved
            logger.debug("%s is a property of this object, checking if "
                         "attribute is already cached" % name)
            if name in self.__dict__.keys():
                logger.debug("Using cached value for %s" % name)
                return object.__getattribute__(self, name)
            # Else, calculate the desired value and set it
            else:
                logger.debug("No cached value for %s. Retrieving..." % name)
                # TODO: Check if it's an array or a single value
                #result = self.method(inst)
                if self.props[name]["MOR"] is True:
                    logger.debug("%s is a MOR" % name)
                    if isinstance(self.props[name]["value"], list):
                        logger.debug("%s is a list of MORs" % name)
                        result = self.client.get_views(self.props[name]["value"])
                    else:
                        logger.debug("%s is single-valued" % name)
                        result = self.client.get_view(self.props[name]["value"])
                else:
                    # It's just a property, get it
                    logger.debug("%s is not a MOR" % name)
                    result = self.props[name]["value"]
                    
                # Set the object value to returned value
                logger.debug("Retrieved %s for %s" % (result, name))
                self.__dict__[name] = result
                return result            
        else:
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


# First list the classes which directly inherit from ManagedObject
class AlarmManager(ManagedObject):
    props = {"defaultExpression": {"MOR": False, "value": list()},
             "description": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class AuthorizationManager(ManagedObject):
    props = {"description": {"MOR": False, "value": None},
             "privilegeList": {"MOR": False, "value": list()},
             "roleList": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class CustomFieldsManager(ManagedObject):
    props = {"field": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class CustomizationSpecManager(ManagedObject):
    props = {"encryptionKey": {"MOR": False, "value": list()},
             "info": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class DiagnosticManager(ManagedObject):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class DistributedVirtualSwitchManager(ManagedObject):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class EnvironmentBrowser(ManagedObject):
    props = {"datastoreBrowser": {"MOR": True, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class EventManager(ManagedObject):
    props = {"description": {"MOR": False, "value": None},
             "latestEvent": {"MOR": False, "value": None},
             "maxCollector": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class ExtensibleManagedObject(ManagedObject):
    props = {"availableField": {"MOR": False, "value": list()},
             "value": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, client):
        ManagedObject.__init__(self, mo_ref, client)
        self.props = dict(ManagedObject.props.items() + self.props.items())


class Alarm(ExtensibleManagedObject):
    props = {"info": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostCpuSchedulerSystem(ExtensibleManagedObject):
    props = {"hyperThreadInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostFirewallSystem(ExtensibleManagedObject):
    props = {"firewallInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostMemorySystem(ExtensibleManagedObject):
    props = {"consoleReservationInfo": {"MOR": False, "value": None},
             "virtualMachineReservationInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostNetworkSystem(ExtensibleManagedObject):
    props = {"capabilites": {"MOR": False, "value": None},
             "consoleIpRouteConfig": {"MOR": False, "value": None},
             "dnsConfig": {"MOR": False, "value": None},
             "ipRouteConfig": {"MOR": False, "value": None},
             "networkConfig": {"MOR": False, "value": None},
             "networkInfo": {"MOR": False, "value": None},
             "offloadCapabilities": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostPciPassthruSystem(ExtensibleManagedObject):
    props = {"pciPassthruInfo": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostServiceSystem(ExtensibleManagedObject):
    props = {"serviceInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostStorageSystem(ExtensibleManagedObject):
    props = {"fileSystemVolumeInfo": {"MOR": False, "value": None},
             "multipathStateInfo": {"MOR": False, "value": None},
             "storageDeviceInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostVirtualNicManager(ExtensibleManagedObject):
    props = {"info": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostVMotionSystem(ExtensibleManagedObject):
    props = {"ipConfig": {"MOR": False, "value": None},
             "netConfig": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class ManagedEntity(ExtensibleManagedObject):
    props = {"alarmActionsEnabled": {"MOR": False, "value": list()},
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
    def __init__(self, mo_ref, client):
        ExtensibleManagedObject.__init__(self, mo_ref, client)
        self.props = dict(ExtensibleManagedObject.props.items() +
                          self.props.items())

    @classmethod
    def find(cls, client):
        """Find ManagedEntity's of this type using the given filter.
        
        :param filter: Find ManagedEntity's matching these key/value pairs
        :type filter: dict
        :returns: A list of ManagedEntity's matching the filter or None
        :rtype: list
        """
        # TODO: Implement filter for this find method
        return client.find_entity_views(view_type=cls.__name__)

    @classmethod
    def find_one(cls, client, filter=None, properties=None):
        """Find a ManagedEntity of this type using the given filter.
        
        If multiple ManagedEntity's are found, only the first is returned.
        
        :param filter: Find ManagedEntity's matching these key/value pairs
        :type filter: dict
        :returns: A ManagedEntity's matching the filter or None
        :rtype: ManagedEntity
        """
        if filter is None:
            filter = []
        if properties is None:
            properties = []
        return client.find_entity_view(view_type=cls.__name__, filter=filter,
                                       properties=properties)

    def find_datacenter(self, parent=None):
        """Find the datacenter which this ManagedEntity belongs to."""
        # If the parent hasn't been set, use the parent of the
        # calling instance, if it exists
        if not parent:
            if not self.parent:
                raise ObjectNotFoundError('No parent found for this instance')

            # Establish the type of object we need to create
            kls = classmapper(self.parent._type)
            parent = kls(self.parent, self.client)
            parent.update_view_data(properties=['name', 'parent'])

        if not parent.__name__ == 'Datacenter':
            # Create an instance of the parent class
            kls = classmapper(parent.parent._type)
            next_parent = kls(parent.parent, self.client)
            next_parent.update_view_data(properties=['name', 'parent'])
            # ...and recursively call this method
            parent = self.find_datacenter(parent=next_parent)

        if parent.__name__ == 'Datacenter':
            return parent
        else:
            raise ObjectNotFoundError('No parent found for this instance')


class ComputeResource(ManagedEntity):
    props = {"configurationEx": {"MOR": False, "value": None},
             "datastore": {"MOR": True, "value": list()},
             "environmentBrowser": {"MOR": True, "value": None},
             "host": {"MOR": True, "value": list()},
             "network": {"MOR": True, "value": list()},
             "resourcePool": {"MOR": True, "value": None},
             "summary": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())

    def find_datastore(self, name):
        if not self.datastore:
            self.update_view_data(self.datastore)

        datastores = self.client.get_views(self.datastore,
                                           properties=['summary'])
        for datastore in datastores:
            if datastore.summary.name == name:
                if self.client.auto_populate:
                    datastore.update_view_data()
                return datastore

        raise ObjectNotFoundError(error='No datastore matching %s' % name)


class ClusterComputeResource(ComputeResource):
    props = {"actionHistory": {"MOR": False, "value": list()},
             "configuration": {"MOR": False, "value": None},
             "drsFault": {"MOR": False, "value": list()},
             "drsRecommendation": {"MOR": False, "value": list()},
             "migrationHistory": {"MOR": False, "value": list()},
             "recommendation": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class Datacenter(ManagedEntity):
    props = {"datastore": {"MOR": True, "value": list()},
             "datastoreFolder": {"MOR": True, "value": None},
             "hostFolder": {"MOR": True, "value": None},
             "network": {"MOR": True, "value": list()},
             "networkFolder": {"MOR": True, "value": None},
             "vmFolder": {"MOR": True, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class Datastore(ManagedEntity):
    props = {"browser": {"MOR": True, "value": None},
             "capability": {"MOR": False, "value": None},
             "host": {"MOR": False, "value": list()},
             "info": {"MOR": False, "value": None},
             "iormConfiguration": {"MOR": False, "value": None},
             "summary": {"MOR": False, "value": None},
             "vm": {"MOR": True, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())

class DistributedVirtualSwitch(ManagedEntity):
    props = {"capability": {"MOR": False, "value": None},
             "config": {"MOR": False, "value": None},
             "portgroup": {"MOR": True, "value": list()},
             "summary": {"MOR": False, "value": None},
             "uuid": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class VmwareDistributedVirtualSwitch(DistributedVirtualSwitch):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class Folder(ManagedEntity):
    props = {"childEntity": {"MOR": True, "value": list()},
             "childType": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, client):
        ManagedEntity.__init__(self, mo_ref, client)
        self.props = dict(ManagedEntity.props.items() + self.props.items())


class HostSystem(ManagedEntity):
    props = {"capability": {"MOR": False, "value": None},
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
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class Network(ManagedEntity):
    props = {"host": {"MOR": True, "value": list()},
             "name": {"MOR": False, "value": None},
             "summary": {"MOR": False, "value": None},
             "vm": {"MOR": True, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class DistributedVirtualPortgroup(Network):
    props = {"config": {"MOR": False, "value": None},
             "key": {"MOR": False, "value": None},
             "portKeys": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class ResourcePool(ManagedEntity):
    props = {"childConfiguration": {"MOR": False, "value": list()},
             "config": {"MOR": False, "value": None},
             "owner": {"MOR": True, "value": None},
             "resourcePool": {"MOR": True, "value": list()},
             "runtime": {"MOR": False, "value": None},
             "summary": {"MOR": False, "value": None},
             "vm": {"MOR": True, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class VirtualApp(ResourcePool):
    props = {"datastore": {"MOR": True, "value": list()},
             "network": {"MOR": True, "value": list()},
             "parentFolder": {"MOR": True, "value": None},
             "vAppConfig": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class VirtualMachine(ManagedEntity):
    props = {}
    props["capability"] = {"MOR": False, "value": None}
    props["config"] = {"MOR": False, "value": None}
    props["datastore"] = {"MOR": True, "value": list()}
    props["environmentBrowser"] = {"MOR": True, "value": None}
    props["guest"] = {"MOR": False, "value": None}
    props["heartbeatStatus"] = {"MOR": False, "value": None}
    props["layout"] = {"MOR": False, "value": None}
    props["layoutEx"] = {"MOR": False, "value": None}
    props["network"] = {"MOR": True, "value": list()}
    props["parentVApp"] = {"MOR": False, "value": None}
    props["resourceConfig"] = {"MOR": False, "value": None}
    props["resourcePool"] = {"MOR": True, "value": None}
    props["rootSnapshot"] = {"MOR": False, "value": list()}
    props["runtime"] = {"MOR": False, "value": None}
    props["snapshot"] = {"MOR": False, "value": None}
    props["storage"] = {"MOR": False, "value": None}
    props["summary"] = {"MOR": False, "value": None}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class ScheduledTask(ExtensibleManagedObject):
    props = {"info": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class Task(ExtensibleManagedObject):
    props = {"info": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())

class VirtualMachineSnapshot(ExtensibleManagedObject):
    props = {"config": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class ExtensionManager(ManagedObject):
    props = {"extensionList": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class FileManager(ManagedObject):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HistoryCollector(ManagedObject):
    props = {"filter": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class EventHistoryCollector(HistoryCollector):
    props = {"latestPage": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class TaskHistoryCollector(HistoryCollector):
    props = {"latestPage": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostAutoStartManager(ManagedObject):
    props = {"config": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostBootDeviceSystem(ManagedObject):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostDatastoreBrowser(ManagedObject):
    props = {"datastore": {"MOR": True, "value": list()},
             "supportedType": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostDatastoreSystem(ManagedObject):
    props = {"capabilities": {"MOR": False, "value": None},
             "datastore": {"MOR": True, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostDateTimeSystem(ManagedObject):
    props = {"dateTimeInfo": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostDiagnosticSystem(ManagedObject):
    props = {"activePartition": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostFirmwareSystem(ManagedObject):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostHealthStatusSystem(ManagedObject):
    props = {"runtime": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostKernelModuleSystem(ManagedObject):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostLocalAccountManager(ManagedObject):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostPatchManager(ManagedObject):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostSnmpSystem(ManagedObject):
    props = {"configuration": {"MOR": False, "value": None},
             "limits": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HttpNfcLease(ManagedObject):
    props = {"error": {"MOR": False, "value": None},
             "info": {"MOR": False, "value": None},
             "initializeProgress": {"MOR": False, "value": None},
             "state": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class IpPoolManager(ManagedObject):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class LicenseAssignmentManager(ManagedObject):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class LicenseManager(ManagedObject):
    props = {"diagnostics": {"MOR": False, "value": None},
             "evaluation": {"MOR": False, "value": None},
             "featureInfo": {"MOR": False, "value": list()},
             "licenseAssignmentManager": {"MOR": True, "value": None},
             "licensedEdition": {"MOR": False, "value": None},
             "licenses": {"MOR": False, "value": list()},
             "source": {"MOR": False, "value": None},
             "sourceAvailable": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class LocalizationManager(ManagedObject):
    props = {"catalog": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class OptionManager(ManagedObject):
    props = {"setting": {"MOR": False, "value": list()},
             "supportedOptions": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class OvfManager(ManagedObject):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class PerformanceManager(ManagedObject):
    props = {"description": {"MOR": False, "value": None},
             "historicalInterval": {"MOR": False, "value": list()},
             "perfCounter": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class Profile(ManagedObject):
    props = {"complianceStatus": {"MOR": False, "value": None},
             "config": {"MOR": False, "value": None},
             "createdTime": {"MOR": False, "value": None},
             "description": {"MOR": False, "value": None},
             "entity": {"MOR": True, "value": list()},
             "modifiedTime": {"MOR": False, "value": None},
             "name": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class ClusterProfile(Profile):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostProfile(Profile):
    props = {"referenceHost": {"MOR": True, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class ProfileComplianceManager(ManagedObject):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class ProfileManager(ManagedObject):
    props = {"profile": {"MOR": True, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class ClusterProfileManager(ProfileManager):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostProfileManager(ProfileManager):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class PropertyCollector(ManagedObject):
    props = {"filter": {"MOR": True, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class PropertyFilter(ManagedObject):
    props = {"partialUpdates": {"MOR": False, "value": None},
             "spec": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class ResourcePlanningManager(ManagedObject):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class ScheduledTaskManager(ManagedObject):
    props = {"description": {"MOR": False, "value": None},
             "scheduledTask": {"MOR": True, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class SearchIndex(ManagedObject):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class ServiceInstance(ManagedObject):
    props = {"capability": {"MOR": False, "value": None},
             "content": {"MOR": False, "value": None},
             "clientClock": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client, properties=None):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class SessionManager(ManagedObject):
    props = {"currentSession": {"MOR": False, "value": None},
             "defaultLocale": {"MOR": False, "value": None},
             "message": {"MOR": False, "value": None},
             "messageLocaleList": {"MOR": False, "value": list()},
             "sessionList": {"MOR": False, "value": list()},
             "supportedLocaleList": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class TaskManager(ManagedObject):
    props = {"description": {"MOR": False, "value": None},
             "maxCollector": {"MOR": False, "value": None},
             "recentTask": {"MOR": True, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class UserDirectory(ManagedObject):
    props = {"domainList": {"MOR": False, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class View(ManagedObject):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class ManagedObjectView(View):
    props = {"view": {"MOR": True, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class ContainerView(ManagedObjectView):
    props = {"container": {"MOR": True, "value": None},
             "recursive": {"MOR": False, "value": None},
             "type": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class InventoryView(ManagedObjectView):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class ListView(ManagedObjectView):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class ViewManager(ManagedObject):
    props = {"viewList": {"MOR": True, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class VirtualDiskManager(ManagedObject):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class VirtualizationManager(ManagedObject):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class VirtualMachineCompatibilityChecker(ManagedObject):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class VirtualMachineProvisioningChecker(ManagedObject):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostAuthenticationManager(ManagedObject):
    props = {"info": {"MOR": False, "value": None},
             "supportedStore": {"MOR": True, "value": list()}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostAuthenticationStore(ManagedObject):
    props = {"info": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostDirectoryStore(HostAuthenticationStore):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class HostLocalAuthentication(HostAuthenticationStore):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())
    

class HostActiveDirectoryAuthentication(HostDirectoryStore):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())
    

class HostPowerSystem(ManagedObject):
    props = {"capability": {"MOR": False, "value": None},
             "info": {"MOR": False, "value": None}}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


class StorageResourceManager(ManagedObject):
    props = {}
    def __init__(self, mo_ref, client):
        super(self.__class__, self).__init__(mo_ref, client)
        self.props = dict(super(self.__class__, self).props.items() +
                          self.props.items())


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
    HostActiveDirectoryAuthentication,
    HostAuthenticationManager,
    HostAuthenticationStore,
    HostAutoStartManager,
    HostBootDeviceSystem,
    HostCpuSchedulerSystem,
    HostDatastoreBrowser,
    HostDatastoreSystem,
    HostDateTimeSystem,
    HostDiagnosticSystem,
    HostDirectoryStore,
    HostFirewallSystem,
    HostFirmwareSystem,
    HostHealthStatusSystem,
    HostKernelModuleSystem,
    HostLocalAccountManager,
    HostLocalAuthentication,
    HostMemorySystem,
    HostNetworkSystem,
    HostPatchManager,
    HostPciPassthruSystem,
    HostPowerSystem,
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
    StorageResourceManager,
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
    VmwareDistributedVirtualSwitch
))


def classmapper(name):
    return classmap[name]
