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

import re
import sys
import time

from psphere import config, template
from psphere.client import Client
from psphere.errors import TemplateNotFoundError
from psphere.soap import VimFault

def create_vm(client, name, compute_resource, datastore, disksize, nics,
              memory, num_cpus, guest_id, host=None):
    """Create a virtual machine using the specified values.

    :param name: The name of the VM to create.
    :type name: str
    :param compute_resource: The name of a ComputeResource in which to \
            create the VM.
    :type compute_resource: str
    :param datastore: The name of the datastore on which to create the VM.
    :type datastore: str
    :param disksize: The size of the disk, specified in KB, MB or GB. e.g. \
            20971520KB, 20480MB, 20GB.
    :type disksize: str
    :param nics: The NICs to create, specified in a list of dict's which \
            contain a "network_name" and "type" key. e.g. \
            {"network_name": "VM Network", "type": "VirtualE1000"}
    :type nics: list of dict's
    :param memory: The amount of memory for the VM. Specified in KB, MB or \
            GB. e.g. 2097152KB, 2048MB, 2GB.
    :type memory: str
    :param num_cpus: The number of CPUs the VM will have.
    :type num_cpus: int
    :param guest_id: The vSphere string of the VM guest you are creating. \
            The list of VMs can be found at \
        http://www.vmware.com/support/developer/vc-sdk/visdk41pubs/ApiReference/index.html
    :type guest_id: str
    :param host: The name of the host (default: None), if you want to \
            provision the VM on a \ specific host.
    :type host: str

    """
    print("Creating VM %s" % name)
    # If the host is not set, use the ComputeResource as the target
    if host is None:
        target = client.find_entity_view("ComputeResource",
                                      filter={"name": compute_resource})
        resource_pool = target.resourcePool
    else:
        target = client.find_entity_view("HostSystem", filter={"name": host})
        resource_pool = target.parent.resourcePool

    disksize_pattern = re.compile("^\d+[KMG]B")
    if disksize_pattern.match(disksize) is None:
        print("Disk size %s is invalid. Try \"12G\" or similar" % disksize)
        sys.exit(1)

    if disksize.endswith("GB"):
        disksize_kb = int(disksize[:-2]) * 1024 * 1024
    elif disksize.endswith("MB"):
        disksize_kb = int(disksize[:-2]) * 1024
    elif disksize.endswith("KB"):
        disksize_kb = int(disksize[:-2])
    else:
        print("Disk size %s is invalid. Try \"12G\" or similar" % disksize)

    memory_pattern = re.compile("^\d+[KMG]B")
    if memory_pattern.match(memory) is None:
        print("Memory size %s is invalid. Try \"12G\" or similar" % memory)
        sys.exit(1)

    if memory.endswith("GB"):
        memory_mb = int(memory[:-2]) * 1024
    elif memory.endswith("MB"):
        memory_mb = int(memory[:-2])
    elif memory.endswith("KB"):
        memory_mb = int(memory[:-2]) / 1024
    else:
        print("Memory size %s is invalid. Try \"12G\" or similar" % memory)

    # A list of devices to be assigned to the VM
    vm_devices = []

    # Create a disk controller
    controller = create_controller(client, "VirtualLsiLogicController")
    vm_devices.append(controller)

    ds_to_use = None
    for ds in target.datastore:
        if ds.name == datastore:
            ds_to_use = ds
            break

    if ds_to_use is None:
        print("Could not find datastore on %s with name %s" %
              (target.name, datastore))
        sys.exit(1)

    # Ensure the datastore is accessible and has enough space
    if ds_to_use.summary.accessible is not True:
        print("Datastore (%s) exists, but is not accessible" %
              ds_to_use.summary.name)
        sys.exit(1)
    if ds_to_use.summary.freeSpace < disksize_kb * 1024:
        print("Datastore (%s) exists, but does not have sufficient"
              " free space." % ds_to_use.summary.name)
        sys.exit(1)

    disk = create_disk(client, datastore=ds_to_use, disksize_kb=disksize_kb)
    vm_devices.append(disk)
    
    for nic in nics:
        nic_spec = create_nic(client, target, nic)
        if nic_spec is None:
            print("Could not create spec for NIC")
            sys.exit(1)

        # Append the nic spec to the vm_devices list
        vm_devices.append(nic_spec)

    vmfi = client.create("VirtualMachineFileInfo")
    vmfi.vmPathName = "[%s]" % ds_to_use.summary.name
    vm_config_spec = client.create("VirtualMachineConfigSpec")
    vm_config_spec.name = name
    vm_config_spec.memoryMB = memory_mb
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
                                                 pool=resource_pool)
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

