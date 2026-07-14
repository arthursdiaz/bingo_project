import asyncio
import base64

from bingo.client.websocket import BingoClient
from bingo.protocol import (
    create_dict,
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

    client = BingoClient()

    await client.connect()

    try:

        await client.send(
            create_dict(
                MessageType.AUDIO,
                filename="audio.wav",
                data=audio,
            )
        )

        print(
            await client.recv()
        )

    finally:

        await client.close()


asyncio.run(main())