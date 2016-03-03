#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import webbrowser
import tornado
import tornado.ioloop
import tornado.web
import tornado.httpserver
import handlers
from sockjs.tornado import SockJSRouter
import os
import subprocess
import base64

DEFAULT_SSL_DIRECTORY = "../../ssl_cert"
CERT_FILE_SSL = os.path.join(DEFAULT_SSL_DIRECTORY, "ca.csr")
KEY_FILE_SSL = os.path.join(DEFAULT_SSL_DIRECTORY, "ca.key")


def main(debug, static_dir, template_dir, listen):
    socket_connection = SockJSRouter(handlers.TestStatusConnection, '/update_user', user_settings=None)

    # TODO store cookie_secret if want to reuse it if restart server
    settings = {"static_path": static_dir,
                "template_path": template_dir,
                "debug": debug,
                "cookie_secret": base64.b64encode(os.urandom(50)).decode('ascii'),
                "login_url": "/login"
                }
    routes = [
        # pages
        tornado.web.url(r"/", handlers.IndexHandler, name='index'),
        tornado.web.url(r"/login", handlers.LoginHandler, name='login'),
        tornado.web.url(r"/logout", handlers.LogoutHandler, name='logout'),
        tornado.web.url(r"/admin", handlers.AdminHandler, name='admin'),
        tornado.web.url(r"/character", handlers.CharacterHandler, name='character'),
        tornado.web.url(r'/static/(favicon.ico)', tornado.web.StaticFileHandler, {"path": "src/web/"}),

        # command
        tornado.web.url(r"/cmd/character_view", handlers.CharacterViewHandler, name='character_view'),
    ]
    application = tornado.web.Application(routes + socket_connection.urls, **settings)

    # Generate a self-signed certificate and key if we don't already have one.
    if not os.path.isfile(CERT_FILE_SSL) or not os.path.isfile(KEY_FILE_SSL):
        cmd = 'openssl req -x509 -sha256 -newkey rsa:2048 -keyout %s -out %s -days 36500 -nodes -subj' % (
            KEY_FILE_SSL, CERT_FILE_SSL)
        cmd_in = cmd.split() + ["/C=CA/ST=QC/L=Montreal/O=Traitre-lame/OU=gn.qc.ca"]

        subprocess.call(cmd_in)

    # ssl_options = {"certfile": CERT_FILE_SSL, "keyfile": KEY_FILE_SSL}
    ssl_options = None

    io_loop = tornado.ioloop.IOLoop.instance()

    http_server = tornado.httpserver.HTTPServer(application, ssl_options=ssl_options, io_loop=io_loop)
    http_server.listen(port=listen.port, address=listen.address)

    url = "http{2}://{0}:{1}".format(listen.address, listen.port, "s" if ssl_options else "")
    print('Starting server at {0}'.format(url))

    # open a URL, if possible on new tab
    webbrowser.open(url, new=2)

    try:
        io_loop.start()
    except KeyboardInterrupt:
        io_loop.stop()
        io_loop.close()