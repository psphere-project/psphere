"""
A leaky wrapper for the underlying suds library.
"""

import sys
import urllib2
import suds

#import logging
#logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)
#logging.getLogger('suds.wsdl').setLevel(logging.DEBUG)

class VimSoap(object):
    def __init__(self, url):
        self.client = suds.client.Client(url + '/vimService.wsdl')
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
        except urllib2.URLError, e:
            print('A URL related error occurred while invoking the "%s" '
                  'method on the VIM server, this can be caused by '
                  'name resolution or connection problems.' % method)
            print('The underlying error is: %s' % e.reason[1])
            sys.exit()
        except suds.client.TransportError, e:
            print('TransportError: %s' % e)
        except suds.WebFault, e:
            print('Caught Webfault %s' % e)
            sys.exit()

        return result

    def create_object(self, type):
        """Create a suds object of the requested type."""
        return self.client.factory.create('ns0:%s' % type)

class ManagedObjectReference(suds.sudsobject.Property):
    """Custom class to replace the suds generated class, which lacks _type."""
    def __init__(self, mor=None, type=None, value=None):
        if mor:
            suds.sudsobject.Property.__init__(self, mor.value)
            self._type = str(mor._type)
        else:
            suds.sudsobject.Property.__init__(self, value)
            self._type = str(type)

