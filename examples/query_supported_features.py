#!/usr/bin/python
# Copyright 2013 Jonathan Kinred
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

from psphere.client import Client


def main(options):
    """Obtains supported features from the license manager"""
    client = Client(server=options.server, username=options.username,
                    password=options.password)
    print('Successfully connected to %s' % client.server)
    lm_info = client.sc.licenseManager.QuerySupportedFeatures()
    for feature in lm_info:
        print('%s: %s' % (feature.featureName, feature.state))

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
