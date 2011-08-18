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

from psphere.client import Client
from psphere.scripting import BaseScript

class Connect(BaseScript):
    def connect(self):
        """A simple connection test to login and print the server time."""
        print(self.client.si.CurrentTime())

def main():
    client = Client()
    print('Successfully connected to %s' % client.server)
    c = Connect(client)
    c.connect()
    client.logout()

if __name__ == '__main__':
    main()
