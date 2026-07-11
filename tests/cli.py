import sys
from pathlib import Path

import asyncio
import websockets

from bingo.config import WEBSOCKET_URL
from bingo.parser import parse
from bingo.protocol import (
    MessageType,
    create_message,
    parse_message,
)

HELP = """
Comandos:

ping

exit
"""


async def main():

    print("======================")
    print("🤖 Bingo CLI")
    print("======================")

    print(HELP)

    async with websockets.connect(WEBSOCKET_URL) as websocket:

        while True:

            command = input("\n> ").strip()

            if command == "exit":
                break

            if command == "ping":

                await websocket.send(
                    create_message(
                        MessageType.PING
                    )
                )

            else:

                message = parse(command)

                if message is None:

                    print("❌ Não entendi esse comando.")
                    continue

                await websocket.send(message)

            response = await websocket.recv()

            print(parse_message(response))


asyncio.run(main())
