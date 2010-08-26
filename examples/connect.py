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

from psphere.vim25 import Vim
from psphere.util import optionbuilder

def connect(url, username, password):
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
    >>> import connect
    >>> connect.connect('https://localhost/sdk', 'root', 'root')
    Successfully connected to https://bennevis/sdk
    Server time is 2010-08-26 23:53:38.003445

    """
    vim = Vim(url, username, password)
    curtime = vim.service_instance.current_time()
    print('Successfully connected to %s' % url)
    print('Server time is %s' % curtime)

def main(options):
    connect(options.url, options.username, options.password)

if __name__ == '__main__':
    ob = optionbuilder.OptionBuilder()
    options = ob.get_options()
    main(options)

