#!/usr/bin/python
"""A script which generates DHCP configuration for hosts matching a regex.
Usage:
    find_vms_by_regex.py <regex> <compute_resource>
e.g.
    find_vms_by_regex.py 'ssi2+' 'Online Engineering'
"""

import re
import sys

from psphere.client import Client
from psphere.managedobjects import ComputeResource

client = Client()

vm_regex = sys.argv[1]
p = re.compile(vm_regex)
compute_resource = sys.argv[2]

cr = ComputeResource.get(client, name=compute_resource)

cr.resourcePool.preload("vm", properties=["name"])
for vm in sorted(cr.resourcePool.vm):
    if p.match(vm.name) is None:
        continue
    print(vm.name)

client.logout()
