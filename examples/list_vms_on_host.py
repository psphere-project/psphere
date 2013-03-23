#!/usr/bin/python
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
#
# A simple script to list the VMs on a host
#
# Example usage:
# python ./examples/list_vms_on_host.py --server <server> --username <user> --password <pass> --hostsystem <hostsystem>

import sys

from psphere.client import Client
from psphere.managedobjects import HostSystem

def main(options):
    client = Client(server=options.server, username=options.username,
                    password=options.password)

    print('Successfully connected to %s' % client.server)

    # Get a HostSystem object representing the host
    host = HostSystem.get(client, name=options.hostsystem)

    # Preload the name attribute of all items in the vm attribute. Read the
    # manual as this significantly speeds up queries for ManagedObject's
    host.preload("vm", properties=["name"])

    # Iterate over the items in host.vm and print their names
    for vm in sorted(host.vm):
        print(vm.name)

    # Close the connection
    client.logout()

if __name__ == "__main__":
    from optparse import OptionParser
    usage = "Usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("--server", dest="server",
                      help="The server to connect to")
    parser.add_option("--username", dest="username",
                      help="The username used to connect to the server")
    parser.add_option("--password", dest="password",
                      help="The password used to connect to the server")
    parser.add_option("--hostsystem", dest="hostsystem",
                      help="The host from which to list VMs")

    (options, args) = parser.parse_args()

    if options.server is None:
        print("You must specify a server")
        parser.print_help()
        sys.exit(1)

    if options.username is None:
        print("You must specify a username")
        parser.print_help()
        sys.exit(1)

    if options.password is None:
        print("You must specify a password")
        parser.print_help()
        sys.exit(1)

    if options.hostsystem is None:
        print("You must specify a host system")
        parser.print_help()
        sys.exit(1)

    main(options)
