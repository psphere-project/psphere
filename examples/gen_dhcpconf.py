#!/usr/bin/python
"""A script which generates DHCP configuration for hosts matching a regex.
Usage:
    gen_dhcpconf.py <regex> <compute_resource>
e.g.
    gen_dhcpconf.py 'ssi2+' 'Online Engineering'
"""

import re
import sys

from psphere.client import Client

client = Client()

host_regex = sys.argv[1]
p = re.compile(host_regex)
compute_resource = sys.argv[2]

cr = client.find_entity_view("ComputeResource",
                             filter={"name": compute_resource})

cr.resourcePool.preload("vm", properties=["name"])
for vm in sorted(cr.resourcePool.vm):
    if p.match(vm.name) is None:
        continue

    print("host %s {" % vm.name)
    print("    option host-name \"%s\";" % vm.name)
    nic_found = False
    for device in vm.config.hardware.device:
        if "macAddress" in device:
            print("    hardware ethernet %s;" % device["macAddress"])
            nic_found = True
    if nic_found is False:
        print("ERROR: Did not find a NIC to get MAC address from.")
        sys.exit(1)
    try:
        print("    fixed-address %s;" % vm.guest.ipAddress)
    except AttributeError:
        print("    fixed-address <manual_entry>;")
    print("}")

client.logout()
