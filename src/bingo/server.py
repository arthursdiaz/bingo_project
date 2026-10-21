import datetime
import asyncio

import websockets

from bingo.dispatcher import Dispatcher
from bingo.protocol import (
    MessageType,
    create_dict,
    encode_message,
    parse_message,
)
from bingo.config import HOST, PORT
from bingo.logger import info, success, debug, error
from bingo.state import state
from bingo.network.client_manager import client_manager
from bingo.network.heartbeat import run_heartbeat
from bingo.network.session import ClientStatus

dispatcher = Dispatcher()
music_lock = asyncio.Lock()


async def run_music_task(websocket, message: dict):
    """
    Executa a automação musical em thread separada para não bloquear o event loop do WebSocket.
    Garante sincronização através do music_lock e devolve o resultado final estruturado ao cliente.
    """
    async with music_lock:
        try:
            response = await asyncio.to_thread(dispatcher.dispatch, message)

            while isinstance(response, dict) and response.get("type") == MessageType.COMMAND.value:
                response = await asyncio.to_thread(dispatcher.dispatch, response)

            if isinstance(response, dict):
                if "id" in message and "id" not in response:
                    response["id"] = message["id"]
                response = encode_message(response)

            if response is not None:
                await websocket.send(response)

        except websockets.ConnectionClosed:
            debug("Cliente desconectou durante a execução da automação musical.")
        except Exception as e:
            error(f"Erro ao executar automação de música: {e}")
            try:
                err_resp = create_dict(
                    MessageType.STATUS,
                    success=False,
                    status="error",
                    command="play_music",
                    message=f"Erro interno durante a execução: {e}",
                    data={"mode": "internal_error", "error": str(e)},
                )
                if "id" in message:
                    err_resp["id"] = message["id"]
                await websocket.send(encode_message(err_resp))
            except websockets.ConnectionClosed:
                pass


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
                # Caso especial: Comando de reprodução de música (via comando explícito ou type music)
                is_music_cmd = (
                    message.get("type") == MessageType.MUSIC.value
                    or (
                        message.get("type") == MessageType.COMMAND.value
                        and message.get("command") == "play_music"
                    )
                )

                if is_music_cmd:
                    if music_lock.locked():
                        busy_resp = create_dict(
                            MessageType.STATUS,
                            success=False,
                            status="busy",
                            command="play_music",
                            message="Uma solicitação de reprodução musical já está em andamento. Aguarde a conclusão.",
                            data={"mode": "already_in_progress"},
                        )
                        if "id" in message:
                            busy_resp["id"] = message["id"]
                        await websocket.send(encode_message(busy_resp))
                        continue

                    # 1. Notifica imediatamente que a solicitação foi aceita e está em processamento
                    ack_msg = create_dict(
                        MessageType.STATUS,
                        status="in_progress",
                        command="play_music",
                        message="Solicitação recebida. Iniciando automação e conectando ao Chromecast...",
                    )
                    if "id" in message:
                        ack_msg["id"] = message["id"]
                    await websocket.send(encode_message(ack_msg))

                    # 2. Executa a tarefa de forma assíncrona em segundo plano sem travar o loop
                    asyncio.create_task(run_music_task(websocket, message))
                    continue

                # Processamento padrão para outros comandos (síncronos / rápidos)
                response = dispatcher.dispatch(message)

                # Resolve cadeias de comando (por exemplo, audio.execute -> command.execute)
                while isinstance(response, dict) and response.get("type") == MessageType.COMMAND.value:
                    if response.get("command") == "play_music":
                        if "id" in message and "id" not in response:
                            response["id"] = message["id"]

                        if music_lock.locked():
                            busy_resp = create_dict(
                                MessageType.STATUS,
                                success=False,
                                status="busy",
                                command="play_music",
                                message="Uma solicitação de reprodução musical já está em andamento. Aguarde a conclusão.",
                                data={"mode": "already_in_progress"},
                            )
                            if "id" in message:
                                busy_resp["id"] = message["id"]
                            await websocket.send(encode_message(busy_resp))
                        else:
                            ack_msg = create_dict(
                                MessageType.STATUS,
                                status="in_progress",
                                command="play_music",
                                message="Solicitação de voz recebida. Iniciando automação musical...",
                            )
                            if "id" in message:
                                ack_msg["id"] = message["id"]
                            await websocket.send(encode_message(ack_msg))
                            asyncio.create_task(run_music_task(websocket, response))

                        response = None
                        break

                    response = dispatcher.dispatch(response)

                if isinstance(response, dict):
                    if "id" in message and "id" not in response:
                        response["id"] = message["id"]
                    response = encode_message(response)

                if response is not None:
                    await websocket.send(response)

            except Exception as e:
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
