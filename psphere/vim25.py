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

from suds.client import Client
from psphere.mor import ManagedObjectReference

import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').setLevel(logging.DEBUG)
#logging.getLogger('suds.wsdl').setLevel(logging.DEBUG)

class VimService(object):
    def __init__(self, url):
        self.vim_soap = Client('file:///home/jonathan/fooo/vimService.wsdl')
        self.vim_soap.set_options(location=url)

    def Login(self, _this, username, password):
        """
        si_moref: ManagedObjectReference to a ServiceInstance.
        username: The username to authenticate with.
        password: The password to authenticate with.
        """

        print("In VimService.Login()")
        result = self.vim_soap.service.Login(_this, username, password)
        return result

    def RetrieveServiceContent(self, service_instance):
        print("In VimService.RetrieveServiceContent()")
        return self.vim_soap.service.RetrieveServiceContent(service_instance)

    def CurrentTime(self, _this):
        print("In VimService.CurrentTime()")
        result = self.vim_soap.service.CurrentTime(_this)
        return result

    def RetrieveProperties(self, _this, specSet):
        print('In VimService.RetrieveProperties()')
        print(_this)
        print(specSet)
        result = self.vim_soap.service.RetrieveProperties(_this, specSet)
        return result

    def PowerOnMultiVM_Task(self, _this, vm):
        print('In VimService.PowerOnMultiVM_Task()')
        result = self.vim_soap.service.PowerOnMultiVM_Task(_this, vm)
        return result

    def CreateVM_Task(self, _this, config, pool, host=None):
        print('In VimService.CreateVM_Task()')
        result = self.vim_soap.service.CreateVM_Task(_this, vm)
        return result

    def CreateFolder(self, _this, name):
        print('In VimService.CreateFolder()')
        result = self.vim_soap.service.CreateFolder(_this, name)
        return result

class Vim(object):
    def __init__(self, service_url):
        self.vim_service = VimService(service_url)
        self.si_mo_ref = ManagedObjectReference('ServiceInstance',
                                                'ServiceInstance')
        self.service_content = (self.vim_service
                                .RetrieveServiceContent(self.si_mo_ref))

    def login(self, username, password):
        sm = ManagedObjectReference(self.service_content.sessionManager.value,
                                    self.service_content.sessionManager._type)
        self.vim_service.Login(_this=sm, username=username, password=password)

    def create_object(self, type):
        return self.vim_service.vim_soap.factory.create('ns0:%s' % type)

    def get_view(self, mo_ref, view_type=None, properties=None):
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
        view = eval(view_type)(mo_ref, self)
        view.update_view_data(properties)
        return view

    def get_views(self):
        pass

    def get_service_instance(self):
        return self.get_view(self.si_mo_ref)

    @classmethod
    def find_entity_view(self, view_type, begin_entity=None, filter=None):
        if not begin_entity:
            begin_entity = self.service_content.rootFolder

        ps = self.vim.create_object('PropertySpec')
        ps.all = False
        ps.pathSet = None
        ps.type = view_type
        pfs = ExtensibleManagedObject.get_search_filter_spec(begin_entity, ps)
        obj_contents = self.vim_service.RetrieveProperties(
            mo_ref=self.service_content.property_collector,
            spec_set=pfs)
        print(obj_contents)
