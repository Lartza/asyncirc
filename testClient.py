#!/usr/bin/env python3
#coding=utf-8
# lagirc, simple Python irc library
# Copyright (C) 2015  Lari Tikkanen
#
# Released under the GPLv3
# See LICENSE for details.

import asyncio
import lagirc

class testClient(lagirc.IRCClient):

    nickname = 'testClient'

    def connected(self):
        self.join('#test')

    def line_received(self, line):
        super().line_received(line)
        print(line)

    def privmsg_received(self, user, channel, message):
        if message == '!quit':
            self.quit()

loop = asyncio.get_event_loop()
coro = loop.create_connection(testClient, '127.0.0.1', 6667)
loop.run_until_complete(coro)
loop.run_forever()
loop.close()
