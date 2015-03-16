#!/usr/bin/env python3
#coding=utf-8
# lagirc, simple Python irc library
# Copyright (C) 2015  Lari Tikkanen
#
# Released under the GPLv3
# See LICENSE for details.

import asyncio
from lagirc.rfc import rfc

class IRCClient(asyncio.Protocol):

    nickname = 'lagirc'
    username = nickname
    realname = nickname
    
    buffer = ''
    queue = []

    def connection_made(self, transport):
        self.transport = transport
        self.nick(self.nickname)
        self.user(self.username, self.realname)

    def connection_lost(self, exc):
        pass
    
    def data_received(self, data):
        data = self.buffer + data.decode('utf-8').replace('\r', '')
        lines=data.split('\n')
        self.buffer=lines.pop()
        for line in lines:
            self.line_received(line)

    def line_received(self, line):
        prefix, command, params = self.parse_line(line)
        if command in rfc.numerics:
            command = rfc.numerics[command]
        self.handle_command(prefix, command, params)

    def parse_line(self, line):
        prefix = ''
        trailing = []
        if line[0] == ':':
            prefix, line = line[1:].split(' ', 1)
        if ' :' in line:
            line, trailing = line.split(' :', 1)
            params = line.split()
            params.append(trailing)
        else:
            params = line.split()
        command = params.pop(0)
        return prefix, command, params

    def handle_command(self, prefix, command, params):
        method = getattr(self, "irc_{0}".format(command), None)
        if method:
            method(prefix, params)

    def send_line(self, line):
        asyncio.async(self._send_line(line))

    @asyncio.coroutine
    def _send_line(self, line):
        if not line.endswith('\r\n'):
            line = line + '\r\n'
        self.transport.write(line.encode('utf-8'))
        yield from asyncio.sleep(1)

    def connected(self):
        pass

    def privmsg_received(self, user, channel, message):
        pass

    def raw(self, command):
        self.send_line('{0}'.format(command))

    def away(self, message=''):
        self.send_line('AWAY :{0}'.format(message))
    
    def back(self):
        self.away()

    def invite(self, nickname, channel):
        self.send_line('INVITE {0} {1}'.format(nickname, channel))

    def join(self, channels, keys=''):
        if type(channels) == list:
            channels = ','.join(channels)
        if type(keys) == list:
            keys = ','.join(keys)
        self.send_line('JOIN {0} {1}'.format(channels, keys))

    def kick(self, channel, client, message=''):
        self.send_line('KICK {0} {1} :{2}'.format(channel, client, message))

    def mode(self, target, flags, args=''):
        self.send_line('MODE {0} {1} {2}'.format(target, flags, args))

    def nick(self, nickname):
        self.nickname = nickname
        self.send_line('NICK {0}'.format(nickname))

    def notice(self, msgtarget, message):
        self.send_line('NOTICE {0} :{1}'.format(msgtarget, message))

    def part(self, channels, message=''):
        try:
            channels = ','.join(channels)
        except:
            pass
        self.send_line('JOIN {0} :{1}'.format(channels, message))

    def PASS(self, password):
        self.send_line('PASS {0}'.format(password))

    def pong(self, server1):
        self.send_line('PONG :{0}'.format(server1))

    def msg(self, msgtarget, message):
        self.send_line('PRIVMSG {0} :{1}'.format(msgtarget, message))

    def quit(self, message=''):
        self.send_line('QUIT :{0}'.format(message))

    def topic(self, channel, topic):
        self.send_line('TOPIC {0} :{1}'.format(channel, topic))

    def user(self, user, realname):
        self.send_line('USER {0} {1} {2} :{3}'.format(user, '0', '*', realname))

    def irc_PING(self, prefix, params):
        self.pong(params[-1])

    def irc_PRIVMSG(self, prefix, params):
        self.privmsg_received(prefix, params[0], params[-1])

    def irc_RPL_WELCOME(self, prefix, params):
        self.connected()
