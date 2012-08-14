#!/usr/bin/python

import time
import sys

from psphere.client import Client
from psphere.managedobjects import VirtualMachine

scatter_secs = 8

nodes = sys.argv[1:]

client = Client()

print("Powering on %s VMs" % len(nodes))
print("Estimated run time with %s seconds sleep between each power on: %s" %
      (scatter_secs, scatter_secs*len(nodes)))

for node in nodes:
    try:
        vm = VirtualMachine.get(client, name=node, properties=["name", "runtime"])
    except ObjectNotFoundError:
        print("WARNING: Could not find VM with name %s" % node)
        pass

    print("Powering on %s" % vm.name)
    if vm.runtime.powerState == "poweredOn":
        print("%s is already powered on." % vm.name)
        continue

    task = vm.PowerOnVM_Task()
    time.sleep(scatter_secs)
