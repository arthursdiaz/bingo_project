import datetime
import asyncio

import websockets

from bingo.dispatcher import Dispatcher
from bingo.protocol import parse_message
from bingo.config import HOST, PORT
from bingo.logger import info
from bingo.logger import success
from bingo.logger import debug
from bingo.state import state
from bingo.network.client_manager import client_manager
from bingo.network.heartbeat import run_heartbeat
from bingo.network.session import ClientStatus

dispatcher = Dispatcher()


async def handle_client(websocket):

    session = client_manager.create_session(websocket)
    state.connected_clients = sum(1 for s in client_manager.get_all_sessions() if s.status == ClientStatus.CONNECTED)
    success(f"Client connected ({state.connected_clients} online)")

    heartbeat_task = asyncio.create_task(run_heartbeat(session))

    try:
            async for raw_message in websocket:

                message = parse_message(raw_message)

                if message.get("type") == "pong":
                    session.last_heartbeat = datetime.datetime.now()
                    session.missed_pings = 0
                    info("Heartbeat OK")
                    continue

                log_message = message.copy()
                
                if log_message.get("type") == "audio":
                    log_message["data"] = f"<{len(message['data'])} bytes base64>"
                
                debug(f"Received: {log_message}")

                try:
                    response = dispatcher.dispatch(message)
                    
                    while isinstance(response, dict):
                        response = dispatcher.dispatch(response)
                    
                    if response is not None:
                        await websocket.send(response)
                
                except Exception as e:
                    from bingo.logger import error
                
                    error(f"Dispatcher failed: {e}")

    finally:
        heartbeat_task.cancel()
        client_manager.disconnect_session(session)
        client_manager.remove_session(session)
        state.connected_clients = sum(1 for s in client_manager.get_all_sessions() if s.status == ClientStatus.CONNECTED)
        info(f"Client disconnected ({state.connected_clients} online)")


async def server():

    state.start_time = datetime.datetime.now()

    async with websockets.serve(
        handle_client,
        HOST,
        PORT
    ):

        info(f"Listening on ws://{HOST}:{PORT}")

        await asyncio.Future()


def start_server():

    asyncio.run(server())
