import asyncio
import websockets

from protocol import (
    MessageType,
    create_message,
    parse_message
)

HOST = "0.0.0.0"
PORT = 8765


async def handle_client(websocket):
    print("📱 Client connected")

    async for raw_message in websocket:

        message = parse_message(raw_message)

        print(message)

        match message["type"]:

            case MessageType.PING.value:

                await websocket.send(
                    create_message(MessageType.PONG)
                )

            case _:

                print("Unknown message")


async def server():

    async with websockets.serve(
        handle_client,
        HOST,
        PORT
    ):

        print(f"🌐 Listening on ws://{HOST}:{PORT}")

        await asyncio.Future()


def start_server():
    asyncio.run(server())