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

import time

from psphere import soap
from psphere.errors import TaskFailedError
from psphere.managedobjects import *

class Vim(object):
    def __init__(self, url, auto_populate=True, debug=False):
        self.debug = debug
        if self.debug:
            import logging
            logging.basicConfig(level=logging.INFO)
            logging.getLogger('suds.client').setLevel(logging.DEBUG)
        self.auto_populate = auto_populate
        self.client = soap.get_client(url)
        si_mo_ref = soap.ManagedObjectReference(_type='ServiceInstance',
                                                value='ServiceInstance')
        self.si = ServiceInstance(si_mo_ref, self) 
        self.sc = self.si.RetrieveServiceContent()

    def login(self, username, password):
        """Login to a vSphere server."""
        self.sc.sessionManager.Login(userName=username, password=password)

    def logout(self):
        """Logout of a vSphere server."""
        self.sc.sessionManager.Logout()

    def find_and_destroy(self, property):
        if not hasattr(property, '__iter__'):
            return property

        for subprop in property:
            print('@@@@@@@@@@@@@@@')
            print(property)
            print('@@@@@@@@@@@@@@@')
            if hasattr(property[1], '_type'):
                print("It has _type attribute")
                # If it is, then instantiate and populate a class of that type
                kls = classmapper(property[1]._type)
                replacement = kls(property[1], self)
                # ...and replace the property in the result
                result[property[0]] = replacement

    def invoke(self, method, _this, **kwargs):
        result = soap.invoke(self.client, method, _this=_this, **kwargs)
        print(result.__class__)
        if not hasattr(result, '__iter__'):
            print("Result is not iterable")
            return result

        # For each property
        property = self.find_and_destroy(property)
        print result
        # Return the modified result to the caller
        return result

    def create_object(self, type_, **kwargs):
        """Create a SOAP object of the requested type."""
        obj = soap.create(self.client, type_)
        for key, value in kwargs.items():
            setattr(obj, key, value)
        return obj