def create_nic(client, target, nic):
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
    backing = client.create("VirtualEthernetCardNetworkBackingInfo")
    backing.deviceName = nic["network_name"]
    backing.network = net

    connect_info = client.create("VirtualDeviceConnectInfo")
    connect_info.allowGuestControl = True
    connect_info.connected = False
    connect_info.startConnected = True

    new_nic = client.create(nic["type"]) 
    new_nic.backing = backing
    new_nic.key = 2
    # TODO: Work out a way to automatically increment this
    new_nic.unitNumber = 1
    new_nic.addressType = "generated"
    new_nic.connectable = connect_info

    nic_spec = client.create("VirtualDeviceConfigSpec")
    nic_spec.device = new_nic
    nic_spec.fileOperation = None
    operation = client.create("VirtualDeviceConfigSpecOperation")
    nic_spec.operation = (operation.add)

    return nic_spec

def create_controller(client, controller_type):
    controller = client.create(controller_type)
    controller.key = 0
    controller.device = [0]
    controller.busNumber = 0,
    controller.sharedBus = client.create("VirtualSCSISharing").noSharing
    spec = client.create("VirtualDeviceConfigSpec")
    spec.device = controller
    spec.fileOperation = None
    spec.operation = client.create("VirtualDeviceConfigSpecOperation").add
    return spec

def create_disk(client, datastore, disksize_kb):
    backing = client.create("VirtualDiskFlatVer2BackingInfo")
    backing.datastore = None
    backing.diskMode = "persistent"
    backing.fileName = "[%s]" % datastore.summary.name
    backing.thinProvisioned = True

    disk = client.create("VirtualDisk")
    disk.backing = backing
    disk.controllerKey = 0
    disk.key = 0
    disk.unitNumber = 0
    disk.capacityInKB = disksize_kb

    disk_spec = client.create("VirtualDeviceConfigSpec")
    disk_spec.device = disk
    file_op = client.create("VirtualDeviceConfigSpecFileOperation")
    disk_spec.fileOperation = file_op.create
    operation = client.create("VirtualDeviceConfigSpecOperation")
    disk_spec.operation = operation.add

    return disk_spec

def main(name, options):
    """The main method for this script.

    :param name: The name of the VM to create.
    :type name: str
    :param template_name: The name of the template to use for creating \
            the VM.
    :type template_name: str

    """
    server = config._config_value("general", "server", options.server)
    if server is None:
        raise ValueError("server must be supplied on command line"
                         " or in configuration file.")
    username = config._config_value("general", "username", options.username)
    if username is None:
        raise ValueError("username must be supplied on command line"
                         " or in configuration file.")
    password = config._config_value("general", "password", options.password)
    if password is None:
        raise ValueError("password must be supplied on command line"
                         " or in configuration file.")

    vm_template = None
    if options.template is not None:
        try:
            vm_template = template.load_template(options.template)
        except TemplateNotFoundError:
            print("ERROR: Template \"%s\" could not be found." % options.template)
            sys.exit(1)

    expected_opts = ["compute_resource", "datastore", "disksize", "nics",
                     "memory", "num_cpus", "guest_id", "host"]

    vm_opts = {}
    for opt in expected_opts:
        vm_opts[opt] = getattr(options, opt)
        if vm_opts[opt] is None:
            if vm_template is None:
                raise ValueError("%s not specified on the command line and"
                                 " you have not specified any template to"
                                 " inherit the value from." % opt)
            try:
                vm_opts[opt] = vm_template[opt]
            except AttributeError:
                raise ValueError("%s not specified on the command line and"
                                 " no value is provided in the specified"
                                 " template." % opt)

    client = Client(server=server, username=username, password=password)
    create_vm(client, name, vm_opts["compute_resource"], vm_opts["datastore"],
              vm_opts["disksize"], vm_opts["nics"], vm_opts["memory"],
              vm_opts["num_cpus"], vm_opts["guest_id"], host=vm_opts["host"])
    client.logout()

if __name__ == "__main__":
    from optparse import OptionParser
    usage = "Usage: %prog [options] name"
    parser = OptionParser(usage=usage)
    parser.add_option("--server", dest="server",
                      help="The server to connect to for provisioning")
    parser.add_option("--username", dest="username",
                      help="The username used to connect to the server")
    parser.add_option("--password", dest="password",
                      help="The password used to connect to the server")
    parser.add_option("--template", dest="template",
                      help="The template used to create the VM")
    parser.add_option("--compute_resource", dest="compute_resource",
                      help="The ComputeResource in which to provision the VM")
    parser.add_option("--datastore", dest="datastore",
                      help="The datastore on which to provision the VM")
    parser.add_option("--disksize", dest="disksize",
                      help="The size of the VM disk")
    parser.add_option("--nics", dest="nics",
                      help="The nics for the VM")
    parser.add_option("--memory", dest="memory",
                      help="The amount of memory for the VM")
    parser.add_option("--num_cpus", dest="num_cpus",
                      help="The number of CPUs for the VM")
    parser.add_option("--guest_id", dest="guest_id",
                      help="The guest_id of the VM (see vSphere doco)")
    parser.add_option("--host", dest="host",
                      help="Specify this if you want to provision the VM on a"
                      " specific host in the ComputeResource")

    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.print_help()
        sys.exit(1)

    main(args[0], options)
