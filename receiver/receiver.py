#!/usr/bin/env python3 -u


import asyncio
import datetime
import aiohttp
import async_timeout

class EchoServerClientProtocol(asyncio.Protocol):

    def connection_made(self, transport):
        self.peername = transport.get_extra_info('peername')
        self.now = datetime.datetime.now()
        self.transport = transport

    def data_received(self, data):
        self.transport.close()
        message = {}

        for _ in data.decode().split('\n'):
            k,v = _.split('=')
            message[k] = v

        print('{} {}'.format(self.now.isoformat(), message), flush=True)

loop = asyncio.get_event_loop()

# Each client connection will create a new protocol instance
coro = loop.create_server(EchoServerClientProtocol, '0.0.0.0', 7654)

server = loop.run_until_complete(coro)

# Serve requests until Ctrl+C is pressed
print('Serving on {}'.format(server.sockets[0].getsockname()))

# async def fetch(session, url):
#     with async_timeout.timeout(10):
#         async with session.get(url) as response:
#             return await response.text()
#
# async def main(loop):
#     async with aiohttp.ClientSession(loop=loop) as session:
#         html = await fetch(session, 'http://python.org')
#         print(html)
#
# loop = asyncio.get_event_loop()
# loop.run_until_complete(main(loop))







try:
    loop.run_forever()
except KeyboardInterrupt:
    pass

# Close the server
server.close()
loop.run_until_complete(server.wait_closed())
loop.close()
