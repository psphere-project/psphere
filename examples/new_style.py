#!/usr/bin/python

import sys

from psphere.client import Client
from psphere.managedobjects import HostSystem, VirtualMachine

client = Client(sys.argv[1], sys.argv[2], sys.argv[3])
host_systems = HostSystem.all(client)
print("HostSystem.all(client) finds these hosts")
for host_system in host_systems:
    print(host_system.name)

vm = VirtualMachine.get(client, name="genesis", overallStatus="green")

print('VirtualMachine.get(client, name="genesis", overallStatus="green")'
      ' got the following host:')
print("Name: %s" % vm.name)
print("overallStatus: %s" % vm.overallStatus)
