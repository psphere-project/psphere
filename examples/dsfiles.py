#!/usr/bin/env python

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


# Lists all files on all datastores attached to managed datacenters.
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
