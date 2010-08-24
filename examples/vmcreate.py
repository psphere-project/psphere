#!/usr/bin/env python
#
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

import optparse
import sys
import psphere.vim25

def main(options):
    vim = psphere.vim25.Vim(options.url, options.username, options.password)
    create_vm(vim, 'Application Engineering', 'nas03', 12582912,
              [{'network_name': 'AE_SDFDIE VLAN'}], 'test', 1024, 1,
              'rhel5Guest', 'Dalley St')

def create_vm(vim, compute_resource, datastore, disksize, nics, name, memory,
              num_cpus, guest_id, datacenter):
    compute_resource_view = vim.find_entity_view(
                                        view_type='ClusterComputeResource',
                                        filter={'name': compute_resource})

    compute_resource_view.update_view_data(['name', 'datastore',
                                            'network', 'resourcePool'])

    # Build a list of devices for the VM
    vm_devices = []
    controller_spec = create_controller_spec(vim, 'VirtualLsiLogicController')
    vm_devices.append(controller_spec)

    # Find the given datastore and ensure it is suitable
    datastore = get_datastore(vim, compute_resource_view, datastore)
    if not datastore:
        print('No datastore found with name %s' % datastore)
        sys.exit()

    free_space_kb = datastore.summary.freeSpace / 1024
    # Ensure the datastore is accessible
    if not datastore.summary.accessible or free_space_kb < disksize:
        print('Datastore (%s) exists, but is not accessible or'
              'does not have sufficient free space.' % datastore.summary.name)
        sys.exit()

    disk_spec = create_virtual_disk(vim, datastore=datastore,
                                    disksize=disksize)
    vm_devices.append(disk_spec)
    
    for nic in nics:
        nic_spec = get_nic_spec(vim, compute_resource_view,
                                'VirtualE1000', nic['network_name'])
        if not nic_spec:
            print('Could not create spec for NIC')
            sys.exit()

        # Append the nic spec to the vm_devices list
        vm_devices.append(nic_spec)

    files = vim.vsoap.create_object('VirtualMachineFileInfo')
    files.vmPathName = '[%s]' % datastore.summary.name

    vm_config_spec = vim.vsoap.create_object('VirtualMachineConfigSpec')
    vm_config_spec.name = name
    vm_config_spec.memoryMB = memory
    vm_config_spec.files = files
    vm_config_spec.annotation = 'Auto-provisioned by vmcreate.py script'
    vm_config_spec.numCPUs = num_cpus
    vm_config_spec.guestId = guest_id
    vm_config_spec.deviceChange = vm_devices

    datacenter_view = vim.find_entity_view(view_type='Datacenter',
                                           filter={'name': datacenter})
    if not datacenter_view:
        print('Could not find datacenter %s' % datacenter)
        sys.exit()

    datacenter_view.update_view_data(properties=['name', 'vmFolder'])
    vmfolder_view = vim.get_mo_view(mor=datacenter_view.vmFolder)

    result = vmfolder_view.create_vm(config=vm_config_spec,
                                     pool=compute_resource_view.resourcePool)

    if result['error_message']:
        print('Error while creating VM: %s' % result['error_message'])
    else:
        print('Successfully created VM: %s' % name)

def get_nic_spec(vim, compute_resource_view, nic_type, network_name):
    """Return a NIC spec"""
    # Get all the networks associated with the compute resource
    networks = vim.get_mo_views(mors=compute_resource_view.network,
                                properties=['name'])
    # Iterate through the networks and look for one matching the requested name
    for network in networks:
        if network.name == network_name:
            # Success! Create a nic attached to this network
            backing = (vim.vsoap.
                       create_object('VirtualEthernetCardNetworkBackingInfo'))
            backing.deviceName = network_name
            backing.network = network.mor

            connect_info = vim.vsoap.create_object('VirtualDeviceConnectInfo')
            connect_info.allowGuestControl = True
            connect_info.connected = False
            connect_info.startConnected = True

            nic = vim.vsoap.create_object(nic_type) 
            nic.backing = backing
            nic.key = 0
            # TODO: Work out a way to automatically increment this
            nic.unitNumber = 1
            nic.addressType = 'generated'
            nic.connectable = connect_info

            nic_spec = vim.vsoap.create_object('VirtualDeviceConfigSpec')
            nic_spec.device = nic
            operation = vim.vsoap.create_object(
                                            'VirtualDeviceConfigSpecOperation')
            nic_spec.operation = (operation.add)
            return nic_spec

def get_datastore(vim, compute_resource_view, name=None):
    """Find a datastore on the given managed object by name.

    Parameters
    ----------
    vim : Vim
        The base Vim instance to use for vSphere related operations.
    compute_resource_view : {'ClusterComputeResource', 'ComputeResource'}
        The entity on which the datastore should be found.
    name : str, optional
        The name of the datastore to be found. If name is not specified
        then the first available datastore will be used.

    Returns
    -------
    datastore : Datastore
        A Datastore view instance.

    Raises
    ------
    DatastoreException
        If there is a problem (inaccessible, insufficient free space) with
        the desired datastore.

    """
    # TODO: Implement selection of datastore if name is not specified
    if not name:
        print('Auto-selection of datastore not implemented.')
        return None

    # Retrieve the datastores associated with the host
    datastores = vim.get_mo_views(mors=compute_resource_view.datastore,
                                  properties=['info', 'summary'])

    # Iterate throught the datastores for one matching `name`
    for datastore in datastores:
        if datastore.info.name == name:
            return datastore 

    return None

def create_controller_spec(vim, controller_type):
    controller = vim.vsoap.create_object(controller_type)
    controller.key = 0
    controller.device = [0]
    controller.busNumber = 0,
    controller.sharedBus = (vim.vsoap.
                            create_object('VirtualSCSISharing').noSharing)

    spec = vim.vsoap.create_object('VirtualDeviceConfigSpec')
    spec.device = controller
    spec.operation = (vim.vsoap.
                      create_object('VirtualDeviceConfigSpecOperation').add)

    return spec

def create_virtual_disk(vim, datastore, disksize):
    backing = (vim.vsoap.create_object('VirtualDiskFlatVer2BackingInfo'))
    backing.diskMode = 'persistent'
    backing.fileName = '[%s]' % datastore.summary.name

    disk = vim.vsoap.create_object('VirtualDisk')
    disk.backing = backing
    disk.controllerKey = 0
    disk.key = 0
    disk.unitNumber = 0
    disk.capacityInKB = disksize

    disk_spec = vim.vsoap.create_object('VirtualDeviceConfigSpec')
    disk_spec.device = disk
    operation = vim.vsoap.create_object('VirtualDeviceConfigSpecOperation')
    disk_spec.operation = (operation.add)

    return disk_spec

if __name__ == '__main__':
    usage = ('usage: %prog --url https://<host>/sdk --username <username> '
             '--password <password>')
    parser = optparse.OptionParser(usage)
    parser.add_option('--url', dest='url',
                      help='the url of the vSphere server')
    parser.add_option('--username', dest='username',
                      help='the username to connnect with')
    parser.add_option('--password', dest='password',
                      help='the password to connect with')

    (options, args) = parser.parse_args()

    if not options.url:
        parser.error('--url option is required')
    if not options.username:
        parser.error('--username option is required')
    if not options.password:
        parser.error('--password option is required')

    # Call the main method with the passed in arguments
    main(options)

