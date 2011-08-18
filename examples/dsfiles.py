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
import time

from psphere.scripting import BaseScript
from psphere.client import Client


class DatastoreFiles(BaseScript):
    def list_files(self):
        for dc in self.client.find_entity_views("Datacenter"):
            print("Datacenter: %s" % dc.name)
            for ds in dc.datastore:
                print("Datastore: %s" % ds.info.name)

            for ds in dc.datastore:
                print("Datastore: %s" % ds.info.name)
                root_folder = "[%s] /" % ds.info.name
                task = ds.browser.SearchDatastoreSubFolders_Task(datastorePath=root_folder)

                while task.info.state == "running":
                    time.sleep(3)
                    task.update()

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
    client = Client()
    dsf = DatastoreFiles(client)
    dsf.list_files()
    client.logout()


if __name__ == '__main__':
    main()
