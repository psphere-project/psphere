from psphere.managed_objects import *

def get_search_filter_spec(vim, begin_entity, property_spec):
    """A PropertyFilterSpec for selecting any object under the begin_entity.
    
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
    selection_specs = []
    for ss_string in ss_strings:
        selection_spec = vim.create_object('SelectionSpec')
        selection_spec.name = ss_string
        selection_specs.append(selection_spec)

    # A traversal spec for deriving ResourcePool's from found VMs
    rpts = vim.create_object('TraversalSpec')
    rpts.name = 'resource_pool_traversal_spec'
    rpts.type = 'ResourcePool'
    rpts.path = 'resourcePool'
    rpts.select_set = [selection_specs[0], selection_specs[1]]

    # A traversal spec for deriving ResourcePool's from found VMs
    rpvts = vim.create_object('TraversalSpec')
    rpvts.name = 'resource_pool_vm_traversal_spec'
    rpvts.type = 'ResourcePool'
    rpvts.path = 'vm'

    crrts = vim.create_object('TraversalSpec')
    crrts.name = 'compute_resource_rp_traversal_spec'
    crrts.type = 'ComputeResource'
    crrts.path = 'resourcePool'
    crrts.select_set = [selection_specs[0], selection_specs[1]]

    crhts = vim.create_object('TraversalSpec')
    crhts.name = 'compute_resource_host_traversal_spec'
    crhts.type = 'ComputeResource'
    crhts.path = 'host'
     
    dhts = vim.create_object('TraversalSpec')
    dhts.name = 'datacenter_host_traversal_spec'
    dhts.type = 'Datacenter'
    dhts.path = 'hostFolder'
    dhts.select_set = [selection_specs[2]]

    dvts = vim.create_object('TraversalSpec')
    dvts.name = 'datacenter_vm_traversal_spec'
    dvts.type = 'Datacenter'
    dvts.path = 'vmFolder'
    dvts.select_set = [selection_specs[2]]

    hvts = vim.create_object('TraversalSpec')
    hvts.name = 'host_vm_traversal_spec'
    hvts.type = 'HostSystem'
    hvts.path = 'vm'
    hvts.select_set = [selection_specs[2]]
  
    fts = vim.create_object('TraversalSpec')
    fts.name = 'folder_traversal_spec'
    fts.type = 'Folder'
    fts.path = 'childEntity'
    fts.select_set = [selection_specs[2], selection_specs[3],
                      selection_specs[4], selection_specs[5],
                      selection_specs[6], selection_specs[7],
                      selection_specs[1]]

    obj_spec = vim.create_object('ObjectSpec')
    obj_spec.obj = begin_entity
    obj_spec.select_set = [fts, dvts, dhts, crhts, crrts,
                           rpts, hvts, rpvts]

    pfs = vim.create_object('PropertyFilterSpec')
    pfs.prop_set = property_spec
    pfs.object_set = [obj_spec]
    return pfs

def get_view(vim, mo_ref, view_type=None, properties=None):
    """Retrieve the properties of a single managed object.
    Arguments:
        mo_ref: ManagedObjectReference of the object to retrieve.
        view_type: The type of view to construct.
        properties: The properties to retrieve from the managed object.
    Returns:
        A view of the 
    """

    if not view_type:
        view_type = str(mo_ref._type)

    print('Type: ' + view_type)
    view = eval(view_type)(mo_ref, vim)
    view.update_view_data(properties)
    return view

def get_views(vim):
    """Retrieve the properties of many managed objects."""
    pass

def find_entity_view(vim, view_type, begin_entity=None, filter=None):
    view_types = ['ClusterComputeResource', 'ComputeResource', 'Datacenter',
                  'Folder', 'HostSystem', 'ResourcePool', 'VirtualMachine']

    if view_type not in view_types:
        print('Invalid view_type specified')
        return None

    if not begin_entity:
        begin_entity = vim.service_content.rootFolder

    ps = vim.create_object('PropertySpec')
    # TODO: Set all to False and set the pathSet parameter
    ps.all = True
    ps.type = view_type
    #ps.pathSet = filter
    pfs = morutil.get_search_filter_spec(vim, begin_entity, [ps])
    obj_contents = vim.vs.invoke(method='RetrieveProperties',
                                 _this=vim.service_content.propertyCollector,
                                 specSet=pfs)
    print(obj_contents)

