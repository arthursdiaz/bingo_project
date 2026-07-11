import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / "core"))

import asyncio
import websockets

from protocol import (
    MessageType,
    create_message,
    parse_message,
)


async def main():

    async with websockets.connect(
        "ws://localhost:8765"
    ) as websocket:

        print("Connected!")

        await websocket.send(
        
            create_message(
        
                MessageType.COMMAND,
        
                command="open_program",
        
                target="system_settings"
            )
        )

        response = await websocket.recv()

        print(parse_message(response))


asyncio.run(main())