# -*- coding: utf-8 -*-
# Copyright (c) 2011, Wojciech Bederski (wuub.net)
# All rights reserved.
# See LICENSE.txt for details.

import socket
import repl
import bencode

class NreplRepl(repl.Repl):
    TYPE = "nrepl"

    def __init__(self, encoding, external_id=None, host="localhost", port=23, cmd_postfix="\n", suppress_echo=False):
        super(NreplRepl, self).__init__(encoding, external_id, cmd_postfix, suppress_echo)
        self._socket = socket.socket()
        self._address = (host, port)
        self._socket.connect(self._address)
        self._alive = True
        self._killed = False
        self._messages = messages(self._socket)
        self._session = self._clone_session()


    def name(self):
        return "%s:%s" % (self._address[0], self._address[1])

    def is_alive(self):
        return self._alive

    def read_bytes(self):
        for message in self._messages:
            reply = self._format_message(message)
            if reply:
                return reply

    def write_bytes(self, bytes):
        self._socket.sendall(bencode.bencode({ "session": self._session, "op": "eval", "code": bytes }))

    def kill(self):
        print "killing socket"
        self._killed = True
        self._socket.close()
        self._alive = False

    def _clone_session(self):
        self._socket.sendall(bencode.bencode({ "op": "clone" }))
        data = self._messages.next()
        return data['new-session']

    def _format_message(self, message):
        if 'out' in message:
            return message['out']

        if 'value' in message:
            return message['value'] + "\n"

        if 'err' in message:
            return message['err']

def messages(socket):
    buffer = ""
    while True:
        (message, length) = bdecode_one(buffer)

        if message:
            buffer = buffer[length:]
            yield message
        else:
            chunk = socket.recv(4096)

            if not chunk:
                # socket closed
                break

            buffer += chunk

def bdecode_one(buffer):
    try:
        return bencode.decode_func[buffer[0]](buffer, 0)
    except (IndexError, KeyError, ValueError):
        # the buffer has only a partial message
        return (None, 0)
