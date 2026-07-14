import websockets

from bingo.config import WEBSOCKET_URL
from bingo.protocol import (
    encode_message,
    parse_message,
)


class BingoClient:

    def __init__(self):

        self.websocket = None

    async def connect(self):

        self.websocket = await websockets.connect(
            WEBSOCKET_URL
        )

    async def send(self, message):

        await self.websocket.send(
            encode_message(message)
        )

    async def recv(self):

        response = await self.websocket.recv()

        return parse_message(response)

    async def close(self):

        await self.websocket.close()