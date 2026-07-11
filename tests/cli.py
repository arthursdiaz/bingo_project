import sys
from pathlib import Path

CORE_PATH = Path(__file__).resolve().parent.parent / "core"
sys.path.append(str(CORE_PATH))

import asyncio
import websockets

from config import WEBSOCKET_URL
from parser import parse
from protocol import (
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
