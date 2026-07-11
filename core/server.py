import asyncio

import websockets

from dispatcher import Dispatcher

from protocol import parse_message

HOST = "0.0.0.0"
PORT = 8765

dispatcher = Dispatcher()


async def handle_client(websocket):

    print("📱 Client connected")

    async for raw_message in websocket:

        message = parse_message(raw_message)

        print(message)

        response = dispatcher.dispatch(message)

        if response is not None:

            await websocket.send(response)


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