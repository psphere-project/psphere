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
        servertime = self.vim.invoke('CurrentTime',
                                     _this=self.vim.service_instance)
        print('Server time is %s' % servertime)
        self.vim.logout()

def main():
    c = Connect()
    c.connect()

if __name__ == '__main__':
    main()

