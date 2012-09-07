from distutils.core import setup

setup(
    name = 'django-mailman',
    version = '0.0.1',
    packages = ['authproxy',],
    platforms = ['any'],
    license = 'MIT',
    author = 'Charlie DeTar',
    author_email = 'cfd@media.mit.edu',
    description = 'Authenticating port forwarder for Django based on gevent',
    long_description = open('README.rst').read(),
    url = 'http://github.com/yourcelf/django-authproxy',
)
