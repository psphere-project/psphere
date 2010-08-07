"""
A leaky wrapper for the underlying suds library.
"""

import sys
from urllib2 import URLError
from suds import WebFault
from suds.client import Client, TransportError
from suds.sudsobject import Property

class VimSoap(object):
    def __init__(self, url):
        self.client = Client(url + '/vimService.wsdl')
        #self.client = Client('file:///home/jonathan/projects/Personal/psphere/resources/vimService.wsdl')
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
        except AttributeError, e:
            print(type(e))
            print('Unknown method: %s' % method)
            sys.exit()
        except URLError, e:
            print('A URL related error occurred while invoking the "%s" '
                  'method on the VIM server, this can be caused by '
                  'name resolution or connection problems.' % method)
            print('The underlying error is: %s' % e.reason[1])
            sys.exit()
        except TransportError, e:
            print('TransportError: %s' % e)
        except WebFault, e:
            print('Caught Webfault %s' % e)
            sys.exit()

        return result

    def create_object(self, type):
        """Create a suds object of the requested type."""
        return self.client.factory.create('ns0:%s' % type)

