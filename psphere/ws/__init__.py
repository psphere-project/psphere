"""
A leaky wrapper for the underlying suds library.
"""

from suds.client import Client, TransportError
from suds.sudsobject import Object, Property
from urllib2 import URLError

class VimClient(Client):
    def __init__(self, url, **kwargs):
        """Append the WSDL filename and init the suds Client class."""
        Client.__init__(self, url + '/vimService.wsdl', **kwargs)
        self.set_options(location=url)
