from __future__ import absolute_import, division, print_function

from ssl import CERT_NONE, PROTOCOL_SSLv23, SSLContext

from psphere.client import Client

if __name__ == '__main__':
    context = SSLContext(PROTOCOL_SSLv23)
    context.verify_mode = CERT_NONE
    test_client = Client('localhost:8989', 'user', 'pass', sslcontext=context)
    print(test_client.si.CurrentTime())
    test_client.logout()
