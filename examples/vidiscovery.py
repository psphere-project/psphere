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

import optparse
from psphere.vim25 import Vim

def discovery(url, username, password):
    """An example that discovers all hosts and VMs in the specified cluster.

    Parameters
    ----------
    url : str
        The URL of the ESX or VIC server. e.g. (https://bennevis/sdk)
    username : str
        The username to connect with.
    password : str
        The password to connect with.

    """
    vim = Vim(url)
    vim.login(username, password)

    # Find the first ClusterComputeResource
    ccs = vim.find_entity_view(view_type='ClusterComputeResource',
                               filter={'name': 'Dalley St'})
    ccs.update_view_data(properties=['name', 'host'])
    print('Cluster: %s (%s hosts)' % (ccs.name, len(ccs.host)))

    # Get the host views in one fell swoop
    # It's important to be selective about the properties that
    # are retrieved from the server. Getting all the properties
    # of some managed entities (HostSystem is one) can be very
    # costly in terms of server resources and response time.
    hosts = vim.get_views(mo_refs=ccs.host, properties=['name', 'vm'])
    for host in hosts:
        print('  Host: %s (%s VMs)' % (host.name, len(host.vm)))
        # Get the vm views in one fell swoop
        vms = vim.get_views(mo_refs=host.vm, properties=['name'])
        for vm in vms:
            print('    VM: %s' % vm.name)
    
def main(options):
    discovery(options.url, options.username, options.password)

if __name__ == '__main__':
    usage = ('usage: %prog --url https://<host>/sdk --username <username> '
             '--password <password>')
    parser = optparse.OptionParser(usage)
    parser.add_option('--url', dest='url',
                      help='the url of the vSphere server')
    parser.add_option('--username', dest='username',
                      help='the username to connnect with')
    parser.add_option('--password', dest='password',
                      help='the password to connect with')

    (options, args) = parser.parse_args()

    if not options.url:
        parser.error('--url option is required')
    if not options.username:
        parser.error('--username option is required')
    if not options.password:
        parser.error('--password option is required')

    # Call the main method with the passed in arguments
    main(options)

