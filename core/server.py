import asyncio
import websockets


HOST = "0.0.0.0"
PORT = 8765


async def handle_client(websocket):
    print("📱 Client connected")

    async for message in websocket:
        print(f"Received: {message}")

        if message == "ping":
            await websocket.send("pong")


async def server():
    async with websockets.serve(handle_client, HOST, PORT):
        print(f"🌐 Listening on ws://{HOST}:{PORT}")

        await asyncio.Future()


def start_server():
    asyncio.run(server())