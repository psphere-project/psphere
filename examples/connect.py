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

from psphere import config
from psphere.client import Client

def main(options):
    """A simple connection test to login and print the server time."""
    server = config._config_value("general", "server", options.server)
    if server is None:
        raise ValueError("server must be supplied on command line"
                         " or in configuration file.")
    username = config._config_value("general", "username", options.username)
    if username is None:
        raise ValueError("username must be supplied on command line"
                         " or in configuration file.")
    password = config._config_value("general", "password", options.password)
    if password is None:
        raise ValueError("password must be supplied on command line"
                         " or in configuration file.")

    client = Client(server=server, username=username, password=password)
    print('Successfully connected to %s' % client.server)
    print(client.si.CurrentTime())
    client.logout()

if __name__ == "__main__":
    from optparse import OptionParser
    usage = "Usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("--server", dest="server",
                      help="The server to connect to for provisioning")
    parser.add_option("--username", dest="username",
                      help="The username used to connect to the server")
    parser.add_option("--password", dest="password",
                      help="The password used to connect to the server")

    (options, args) = parser.parse_args()
    main(options)
