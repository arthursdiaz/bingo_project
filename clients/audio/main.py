import asyncio
import base64

import websockets

from bingo.config import WEBSOCKET_URL
from bingo.protocol import (
    create_message,
    MessageType,
)


async def main():

    with open(
        "audio.wav",
        "rb"
    ) as f:

        audio = base64.b64encode(
            f.read()
        ).decode()

    async with websockets.connect(
        WEBSOCKET_URL
    ) as ws:

        await ws.send(

            create_message(
                MessageType.AUDIO,
                filename="audio.wav",
                data=audio,
            )

        )

        print(
            await ws.recv()
        )

asyncio.run(main())