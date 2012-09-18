import re
import sys
import signal
import logging
from cStringIO import StringIO
from BaseHTTPServer import BaseHTTPRequestHandler

from django.core.management import BaseCommand
from django.core.urlresolvers import resolve
from django.conf import settings
from django import http
from django.http import HttpRequest, Http404, parse_cookie
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware

import gevent
from gevent.server import StreamServer
from gevent.socket import create_connection, gethostbyname

logger = logging.getLogger(__name__)

class PythonHttpRequest(BaseHTTPRequestHandler):
    """ bare-bones parser of HTTP headers from a file handle. """
    def __init__(self, rfile):
        self.rfile = rfile
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message

class DjangoizedHttpRequest(HttpRequest):
    """
    Light alternative to WSGIRequest or ModPythonRequest that uses our raw
    python http request
    """
    def __init__(self, fh, *args, **kwargs):
        self.phr = PythonHttpRequest(fh)
        super(DjangoizedHttpRequest, self).__init__(*args, **kwargs)
        self.method = self.phr.command.upper()
        self.path = self.phr.path
        self.COOKIES = parse_cookie(self.phr.headers.get('Cookie', ''))

class PortForwarder(StreamServer):
    def __init__(self, listener_addr, backend_addr, auth_func, **kwargs):
        StreamServer.__init__(self, listener_addr, **kwargs)
        self.backend_addr = backend_addr
        self.auth_func = auth_func

    def handle(self, listener, address):
        # Find out which backend to use.
        logger.debug('%s:%s accepted', *address[:2])
        try:
            backend = create_connection(self.backend_addr)
        except IOError:
            logger.exception(self.backend_addr)
            gevent.spawn(server_error, listener)
            raise
        gevent.spawn(forward_request, listener, backend, self.auth_func)
        gevent.spawn(forward_response, backend, listener)

def server_error(client):
    body = u"500 Internal Server Error"
    response = u"\r\n".join((
        "HTTP/1.1 500 Internal Server Error",
        "Content-Type: text/plain; charset=utf-8",
        "Content-Length: %s" % len(body),
        "Connection: close",
        "\r\n",
        body
    ))
    client.sendall(response)
    # Close client connection.
    client.sendall("")


def forward_request(client, backend, auth_func):
    headers_complete = False
    body_part = None
    authenticated = False
    headers = StringIO()
    if not headers_complete:
        # Accumulate headers, then parse them.
        while True:
            data = client.recv(1024)
            logger.debug(data)
            if not data:
                break
            header_part, header_end, body_part = data.partition('\r\n\r\n')
            headers.write(header_part)
            if header_end:
                headers.write(header_end)
                # Build a Django flavor HttpRequest from the raw headers
                request = DjangoizedHttpRequest(StringIO(headers.getvalue()))
                # Run it through the middleware we need
                SessionMiddleware().process_request(request)
                AuthenticationMiddleware().process_request(request)
                authenticated = auth_func(request)
                break

    if authenticated:
        backend.sendall(headers.getvalue())
        if body_part:
            backend.sendall(body_part)
        while True:
            data = client.recv(1024)
            if not data:
                break
            backend.sendall(data)
    else:
        # Close backend connection.
        backend.sendall("")
        # Respond to client with forbidden
        body = u"403 Forbidden"
        response = u"\r\n".join((
            "HTTP/1.1 403 Forbidden",
            "Content-Type: text/plain; charset=utf-8",
            "Content-Length: %s" % len(body),
            "Connection: close",
            "\r\n",
            body
        ))
        client.sendall(response)
        # Close client connection.
        client.sendall("")

def forward_response(backend, client):
    try:
        while True:
            data = backend.recv(1024)
            if not data:
                break
            client.sendall(data)
    finally:
        backend.close()
        client.close()

def parse_address(address):
    try:
        hostname, port = address.rsplit(':', 1)
        port = int(port)
    except ValueError:
        sys.exit('Expected HOST:PORT: %r' % address)
    return gethostbyname(hostname), port

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        servers = []
        for auth_proxy in settings.AUTH_PROXIES: 
            listener_addr = parse_address(auth_proxy['listen'])
            backend_addr = parse_address(auth_proxy['backend'])
            module_name, func_name = auth_proxy['authorize'].rsplit(".", 1)
            mod = __import__(module_name)
            for submod in module_name.split('.')[1:]:
                mod = getattr(mod, submod)
            auth_func = getattr(mod, func_name)

            server = PortForwarder(listener_addr, backend_addr, auth_func)
            logger.info('Starting port forwarder for %s:%s => %s:%s' % (listener_addr + backend_addr))
            servers.append(server)
        gevent.joinall([
            gevent.spawn(server.serve_forever, server) for server in servers
        ])

