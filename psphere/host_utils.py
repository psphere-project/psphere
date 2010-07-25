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

def get_datastore(self, host_view, disksize, datastore=None):
    """
    host_view: HostSystem or like MOR
    disksize: Integer in KB
    datastore: String name of datastore, else default
    """

    # The array of datastores in the host or cluster
    ds_mor_array = host_view.datastore
    datastores = Vim.get_views(mo_ref_array=ds_mor_array)
    
    found_datastore = False
    if datastore:
        for ds in datastores:
            name = ds.summary.name
            if name == datastore and ds.summary.accessible:
                ds_disksize = ds.summary.freeSpace / 1024
                if ds_disksize < disksize:
                    return {'mor': None, 'name': 'disksize_error'}
                else:
                    found_datastore = True
                    mor = ds.mo_ref
                    break
    else:
        # TODO: Find first available datastore with free space
        pass

    if not found_datastore:
        return {'mor': None, 'name': 'datastore_error'}

    return {'mor': mor, 'name': ds_name}
