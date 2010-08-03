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

si = ServiceInstance(option.url, option.username, option.password)

def create_conf_spec():
    controller = si.vs.create_object('VirtualLsiLogicController')
    controller.key = 0
    controller.device = [0]
    controller.busNumber = 0,
    controller.sharedBus = si.vs.create_object('VirtualSCSISharing').noSharing

    spec = si.vs.create_object('VirtualDeviceConfigSpec')
    spec.device = controller
    spec.operation = si.vs.create_object('VirtualDeviceConfigSpecOperation').add

    return spec

def create_virtual_disk(ds_path, disksize):
    disk_backing_info = si.vs.create_object('VirtualDiskFlatVer2BackingInfo')
    disk_backing_info.diskMode = 'persistent'
    disk_backing_info.fileName = ds_path

    disk = si.vs.create_object('VirtualDisk')
    disk.backing = disk_backing_info
    disk.controllerKey = 0
    disk.key = 0
    disk.unitNumber = 0
    disk.capacityInKB = disksize

    disk_vm_dev_conf_spec = si.vs.create_object('VirtualDeviceConfigSpec')
    disk_vm_dev_conf_spec.device = disk
    file_op_spec = si.vs.create_object('VirtualDeviceConfigSpecOperation')
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
        for network in host_system.network:
            if network_name == n.name:
                network = n
                nic_backing_info = si.vs.create_object(
                    'VirtualEthernetCardNetworkBackingInfo')
                nic_backing_info.deviceName = network.name
                nic_backing_info.network = network

                vd_connect_info = si.vs.create_object(
                                              'VirtualDeviceConnectInfo')
                vd_connect_info.allowGuestControl = True
                vd_connect_info.connected = True
                vd_connect_info.startConnected = poweron

def create_vm(vmname, vmhost, datacenter, guestid, datastore, disksize,
              memory, num_cpus, nic_network, nic_poweron):
    """Create a virtual machine with the given arguments."""
    ccr_mor = si.find_entity('ClusterComputeResource', {'name': vmhost})
    ccr = ClusterComputeResource(mor=ccr_mor)
    for datastore in ccr.datastore:
        if datastore.name == datastore:
            if not datastore.summary.accessible:
                print("ERROR: Requested datastore is not accessible.")
                break

            if datastore.summary.freeSpace < disksize/1024:
                print("ERROR: Not enough free space on requested datastore.")
                break

            ds_path = '[%s]' % datastore.name
            break


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

    files = vim.create_object('VirtualMachineFileInfo')
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

    vm_folder_view = Folder(mor=datacenter.vmFolder)
    comp_res_view = vim.get_view(host_view.parent)
    
