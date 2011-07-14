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

"""Lists all files on all datastores attached to managed datacenters."""

import sys

from psphere.scripting import BaseScript
from psphere.soap import VimFault
from psphere.vim25 import ObjectNotFoundError


class DatastoreFiles(BaseScript):
    def list_files(self):
        for o in self.vim.find_entity_list('Datacenter', properties=['name', 'datastore']):
            print "Datacenter:", o.name
            ds = self.vim.get_views(o.datastore, properties=['name', 'browser'])
            for d in ds:
                print "Datastore:", d.name
                root_folder = "[%s] /" % d.name
                task = self.vim.invoke_task('SearchDatastoreSubFolders_Task',
                        _this=d.browser,
                        datastorePath=root_folder)

                for array_of_results in task.info.result:
                    # The first entry in this array is a type descriptor
                    # not a data object, so skip over it
                    for result in array_of_results[1:]:
                        for r in result:
                            for f in r.file:
                                print "%s%s" % (r.folderPath, f.path)


def main():
    dsf = DatastoreFiles()
    dsf.login()
    dsf.list_files()


if __name__ == '__main__':
    main()
