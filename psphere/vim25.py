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

from psphere.ws import VimClient, TransportError, URLError
from psphere.util import morutil
from psphere.managed_objects import ManagedObjectReference

#import logging
#logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)
#logging.getLogger('suds.wsdl').setLevel(logging.DEBUG)

class VimService(object):
    def __init__(self, url):
        self.wsclient = VimClient(url)
        self.service = self.wsclient.service
        self.factory = self.wsclient.factory

    def invoke(self, method, **kwargs):
        """Invoke a method on the underlying soap service.

        >>> si_mo_ref = ManagedObjectReference('ServiceInstance',
                                               'ServiceInstance')
        >>> vs = VimService(url)
        >>> vs.invoke('RetrieveServiceContent', _this=si_mo_ref)

        """
        try:
            # Proxy the method to the web services method
            result = getattr(self.service, method)(**kwargs)
        except AttributeError:
            print('Unknown method: %s' % method)
            return None
        except (TransportError, URLError), e:
            print('Caught handled error %s' % e)
            return None

        return result

class Vim(object):
    def __init__(self, service_url):
        self.vs = VimService(service_url)
        self.si_mo_ref = ManagedObjectReference('ServiceInstance',
                                                'ServiceInstance')
        self.service_content = self.vs.invoke('RetrieveServiceContent',
                                              _this=self.si_mo_ref)

    def create_object(self, type):
        return self.vs.wsclient.factory.create('ns0:%s' % type)

    def login(self, username, password):
        sm = ManagedObjectReference(self.service_content.sessionManager.value,
                                    self.service_content.sessionManager._type)
        self.vs.invoke('Login', _this=sm, userName=username, password=password)

    def get_service_instance(self):
        return morutil.get_view(self, self.si_mo_ref)

