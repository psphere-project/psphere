#!/usr/bin/python
"""A script which demonstrates how to reconfigure a VM.
Usage:
    reconfig_vm.py <vm_name>
e.g.
    reconfig_vm test

"""

import sys
import time

from psphere.client import Client
from psphere.soap import VimFault
from psphere.managedobjects import VirtualMachine
from psphere.errors import ObjectNotFoundError

vm_name = sys.argv[1]

client = Client()
new_config = client.create("VirtualMachineConfigSpec")
new_config.numCPUs = 2

try:
    vm = VirtualMachine.get(client, name=vm_name)
except ObjectNotFoundError:
    print("ERROR: No VM found with name %s" % vm_name)

print("Reconfiguring %s" % vm_name)
if vm.config.hardware.numCPU == 2:
    print("Not reconfiguring %s as it already has 2 CPUs" % vm_name)
    sys.exit()

try:
    task = vm.ReconfigVM_Task(spec=new_config)
except VimFault, e:
    print("Failed to reconfigure %s: " % e)
    sys.exit()

while task.info.state in ["queued", "running"]:
    print("Waiting 5 more seconds for VM creation")
    time.sleep(5)
    task.update()

if task.info.state == "success":
    elapsed_time = task.info.completeTime - task.info.startTime
    print("Successfully reconfigured VM %s. Server took %s seconds." %
          (vm_name, elapsed_time.seconds))
elif task.info.state == "error":
    print("ERROR: The task for reconfiguring the VM has finished with"
          " an error. If an error was reported it will follow.")
    try:
        print("ERROR: %s" % task.info.error.localizedMessage)
    except AttributeError:
        print("ERROR: There is no error message available.")
else:
    print("UNKNOWN: The task reports an unknown state %s" %
          task.info.state)

# All done
client.logout()
