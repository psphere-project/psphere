#!/usr/bin/env python
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

import sys
from psphere.vim25 import ObjectNotFoundError
from psphere.soap import VimFault
from psphere.scripting import BaseScript

class VMCreate(BaseScript):
    def create_vm(self, compute_resource, datastore, disksize, nics, name,
                  memory, num_cpus, guest_id, host=None):
        # If the host is not set, use the ComputeResource as the target
        if not host:
            target = self.vim.find_entity_view(view_type='ComputeResource',
                                            filter={'name': compute_resource})
            target.update_view_data(['name', 'datastore', 'network', 'parent',
                                     'resourcePool'])
            resource_pool = target.resourcePool
        else:
            target = self.vim.find_entity_view(view_type='HostSystem',
                                                filter={'name': host})
            # Retrieve the properties we're going to use
            target.update_view_data(['name', 'datastore', 'network', 'parent'])
            host_cr = self.vim.get_view(mo_ref=target.parent, vim=self.vim)
            host_cr.update_view_data(properties=['resourcePool'])
            resource_pool = host_cr.resourcePool

        # TODO: Convert the requested disk size to kb
        disksize_kb = disksize * 1024 * 1024

        # A list of devices to be assigned to the VM
        vm_devices = []

        # Create a disk controller
        controller = self.create_controller('VirtualLsiLogicController')
        vm_devices.append(controller)

        # Find the given datastore and ensure it is suitable
        if host:
            ds_target = host_cr
        else:
            ds_target = target

        try:
            ds = ds_target.find_datastore(name=datastore)
        except ObjectNotFoundError, e:
            print('Could not find datastore with name %s: %s' % (datastore,
                                                                 e.error))
            sys.exit()

        ds.update_view_data(properties=['summary'])
        # Ensure the datastore is accessible and has enough space
        if (not ds.summary.accessible or
            ds.summary.freeSpace < disksize_kb * 1024):
            print('Datastore (%s) exists, but is not accessible or'
                  'does not have sufficient free space.' % ds.summary.name)
            sys.exit()

        disk = self.create_disk(datastore=ds, disksize_kb=disksize_kb)
        vm_devices.append(disk)
        
        for nic in nics:
            nic_spec = self.create_nic(target, nic)
            if not nic_spec:
                print('Could not create spec for NIC')
                sys.exit()

            # Append the nic spec to the vm_devices list
            vm_devices.append(nic_spec)

        vmfi = self.vim.create_object('VirtualMachineFileInfo')
        vmfi.vmPathName = '[%s]' % ds.summary.name
        vm_config_spec = self.vim.create_object('VirtualMachineConfigSpec')
        vm_config_spec.name = name
        vm_config_spec.memoryMB = memory
        vm_config_spec.files = vmfi
        vm_config_spec.annotation = 'Auto-provisioned by pSphere'
        vm_config_spec.numCPUs = num_cpus
        vm_config_spec.guestId = guest_id
        vm_config_spec.deviceChange = vm_devices

        # Find the datacenter of the target
        try:
            dc = target.find_datacenter()
        except ObjectNotFoundError, e:
            print('Error while trying to find datacenter for %s: %s' %
                  (target.name, e.error))
            sys.exit()

        dc.update_view_data(properties=['vmFolder'])

        try:
            self.vim.invoke_task('CreateVM_Task', _this=dc.vmFolder,
                                 config=vm_config_spec, pool=resource_pool)
        except VimFault, e:
            print('Failed to create %s: ' % e)
            sys.exit()

        print('Successfully created new VM: %s' % name)
        self.vim.logout()

    def create_nic(self, target, nic):
        """Return a NIC spec"""
        # Get all the networks associated with the HostSystem/ComputeResource
        networks = self.vim.get_views(mo_refs=target.network, properties=['name'])

        # Iterate through the networks and look for one matching
        # the requested name
        for network in networks:
            if network.name == nic['network_name']:
                # Success! Create a nic attached to this network
                backing = (self.vim.
                       create_object('VirtualEthernetCardNetworkBackingInfo'))
                backing.deviceName = nic['network_name']
                backing.network = network.mo_ref

                connect_info = (self.vim.
                                create_object('VirtualDeviceConnectInfo'))
                connect_info.allowGuestControl = True
                connect_info.connected = False
                connect_info.startConnected = True

                new_nic = self.vim.create_object(nic['type']) 
                new_nic.backing = backing
                new_nic.key = 2
                # TODO: Work out a way to automatically increment this
                new_nic.unitNumber = 1
                new_nic.addressType = 'generated'
                new_nic.connectable = connect_info

                nic_spec = self.vim.create_object('VirtualDeviceConfigSpec')
                nic_spec.device = new_nic
                operation = (self.vim.
                             create_object('VirtualDeviceConfigSpecOperation'))
                nic_spec.operation = (operation.add)

                return nic_spec

    def create_controller(self, controller_type):
        controller = self.vim.create_object(controller_type)
        controller.key = 0
        controller.device = [0]
        controller.busNumber = 0,
        controller.sharedBus = (self.vim.
                                create_object('VirtualSCSISharing').noSharing)

        spec = self.vim.create_object('VirtualDeviceConfigSpec')
        spec.device = controller
        spec.operation = (self.vim.
                          create_object('VirtualDeviceConfigSpecOperation').add)

        return spec

    def create_disk(self, datastore, disksize_kb):
        backing = (self.vim.create_object('VirtualDiskFlatVer2BackingInfo'))
        backing.diskMode = 'persistent'
        backing.fileName = '[%s]' % datastore.summary.name

        disk = self.vim.create_object('VirtualDisk')
        disk.backing = backing
        disk.controllerKey = 0
        disk.key = 1
        disk.unitNumber = 0
        disk.capacityInKB = disksize_kb

        disk_spec = self.vim.create_object('VirtualDeviceConfigSpec')
        disk_spec.device = disk
        file_op = self.vim.create_object('VirtualDeviceConfigSpecFileOperation')
        disk_spec.fileOperation = file_op.create
        operation = self.vim.create_object('VirtualDeviceConfigSpecOperation')
        disk_spec.operation = operation.add

        return disk_spec

def main():
    vmc = VMCreate()
    vmc.login()
    nic = {'network_name': 'AE_SDFDIE VLAN', 'type': 'VirtualE1000'}
    vmc.create_vm(compute_resource='Application Engineering',
                       datastore='nas03', disksize=12, nics=[nic],
                       name='test', memory=1024, num_cpus=1,
                       guest_id='rhel5Guest')

if __name__ == '__main__':
    main()

