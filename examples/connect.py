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

class Connect(BaseScript):
    def connect(self):
        """A simple connection test to login and print the server time.

        Parameters
        ----------
        url : str
            The URL of the ESX or VIC server. e.g. (https://bennevis/sdk)
        username : str
            The username to connect with.
        password : str
            The password to connect with.

        Examples
        --------
        >>> from psphere.scripts import Connect
        >>> c = Connect()
        >>> c.connect()
        Successfully connected to https://bennevis/sdk
        Server time is 2010-08-26 23:53:38.003445

        """
        self.login()
        print('Successfully connected to %s' % self.options.url)
        print(self.client.si.CurrentTime())
        self.client.logout()

def main():
    c = Connect()
    c.connect()

if __name__ == '__main__':
    main()