#        Notes
#        -----
#        A view is a local, static representation of a managed object in
#        the inventory. The view is not automatically synchronised with 
#        the server-side object and can therefore be out of date a moment
#        after it is retrieved.
#        
#        Retrieval of only the properties you intend to use -- through
#        the use of the properties parameter -- is considered best
#        practise as the properties of some managed objects can be
#        costly to retrieve.

    def get_view(self, mo_ref, properties=None):
        """Get a view of a vSphere managed object."""
        # This maps the mo_ref into a psphere class and then instantiates it
        kls = classmapper(mo_ref._type)
        view = kls(mo_ref, self)
        # Update the requested properties of the instance
        view.update_view_data(properties=properties)

        return view

    def get_views(self, mo_refs, properties=None):
        """Get a list of local view's for multiple managed objects.

        Parameters
        ----------
        mo_refs : ManagedObjectReference
            The list of ManagedObjectReference's that views are to
            be created for.
        properties : list
            The properties to retrieve in the views.

        Returns
        -------
        entities : list of instances (ManagedObject subclasses)
            A list of local instances representing the server-side
            managed objects.

        See also
        --------
        get_view : Get the view for a single managed object.

        """
        property_spec = soap.create(self.client, 'PropertySpec')
        # FIXME: Makes assumption about mo_refs being a list
        property_spec.type = str(mo_refs[0]._type)
        if not properties and self.auto_populate:
            property_spec.all = True
        else:
            # Only retrieve the requested properties
            property_spec.all = False
            property_spec.pathSet = properties

        object_specs = []
        for mo_ref in mo_refs:
            object_spec = soap.create(self.client, 'ObjectSpec')
            object_spec.obj = mo_ref
            object_specs.append(object_spec)

        pfs = soap.create(self.client, 'PropertyFilterSpec')
        pfs.propSet = [property_spec]
        pfs.objectSet = object_specs

        object_contents = self.sc.propertyCollector.RetrieveProperties(
            specSet=pfs)
        print('@@@@@@@@@@@@@')
        print(object_contents)
        print('@@@@@@@@@@@@@')
        views = []
        for object_content in object_contents:
            # This maps the type of managed object in object_content into
            # a psphere class and then instantiates it with the mo_ref
            # inside the object_content
            kls = classmapper(object_content.obj._type)
            view = kls(mo_ref, self)
            # Update the instance with the data in object_content
            view.set_view_data(object_content=object_content)
            views.append(view)

        return views
        
    def get_search_filter_spec(self, begin_entity, property_spec):
        """Build a PropertyFilterSpec capable of full inventory traversal.
        
        By specifying all valid traversal specs we are creating a PFS that
        can recursively select any object under the given enitity.

        """
        # The selection spec for additional objects we want to filter
        ss_strings = ['resource_pool_traversal_spec',
                      'resource_pool_vm_traversal_spec',
                      'folder_traversal_spec',
                      'datacenter_host_traversal_spec',
                      'datacenter_vm_traversal_spec',
                      'compute_resource_rp_traversal_spec',
                      'compute_resource_host_traversal_spec',
                      'host_vm_traversal_spec']

        # Create a selection spec for each of the strings specified above
        selection_specs = [
            soap.create(self.client, 'SelectionSpec', name=ss_string)
            for ss_string in ss_strings
        ]

        # A traversal spec for deriving ResourcePool's from found VMs
        rpts = soap.create(self.client, 'TraversalSpec')
        rpts.name = 'resource_pool_traversal_spec'
        rpts.type = 'ResourcePool'
        rpts.path = 'resourcePool'
        rpts.selectSet = [selection_specs[0], selection_specs[1]]

        # A traversal spec for deriving ResourcePool's from found VMs
        rpvts = soap.create(self.client, 'TraversalSpec')
        rpvts.name = 'resource_pool_vm_traversal_spec'
        rpvts.type = 'ResourcePool'
        rpvts.path = 'vm'

        crrts = soap.create(self.client ,'TraversalSpec')
        crrts.name = 'compute_resource_rp_traversal_spec'
        crrts.type = 'ComputeResource'
        crrts.path = 'resourcePool'
        crrts.selectSet = [selection_specs[0], selection_specs[1]]

        crhts = soap.create(self.client, 'TraversalSpec')
        crhts.name = 'compute_resource_host_traversal_spec'
        crhts.type = 'ComputeResource'
        crhts.path = 'host'
         
        dhts = soap.create(self.client, 'TraversalSpec')
        dhts.name = 'datacenter_host_traversal_spec'
        dhts.type = 'Datacenter'
        dhts.path = 'hostFolder'
        dhts.selectSet = [selection_specs[2]]

        dvts = soap.create(self.client, 'TraversalSpec')
        dvts.name = 'datacenter_vm_traversal_spec'
        dvts.type = 'Datacenter'
        dvts.path = 'vmFolder'
        dvts.selectSet = [selection_specs[2]]

        hvts = soap.create(self.client, 'TraversalSpec')
        hvts.name = 'host_vm_traversal_spec'
        hvts.type = 'HostSystem'
        hvts.path = 'vm'
        hvts.selectSet = [selection_specs[2]]
      
        fts = soap.create(self.client, 'TraversalSpec')
        fts.name = 'folder_traversal_spec'
        fts.type = 'Folder'
        fts.path = 'childEntity'
        fts.selectSet = [selection_specs[2], selection_specs[3],
                          selection_specs[4], selection_specs[5],
                          selection_specs[6], selection_specs[7],
                          selection_specs[1]]

        obj_spec = soap.create(self.client, 'ObjectSpec')
        obj_spec.obj = begin_entity
        obj_spec.selectSet = [fts, dvts, dhts, crhts, crrts,
                               rpts, hvts, rpvts]

        pfs = soap.create(self.client, 'PropertyFilterSpec')
        pfs.propSet = [property_spec]
        pfs.objectSet = [obj_spec]
        return pfs

    def invoke_task(self, method, **kwargs):
        """Execute a task and wait for it to complete."""
        # Don't execute methods which don't return a Task object
        if not method.endswith('_Task'):
            print('ERROR: invoke_task can only be used for methods which '
                  'return a ManagedObjectReference to a Task.')
            return None

        task_mo_ref = self.invoke(method=method, **kwargs)
        task = Task(task_mo_ref, self)
        task.update_view_data(properties=['info'])
        # TODO: This returns true when there is an error
        while True:
            if task.info.state == 'success':
                return task
            elif task.info.state == 'error':
                # TODO: Handle error checking properly
                raise TaskFailedError(task.info.error.localizedMessage)

            # TODO: Implement progresscallbackfunc
            # Sleep two seconds and then refresh the data from the server
            time.sleep(2)
            task.update_view_data(properties=['info'])

    def find_entity_list(self, view_type, begin_entity=None, properties=[]):
        """
        Return a list of entities of the given type.

        Parameters
        ----------
        view_type : str
            The object for which we are retrieving the view.
        begin_entity : ManagedObjectReference
            If specified, the traversal is started at this MOR. If not
            specified the search is started at the root folder.
        """
        kls = classmapper(view_type)
        # Start the search at the root folder if no begin_entity was given
        if not begin_entity:
            begin_entity = self.sc.rootFolder.mo_ref

        property_spec = soap.create(self.client, 'PropertySpec')
        property_spec.type = view_type
        property_spec.all = False
        property_spec.pathSet = properties

        pfs = self.get_search_filter_spec(begin_entity, property_spec)

        # Retrieve properties from server and update entity
        obj_contents = self.sc.propertyCollector.RetrieveProperties(specSet=pfs)

        views = []
        for obj_content in obj_contents:
            view = kls(obj_content.obj, self)
            view.update_view_data(properties=properties)
            views.append(view)

        return views

    def find_entity_view(self, view_type, begin_entity=None, filter={},
                         properties=[]):
        """Return a new instance based on the search filter.

        Traverses the MOB looking for an entity matching the filter.

        Parameters
        ----------
        view_type : str
            The object for which we are retrieving the view.
        begin_entity : ManagedObjectReference
            If specified, the traversal is started at this MOR. If not
            specified the search is started at the root folder.
        filter : dict
            Key/value pairs to filter the results. The key is a valid
            parameter of the object type. The value is what that
            parameter should match.

        Returns
        -------
        object : object
            A new instance of the requested object.

        """
        kls = classmapper(view_type)
        # Start the search at the root folder if no begin_entity was given
        if not begin_entity:
            begin_entity = self.sc.rootFolder.mo_ref

        property_spec = soap.create(self.client, 'PropertySpec')
        property_spec.type = view_type
        property_spec.all = False
        property_spec.pathSet = filter.keys()

        pfs = self.get_search_filter_spec(begin_entity, property_spec)

        # Retrieve properties from server and update entity
        #obj_contents = self.propertyCollector.RetrieveProperties(specSet=pfs)
        obj_contents = self.sc.propertyCollector.RetrieveProperties(specSet=pfs)

        # TODO: Implement filtering
        if not filter:
            print('WARNING: No filter specified, returning first match.')
            # If no filter is specified we just return the first item
            # in the list of returned objects
            view = kls(obj_contents[0].obj, self)
            view.update_view_data(properties)
            return view

        matched = False
        # Iterate through obj_contents retrieved
        for obj_content in obj_contents:
            # If there are is no propSet, skip this one
            if not obj_content.propSet:
                continue

            # Iterate through each property in the set
            for prop in obj_content.propSet:
                # If the property name is in the defined filter
                if prop.name in filter:
                    # ...and it matches the value specified
                    # TODO: Regex this?
                    if prop.val == filter[prop.name]:
                        # We've found a match
                        filtered_obj_content = obj_content
                        matched = True
                        break

            # If we've matched something at this point, finish the loop
            if matched:
                break

        if not matched:
            # There were no matches
            raise ObjectNotFoundError("No matching objects for filter")

        view = kls(filtered_obj_content.obj, self)
        view.update_view_data(properties=properties)
        return view
