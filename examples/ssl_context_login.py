from __future__ import absolute_import, division, print_function

from ssl import CERT_NONE, PROTOCOL_SSLv23, SSLContext

from psphere.client import Client

context = SSLContext(PROTOCOL_SSLv23)
context.verify_mode = CERT_NONE
test_client = Client("192.168.0.14", "root", "password", sslcontext=context)
print(test_client.si.CurrentTime())
test_client.logout()
