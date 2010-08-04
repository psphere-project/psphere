#!/usr/bin/env python

from psphere.vim25 import Vim, HostSystem, VirtualMachine

vim = Vim('https://bennevis/sdk', 'Administrator', 'SunF1re!')

name = 'Dalley St'
ccs = vim.find_entity(entity_type='ClusterComputeResource', filter=['name'])
if ccs == None:
    print('No host found with name %s' % name)

for host in ccs.host:
    h = HostSystem(host, vim)
    print('Host: %s' % h.name)
    for vm in h.vm:
        v = VirtualMachine(vm, vim)
        print('  VM: %s' % v.name)
