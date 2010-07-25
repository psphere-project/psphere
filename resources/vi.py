from suds.client import Client
from suds.sudsobject import Property

import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').setLevel(logging.DEBUG)
#logging.getLogger('suds.wsdl').setLevel(logging.DEBUG)

url = 'https://bennevis/sdk/vimService?wsdl'

client = Client(url)

client.set_options(location='https://bennevis/sdk')

mo_ServiceInstance = Property('ServiceInstance')
mo_ServiceInstance._type = 'ServiceInstance'

ServiceContent = client.service.RetrieveServiceContent(mo_ServiceInstance)

mo_SessionManager = Property(ServiceContent.sessionManager.value)
mo_SessionManager._type = 'SessionManager'

SessionManager = client.service.Login(mo_SessionManager, 'Administrator', '')

print "Login Time: {0}".format( SessionManager.loginTime )

# Traversal Specs
FolderTraversalSpec = client.factory.create('ns0:TraversalSpec')
DatacenterVMTraversalSpec = client.factory.create('ns0:TraversalSpec')

FolderSelectionSpec = client.factory.create('ns0:SelectionSpec')
DatacenterVMSelectionSpec = client.factory.create('ns0:SelectionSpec')

FolderSelectionSpec.name = "FolderTraversalSpec"
DatacenterVMSelectionSpec.name = "DatacenterVMTraversalSpec"

DatacenterVMTraversalSpec.name = "DatacenterVMTraversalSpec"
DatacenterVMTraversalSpec.type = "Datacenter"
DatacenterVMTraversalSpec.path = "vmFolder"
DatacenterVMTraversalSpec.skip = True

FolderTraversalSpec.name = "FolderTraversalSpec"
FolderTraversalSpec.type = "Folder"
FolderTraversalSpec.path = "childEntity"
FolderTraversalSpec.skip = True

DatacenterVMTraversalSpec.selectSet = [FolderSelectionSpec]
FolderTraversalSpec.selectSet = [DatacenterVMSelectionSpec, FolderSelectionSpec]

# Property Spec

propSpec = client.factory.create('ns0:PropertySpec')
propSpec.all = False
propSpec.pathSet = ["name", "runtime.powerState"]
propSpec.type = "VirtualMachine"

# Object Spec

mo_RootFolder = Property(ServiceContent.rootFolder.value)
mo_RootFolder._type = 'Folder'

objSpec = client.factory.create('ns0:ObjectSpec')
objSpec.obj = mo_RootFolder
objSpec.selectSet = [ FolderTraversalSpec, DatacenterVMTraversalSpec ]

# PropertyFilterSpec

propFilterSpec = client.factory.create('ns0:PropertyFilterSpec')
propFilterSpec.propSet = [ propSpec ]
propFilterSpec.objectSet = [ objSpec ]

# RetrieveProperties

mo_PropertyCollector = Property(ServiceContent.propertyCollector.value)
mo_PropertyCollector._type = 'PropertyCollector'
objContent = client.service.RetrieveProperties(mo_PropertyCollector, propFilterSpec)

# print results

def properties_to_dict(entity):
	props = {}
	
	props['_type'] = entity.obj._type
	props['mo_ref'] = entity.obj.value
	
	for dynProp in entity.propSet:
		props[dynProp.name] = dynProp.val
	
	return props
	
virtual_machines = map(properties_to_dict, objContent)

for vm in virtual_machines:
	print "Virtual Machine: {0} (PowerState: {1})".format(vm['name'], vm['runtime.powerState'])







