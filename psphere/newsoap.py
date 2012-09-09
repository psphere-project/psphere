from lxml import etree as ET
import logging
import urllib2, cookielib

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

class SOAPClient(object):
    ns = {'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
          'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
          'xsd': 'http://www.w3.org/2001/XMLSchema'}
    def __init__(self, url, username=None, password=None):
        self.url = url
        self._logged_in = False
        if username is None:
            raise Exception("Username is required in SOAPClient()")
        if password is None:
            raise Exception("Password is required in SOAPClient()")
        self.username = username
        self.password = password
        self.cj = cookielib.LWPCookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        self.opener.addheaders = [
            ('User-Agent', 'VI Python'),
            ('SOAPAction', 'urn:vim25/5.0'),
            ('Content-Type', 'text/xml'),
        ]
        urllib2.install_opener(self.opener)

        if self._logged_in == False:
            self.login(self.username, self.password)

    def login(self, username, password):
        """
        Login to vCenter
        """
        creds = { 'userName': username, 'password': password }
        mo_ref = { '_type': 'SessionManager', 'value': 'SessionManager' }

        try:
            response = self.make_request('Login',
                            mo_ref=mo_ref, **creds)
            self._logged_in = True
        except:
            raise Exception("Unable to Login")

    def make_request(self, method, mo_ref, **kwargs):
        """Constructs and sends a SOAP request"""
        req = ET.Element('{%s}Envelope' % self.ns['soapenv'],
                nsmap=self.ns)
        body = ET.SubElement(req, ET.QName(self.ns['soapenv'], 'Body'))
        oper = ET.SubElement(body, method, nsmap={None: 'urn:vim25'})
        mor = ET.SubElement(oper, '_this', type=mo_ref['_type'])
        mor.text = mo_ref['value']

        if kwargs:
            for key in kwargs:
                val = ET.SubElement(oper, key)
                val.text = kwargs[key]

        logger.debug("SENDING SOAP REQUEST:")
        logger.debug(ET.tostring(req))
        logger.debug("--------------------")

        xml = ET.tostring(req, encoding='UTF-8', xml_declaration=True)
        # Create a request object
        request = urllib2.Request(self.url)

        # Put the XML into the request
        request.add_data(xml)

        # Send the request
        try:
            response = urllib2.urlopen(request)
        except urllib2.HTTPError:
            logger.debug("Caught an exception")
            raise

        if response.code in [200]:
            content = ET.fromstring(response.read())
        else:
            logger.error("Server responded with code %s" % response.code)
            raise ValueError

        # We should now have a valid response from the server
        # Convert the object to a psphere object
        # return the psphere object to the caller
        return content

    def deserialise(self, content):
        """Converts XML content to psphere objects"""
        # Dive inside the pickled WSDL
        # Identify if we're dealing with a MOR
        # Identify if we're dealing with an array
        # Identify if we're dealing with a complex type
        pass


if __name__ == '__main__':
    client = SOAPClient(url='https://wsapp4565.ae.sda.corp.telstra.com/sdk", username="------", password="------")
    respxml = client.make_request('RetrieveServiceContent',
            mo_ref={'_type': 'ServiceInstance', 'value': 'ServiceInstance'})
    print("Received: %s" % respxml)

#tree.find('soapenv:Body').find('{urn:vim25}RetrieveServiceContentResponse').find('{urn:vim25}returnval').find('{urn:vim25}rootFolder').attrib['type']
