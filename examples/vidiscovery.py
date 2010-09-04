#!/usr/bin/env python
#
# Copyright 2010 Jonathan Kinred <jonathan.kinred@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# he Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from psphere.scripting import BaseScript

class VimDiscovery(BaseScript):
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
        ccs = self.vim.find_entity_view(view_type='ClusterComputeResource',
                                filter={'name': 'Application Engineering'},
                                        properties=['name', 'host'])
        print('Cluster: %s (%s hosts)' % (ccs.name, len(ccs.host)))

        # Get the host views in one fell swoop
        hosts = self.vim.get_views(mo_refs=ccs.host,
                                   properties=['name', 'vm'])
        for host in hosts:
            print('  Host: %s (%s VMs)' % (host.name, len(host.vm)))
            # Get the vm views in one fell swoop
            vms = self.vim.get_views(mo_refs=host.vm, properties=['name'])
            for vm in vms:
                print('    VM: %s' % vm.name)
    
def main():
    vd = VimDiscovery()
    vd.discovery()

if __name__ == '__main__':
    main()
