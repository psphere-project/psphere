"""
A leaky wrapper for the underlying suds library.
"""

from suds import WebFault
from suds.client import Client, TransportError
from suds.sudsobject import Object, Property
from urllib2 import URLError

class VimSoap(object):
    def __init__(self, url):
        self.client = Client(url + '/vimService.wsdl')
        self.client.set_options(location=url)

    def invoke(self, method, **kwargs):
        """Invoke a method on the underlying soap service.

        >>> si_mo_ref = ManagedObjectReference('ServiceInstance',
                                               'ServiceInstance')
        >>> vs = VimSoap(url)
        >>> vs.invoke('RetrieveServiceContent', _this=si_mo_ref)

        """
        try:
            # Proxy the method to the suds service
            result = getattr(self.client.service, method)(**kwargs)
        except AttributeError:
            print('Unknown method: %s' % method)
            return None
        except (TransportError, URLError), e:
            print('Caught handled error %s' % e)
            return None
        except WebFault, e:
            print('Caught a WebFault')
            return None

        return result

    def create_object(self, type):
        return self.client.factory.create('ns0:%s' % type)

