django-authproxy
================

This is a simple authenticating proxy for Django.  It uses `gevent` to
efficiently forward ports for http connections of all types (including
websockets), but allowing you to authenticate the connection.

The use case I wrote it for: restricting access to a local etherpad server to
users who are logged into Django.

Installation
~~~~~~~~~~~~

Get it into your path.  This ought to work::

    pip install -e http://github.com/yourcelf/django-authproxy.git

You must also install the `gevent` dependency.

Usage
~~~~~

Add `authproxy` to your `INSTALLED_APPS`, and then add an AUTH_PROXIES setting, for example::

    AUTH_PROXIES = ({
        'listen': ':8088', # The port on which to listen
        'backend': ':9001', # The port for the backend
        'authorize': 'myapp.auth.proveit' # auth function
    }, ...)

The `authorize` function should take a single Django `HttpRequest` object as its argument, and return True / False for whether the connection is authorized.

Start the proxy server(s) with::

    python manage.py authproxyd

Status
~~~~~~

This is brand new, not battle or production tested, and probably buggy still.

License
~~~~~~~

MIT License.

Copyright (C) 2012 Charlie DeTar

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Authors
~~~~~~~

By Charlie DeTar.

Some parts are derivitive of `portforwarder.py` example from `gevent` by Denis Bilenko.
