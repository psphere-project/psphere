#!/usr/bin/python
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

from optparse import OptionParser

from psphere.vim25 import Vim
from psphere import host_utils

parser = OptionParser()
parser.add_option('--url', dest='url', help='the url of the vSphere server')
parser.add_option('--username', dest='username', help='the username to connnect with')
parser.add_option('--password', dest='password', help='the password to connect with')

(option, args) = parser.parse_args()

vim = Vim(config.url)
vim.login(config.username, config.password)

def create_conf_spec():
    shared_bus = vim.create_object('VirtualSCSISharing')
    controller = vim.create_object('VirtualLsiLogicController')
    controller.key = 0
    controller.device = [0]
    controller.busNumber = 0,
    controller.sharedBus = shared_bus.noSharing

    operation = vim.create_object('VirtualDeviceConfigSpecOperation')
    spec = vim.create_object('VirtualDeviceConfigSpec')
    spec.device = controller
    spec.operation = operation.add
    return spec

def create_virtual_disk(ds_path, disksize):
    disk_backing_info = vim.create_object('VirtualDiskFlatVer2BackingInfo')
    disk_backing_info.diskMode = 'persistent'
    disk_backing_info.fileName = ds_path

    disk = vim.create_object('VirtualDisk')
    disk.backing = disk_backing_info
    disk.controllerKey = 0
    disk.key = 0
    disk.unitNumber = 0
    disk.capacityInKB = disksize

    disk_vm_dev_conf_spec = vim.create_object('VirtualDeviceConfigSpec')
    disk_vm_dev_conf_spec.device = disk
    file_op_spec = vim.create_object('VirtualDeviceConfigSpecOperation')
    disk_vm_dev_conf_spec.fileOperation = file_op_spec.add

    return disk_vm_dev_conf_spec

def create_nic(network_name, poweron, host_view):
    """Create a VirtualDeviceConfigSpec for the NIC.

    Arguments:
        network_name: The name of the network the NIC resides on.
        poweron: Boolean. Whether to start connected.
        host_view: A view of the host/cluster on which the VM is being created.
    """

    # VirtualDevice.unitNumber. 0 is used by the VirtualDisk
    unit_num = 1

    if(network_name):
        network_list = vim.get_views(host_view.network)
        for n in network_list:
            if network_name == n.name:
                network = n
                nic_backing_info = vim.create_object(
                    'VirtualEthernetCardNetworkBackingInfo')
                nic_backing_info.deviceName = network.name
                nic_backing_info.network = network

                vd_connect_info = vim.create_object('VirtualDeviceConnectInfo')
                vd_connect_info.allowGuestControl = True
                vd_connect_info.connected = True
                vd_connect_info.startConnected = poweron

def create_vm(vmname, vmhost, datacenter, guestid, datastore, disksize,
              memory, num_cpus, nic_network, nic_poweron):
    host_view = vim.find_entity_view('ClusterComputeResource', {'name': vmhost})
    ds_info = host_utils.get_datastore(host_view, disksize, datastore)
    if not ds_info.mor:
        if ds_info.name == 'datastore_error':
            print('Error creating VM "%s": Datastore %s not available' %
                  (vmname, datastore))
            return None

        if ds_info.name == 'disksize_error':
            print('Error creating VM "%s": Not enough free space on %s' %
                  (vmname, datastore))
            return None

    ds_path = '[%s]' % ds_info.name

    controller_vm_dev_conf_spec = create_controller()
    disk_vm_dev_conf_spec = create_virtual_disk(ds_path, disksize)

    net_info = create_nic(nic_network, nic_poweron, host_view)
    if net_info['error']:
        print('Error creating VM "%s": Network "%s" not found' % (vmname,
                                                                  nic_network))
        return None

    vm_devices = []
    vm_devices.append(net_info['nic_conf'])
    vm_devices.append(controller_vm_dev_conf_spec)
    vm_devices.append(disk_vm_dev_conf_spec)

    files = vim.create_object('VirtualMachingFileInfo')
    files.vmPathName = ds_path

    vm_config_spec = vim.create_object('VirtualMachineConfigSpec')
    vm_config_spec.name = vmname
    vm_config_spec.memoryMB = memory
    vm_config_spec.files = files
    vm_config_spec.numCPUs = num_cpus
    vm_config_spec.guestId = guestid
    vm_config_spec.deviceChange = vm_devices

    datacenter_views = vim.find_entity_views('Datacenter', {'name': datacenter})
    if not datacenter_views:
        print('Error creating VM "%s":' % vmname)
        print('Datacenter "%s" not found' % datacenter)
        return False

    if len(datacenter_views) > 1:
        print('Error creating VM "%s":' % vmname)
        print('Datacenter "%s" not found' % datacenter)
        return False

    datacenter = datacenter_views[0]

    vm_folder_view = vim.get_view(datacenter.vmFolder)

    comp_res_view = vim.get_view(host_view.parent)
    
