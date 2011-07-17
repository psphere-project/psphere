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

from psphere.scripting import BaseScript
from psphere.managedobjects import ClusterComputeResource

class Discovery(BaseScript):
    def discovery(self, url=None, username=None, password=None):
        """An example that discovers hosts and VMs in the inventory.

        Parameters
        ----------
        url : str
            The URL of the ESX or VIC server. e.g. (https://bennevis/sdk)
        username : str
            The username to connect with.
        password : str
            The password to connect with.

        """
        self.login()
        # Find the first ClusterComputeResource
        ccs = ClusterComputeResource.find_one(
                                    filter={'name': 'Application Engineering'},
                                    properties=['name', 'host'])
        print('Cluster: %s (%s hosts)' % (ccs.name, len(ccs.host)))

        for host in ccs.hosts:
            print('  Host: %s (%s VMs)' % (host.name, len(host.vm)))
            # Get the vm views in one fell swoop
            for vm in host.vm:
                print('    VM: %s' % vm.name)
    
def main():
    vd = Discovery()
    vd.discovery()

if __name__ == '__main__':
    main()
