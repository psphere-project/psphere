#!/usr/bin/python
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

from psphere.vim25 import Vim

def connect(url, username, password):
    """A simple connection test to login and print the server time.

    Arguments:
        url: The URL of the ESX or VIC server. e.g. (https://bennevis/sdk)
        username: The username to connect with.
        password: The password to connect with.
    """
    vim = Vim(url, username, password)
    print(vim.service_instance.current_time())

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('--url', dest='url',
                      help='the url of the vSphere server')
    parser.add_option('--username', dest='username',
                      help='the username to connnect with')
    parser.add_option('--password', dest='password',
                      help='the password to connect with')

    (option, args) = parser.parse_args()

    # Call the main method with the passed in arguments
    connect(option.url, option.username, option.password)

