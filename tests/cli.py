import asyncio
import json
import sys
from pathlib import Path

import websockets

sys.path.append(str(Path(__file__).resolve().parent.parent / "core"))

from protocol import (
    MessageType,
    create_message,
    parse_message,
)


HELP = """
Comandos:

ping

open system_settings

exit
"""


async def main():

    print("======================")
    print("🤖 Bingo CLI")
    print("======================")

    print(HELP)

    async with websockets.connect("ws://localhost:8765") as websocket:

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

            elif command.startswith("open "):

                target = command.split(maxsplit=1)[1]

                await websocket.send(
                    create_message(
                        MessageType.COMMAND,
                        command="open_program",
                        target=target
                    )
                )

            else:

                print("❌ Comando desconhecido.")
                continue

            response = await websocket.recv()

            print(parse_message(response))


asyncio.run(main())