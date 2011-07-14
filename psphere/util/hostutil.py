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
