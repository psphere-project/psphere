#!/usr/bin/env python
# Copyright 2011 Jonathan Kinred
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
import time
import yaml

from psphere.client import Client
from psphere.errors import ObjectNotFoundError
from psphere.soap import VimFault
from psphere.scripting import BaseScript

class VMCreate(BaseScript):
    def create_vm(self, name, compute_resource, datastore, disksize, nics,
                  memory, num_cpus, guest_id, host=None):
        # If the host is not set, use the ComputeResource as the target
        if host is None:
            target = self.client.find_entity_view("ComputeResource",
                                          filter={"name": compute_resource})
            resource_pool = target.resourcePool
        else:
            target = self.client.find_entity_view("HostSystem",
                                                  filter={"name": host})
            resource_pool = target.parent.resourcePool

        # TODO: Convert the requested disk size to kb
        disksize_kb = disksize * 1024 * 1024

        # A list of devices to be assigned to the VM
        vm_devices = []

        # Create a disk controller
        controller = self.create_controller("VirtualLsiLogicController")
        vm_devices.append(controller)

        ds_to_use = None
        for ds in target.datastore:
            if ds.name == datastore:
                ds_to_use = ds
                break

        if ds_to_use is None:
            print("Could not find datastore on %s with name %s" %
                  (target.name, datastore))
            sys.exit()

        # Ensure the datastore is accessible and has enough space
        if ds_to_use.summary.accessible is not True:
            print("Datastore (%s) exists, but is not accessible" %
                  ds_to_use.summary.name)
            sys.exit()
        if ds_to_use.summary.freeSpace < disksize_kb * 1024:
            print("Datastore (%s) exists, but does not have sufficient"
                  " free space." % ds_to_use.summary.name)
            sys.exit()

        disk = self.create_disk(datastore=ds_to_use, disksize_kb=disksize_kb)
        vm_devices.append(disk)
        
        for nic in nics:
            nic_spec = self.create_nic(target, nic)
            if nic_spec is None:
                print("Could not create spec for NIC")
                sys.exit()

            # Append the nic spec to the vm_devices list
            vm_devices.append(nic_spec)

        vmfi = self.client.create("VirtualMachineFileInfo")
        vmfi.vmPathName = "[%s]" % ds_to_use.summary.name
        vm_config_spec = self.client.create("VirtualMachineConfigSpec")
        vm_config_spec.name = name
        vm_config_spec.memoryMB = memory
        vm_config_spec.files = vmfi
        vm_config_spec.annotation = "Auto-provisioned by psphere"
        vm_config_spec.numCPUs = num_cpus
        vm_config_spec.guestId = guest_id
        vm_config_spec.deviceChange = vm_devices

        # Find the datacenter of the target
        if target.__class__.__name__ == "HostSystem":
            datacenter = target.parent.parent.parent
        else:
            datacenter = target.parent.parent

        try:
            task = datacenter.vmFolder.CreateVM_Task(config=vm_config_spec,
                                                     pool=resource_pool._mo_ref)
        except VimFault, e:
            print("Failed to create %s: " % e)
            sys.exit()

        while task.info.state in ["queued", "running"]:
            time.sleep(5)
            task.update()
            print("Waiting 5 more seconds for VM creation")

        if task.info.state == "success":
            elapsed_time = task.info.completeTime - task.info.startTime
            print("Successfully created new VM %s. Server took %s seconds." %
                  (name, elapsed_time.seconds))
        elif task.info.state == "error":
            print("ERROR: The task for creating the VM has finished with"
                  " an error. If an error was reported it will follow.")
            try:
                print("ERROR: %s" % task.info.error.localizedMessage)
            except AttributeError:
                print("ERROR: There is no error message available.")
        else:
            print("UNKNOWN: The task reports an unknown state %s" %
                  task.info.state)

        # All done
        self.client.logout()

    def create_nic(self, target, nic):
        """Return a NIC spec"""
        # Iterate through the networks and look for one matching
        # the requested name
        for network in target.network:
            if network.name == nic["network_name"]:
                net = network
                break
            else:
                return None

        # Success! Create a nic attached to this network
        backing = (self.client.
               create("VirtualEthernetCardNetworkBackingInfo"))
        backing.deviceName = nic["network_name"]
        backing.network = net._mo_ref

        connect_info = self.client.create("VirtualDeviceConnectInfo")
        connect_info.allowGuestControl = True
        connect_info.connected = False
        connect_info.startConnected = True

        new_nic = self.client.create(nic["type"]) 
        new_nic.backing = backing
        new_nic.key = 2
        # TODO: Work out a way to automatically increment this
        new_nic.unitNumber = 1
        new_nic.addressType = "generated"
        new_nic.connectable = connect_info

        nic_spec = self.client.create("VirtualDeviceConfigSpec")
        nic_spec.device = new_nic
        nic_spec.fileOperation = None
        operation = (self.client.create("VirtualDeviceConfigSpecOperation"))
        nic_spec.operation = (operation.add)

        return nic_spec

    def create_controller(self, controller_type):
        controller = self.client.create(controller_type)
        controller.key = 0
        controller.device = [0]
        controller.busNumber = 0,
        controller.sharedBus = (self.client.
                                create("VirtualSCSISharing").noSharing)
        spec = self.client.create("VirtualDeviceConfigSpec")
        spec.device = controller
        spec.fileOperation = None
        spec.operation = (self.client.
                          create("VirtualDeviceConfigSpecOperation").add)
        return spec

    def create_disk(self, datastore, disksize_kb):
        backing = self.client.create("VirtualDiskFlatVer2BackingInfo")
        backing.datastore = None
        backing.diskMode = "persistent"
        backing.fileName = "[%s]" % datastore.summary.name
        backing.thinProvisioned = True

        disk = self.client.create("VirtualDisk")
        disk.backing = backing
        disk.controllerKey = 0
        disk.key = 0
        disk.unitNumber = 0
        disk.capacityInKB = disksize_kb

        disk_spec = self.client.create("VirtualDeviceConfigSpec")
        disk_spec.device = disk
        file_op = self.client.create("VirtualDeviceConfigSpecFileOperation")
        disk_spec.fileOperation = file_op.create
        operation = self.client.create("VirtualDeviceConfigSpecOperation")
        disk_spec.operation = operation.add

        return disk_spec

def main():
    #hosts = ["ssi4as1app01", "ssi4brmapp01", "ssi4chgapp01", "ssi4extapp01",
    #         "ssi4oamapp01", "ssi4oamapp02", "ssi4ppcapp01", "ssi4sdfosb01",
    #         "ssi4sdfosb02", "ssi4sdfosb03", "ssi4sdfstb01", "ssi4subapp01",
    #         "ssi4upeapp01"]
    client = Client()
    vmc = VMCreate(client)
    vm_file = open("vm_info.yml")
    vm_info = yaml.safe_load(vm_file)
    vm_file.close()
    nic = {"network_name": "AE_SDFDIE VLAN", "type": "VirtualE1000"}
    vmc.create_vm(vm_info["name"], vm_info["compute_resource"],
                  vm_info["datastore"], vm_info["disksize"], vm_info["nics"],
                  vm_info["memory"], vm_info["num_cpus"], vm_info["guest_id"])

if __name__ == "__main__":
    main()
