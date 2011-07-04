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
import time

from psphere.scripting import BaseScript
from psphere.managedobjects import Datacenter


class DatastoreFiles(BaseScript):
    def list_files(self):
        for dc in Datacenter.find(self.server):
            print("Datacenter: %s" % dc.name)
            print(dc.datastore)
            for ds in dc.datastore:
                print("Datastore: %s" % ds.info.name)

            for ds in dc.datastore:
                print("Datastore: %s" % ds.info.name)
                root_folder = "[%s] /" % ds.info.name
                task = ds.browser.SearchDatastoreSubFolders_Task(datastorePath=root_folder)

                task.update_view_data()
                while task.info.state == "running":
                    time.sleep(3)
                    task.update_view_data()

                for array_of_results in task.info.result:
                    # The first entry in this array is a type descriptor
                    # not a data object, so skip over it
                    for result in array_of_results[1:]:
                        for r in result:
                            try:
                                for f in r.file:
                                    print("%s%s" % (r.folderPath, f.path))
                            except AttributeError:
                                pass


def main():
    dsf = DatastoreFiles()
    dsf.login()
    dsf.list_files()


if __name__ == '__main__':
    main()
