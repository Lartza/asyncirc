#!/usr/bin/env python3
# coding=utf-8
# lagirc, simple Python irc library
# Copyright (C) 2015  Lari Tikkanen
#
# Released under the GPLv3
# See LICENSE for details.

import asyncio
from lagirc.rfc import rfc


class IRCClient(asyncio.Protocol):

    def __init__(self):
        self.buffer = ''
        self.nickname = 'lagirc'
        self.username = self.nickname
        self.realname = self.nickname
        self.transport = None
        self.channels = []

    def connection_made(self, transport):
        """Called when a connection to the server has been established. (Not the same as RPL_WELCOME received.)"""
        self.transport = transport
        self.nick(self.nickname)
        self.user(self.username, self.realname)

    def connection_lost(self, exc):
        """Called when connection to the server is lost."""
        pass
    
    def data_received(self, data):
        """Decodes received data and splits it to lines."""
        data = self.buffer + data.decode('utf-8').replace('\r', '')
        # Split data received from the IRC server to lines
        lines = data.split('\n')
        self.buffer = lines.pop()
        # Send each IRC message to be parsed
        for line in lines:
            asyncio.ensure_future(self.line_received(line))

    async def line_received(self, line):
        """Turns the line to an IRC message in usable format."""
        # Pass line for splitting. prefix, command, params
        result = await self.parse_line(line)
        # Convert IRC numerics to message names
        if result[1] in rfc.numerics:
            result[1] = rfc.numerics[result[1]]
        # Send the text format message to be handled
        asyncio.ensure_future(self.handle_command(result[0], result[1], result[2]))

    async def parse_line(self, line):
        """Returns a line split to it's components."""
        prefix = ''
        if line[0] == ':':
            prefix, line = line[1:].split(' ', 1)
        if ' :' in line:
            line, trailing = line.split(' :', 1)
            params = line.split()
            params.append(trailing)
        else:
            params = line.split()
        command = params.pop(0)
        return [prefix, command, params]

    async def handle_command(self, prefix, command, params):
        """Call methods that handle IRC messages."""
        # Convert the IRC message to a method, ex: irc_MESSAGE
        method = getattr(self, 'irc_{0}'.format(command), None)
        # Call the method if it exists
        if method:
            asyncio.ensure_future(method(prefix, params))

    def send_line(self, line):
        asyncio.ensure_future(self._send_line(line))

    async def _send_line(self, line):
        if not line.endswith('\r\n'):
            line += '\r\n'
        self.transport.write(line.encode('utf-8'))
        await asyncio.sleep(1)

    async def connected(self):
        """Called after RPL_WELCOME has been received from the server."""
        pass

    async def privmsg_received(self, user, channel, message):
        """Called for every PRIVMSG received from the server."""
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
        if not isinstance(channels, str):
            channels = ','.join(channels)
        if not isinstance(keys, str):
            keys = ','.join(keys)
        for chan in channels.split(','):
            if chan not in self.channels:
                self.channels.append(chan)
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
        if not isinstance(channels, str):
            channels = ','.join(channels)
        for chan in channels.split(','):
            if chan in self.channels:
                self.channels.remove(chan)
        self.send_line('PART {0} :{1}'.format(channels, message))

    def password(self, password):
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

    async def irc_PING(self, prefix, params):
        self.pong(params[-1])

    async def irc_PRIVMSG(self, prefix, params):
        asyncio.ensure_future(self.privmsg_received(prefix, params[0], params[-1]))

    async def irc_RPL_WELCOME(self, prefix, params):
        asyncio.ensure_future(self.connected())
