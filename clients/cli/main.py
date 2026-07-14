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
            elif command == "status":
            
                await websocket.send(
                    create_message(
                        MessageType.STATUS
                    )
                )

            else:

                message = parse(command)

                if message is None:

                    print("❌ Não entendi esse comando.")
                    continue

                await websocket.send(message)

            response = parse_message(
                await websocket.recv()
            )

            if response["type"] == "status_info":
            
                print()
                print("========================")
                print("🤖 Bingo Status")
                print("========================")
                print()
            
                print(f"Clients: {response['clients']}")
                print()
            
                print(f"Last command: {response['last_command']}")
                print()
            
                print("Programs:")
            
                for program in response["running_programs"]:
            
                    print(f" - {program}")
            
                print()
            else:
                print(response)
            
asyncio.run(main())
