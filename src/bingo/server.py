import asyncio

import websockets

from bingo.dispatcher import Dispatcher
from bingo.protocol import parse_message
from bingo.config import HOST, PORT
from bingo.logger import info
from bingo.logger import success
from bingo.logger import debug
from bingo.state import state

dispatcher = Dispatcher()


async def handle_client(websocket):

    state.connected_clients += 1
    success(f"Client connected ({state.connected_clients} online)")

    try:
            async for raw_message in websocket:

                message = parse_message(raw_message)

                debug(f"Received: {message}")

                try:
                    response = dispatcher.dispatch(message)
                
                    if response is not None:
                        await websocket.send(response)
                
                except Exception as e:
                    from bingo.logger import error
                
                    error(f"Dispatcher failed: {e}")

    finally:
        state.connected_clients -= 1
        info(f"Client disconnected ({state.connected_clients} online)")


async def server():

    async with websockets.serve(
        handle_client,
        HOST,
        PORT
    ):

        info(f"Listening on ws://{HOST}:{PORT}")

        await asyncio.Future()


def start_server():

    asyncio.run(server())
