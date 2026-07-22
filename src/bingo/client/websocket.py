import asyncio
import websockets

from bingo.config import WEBSOCKET_URL
from bingo.protocol import (
    encode_message,
    parse_message,
)


class BingoClient:

    def __init__(self):
        self.websocket = None
        self._reader_task = None
        self._queue = None

    async def connect(self):
        self.websocket = await websockets.connect(
            WEBSOCKET_URL
        )
        self._queue = asyncio.Queue()
        self._reader_task = asyncio.create_task(self._reader())

    async def _reader(self):
        try:
            async for response in self.websocket:
                message = parse_message(response)
                if message.get("type") == "ping":
                    await self.send({"type": "pong"})
                else:
                    await self._queue.put(message)
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    async def send(self, message):
        await self.websocket.send(
            encode_message(message)
        )

    async def recv(self):
        return await self._queue.get()

    async def close(self):
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
        if self.websocket:
            await self.websocket.close()