import asyncio
from bingo.logger import info
from bingo.protocol import create_message, MessageType
from bingo.network.session import ClientSession, ClientStatus

async def run_heartbeat(session: ClientSession):
    try:
        while True:
            await asyncio.sleep(10)

            if session.status != ClientStatus.CONNECTED:
                break

            try:
                ping_message = create_message(MessageType.PING)
                await session.websocket.send(ping_message)
                session.missed_pings += 1
            except Exception:
                session.status = ClientStatus.TIMEOUT
                info("Heartbeat timeout")
                try:
                    await session.websocket.close()
                except Exception:
                    pass
                break

            # If client misses 3 consecutive cycles (30 seconds)
            if session.missed_pings >= 3:
                session.status = ClientStatus.TIMEOUT
                info("Heartbeat timeout")
                try:
                    await session.websocket.close()
                except Exception:
                    pass
                break
    except asyncio.CancelledError:
        pass
