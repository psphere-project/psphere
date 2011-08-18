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

from psphere.scripting import BaseScript
from psphere.client import Client
from psphere.managedobjects import ComputeResource
from psphere.errors import ObjectNotFoundError

class Discovery(BaseScript):
    def discovery(self, compute_resource):
        """An example that discovers hosts and VMs in the inventory."""
        # Find the first ClusterComputeResource
        if compute_resource is None:
            cr_list = ComputeResource.all(self.client)
            print("ERROR: You must specify a ComputeResource.")
            print("Available ComputeResource's:")
            for cr in cr_list:
                print(cr.name)
            sys.exit(1)

        try:
            ccr = ComputeResource.get(self.client, name=compute_resource)
        except ObjectNotFoundError:
            print("ERROR: Could not find ComputeResource with name %s" %
                  compute_resource)
            sys.exit(1)

        print('Cluster: %s (%s hosts)' % (ccr.name, len(ccr.host)))

        ccr.preload("host", properties=["name", "vm"])
        for host in ccr.host:
            print('  Host: %s (%s VMs)' % (host.name, len(host.vm)))
            # Get the vm views in one fell swoop
            host.preload("vm", properties=["name"])
            for vm in host.vm:
                print('    VM: %s' % vm.name)
    
def main():
    client = Client()
    vd = Discovery(client)
    vd.discovery(sys.argv[1])

if __name__ == '__main__':
    main()
