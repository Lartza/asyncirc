# coding=utf-8
import asyncio
import asyncirc

class testClient(asyncirc.IRCClient):

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