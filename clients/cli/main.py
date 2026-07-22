import asyncio
from bingo.client.websocket import BingoClient
from bingo.parser import parse
from bingo.protocol import (
    MessageType,
    create_dict,
)

async def main():

    print("======================")
    print("🤖 Bingo CLI")
    print("======================")

    client = BingoClient()

    await client.connect()
    
    try:

        while True:

            command = await asyncio.to_thread(input, "\n> ")
            command = command.strip()

            if command == "exit":
                break

            if command == "ping":
            
                await client.send(
                    create_dict(MessageType.PING)
                )
            
            elif command == "status":
            
                await client.send(
                    create_dict(MessageType.STATUS)
                )
            
            else:
            
                message = parse(command)
            
                if message is None:
                    print("❌ Não entendi.")
                    continue
            
                await client.send(message)
            
            response = await client.recv()

            if response["type"] == "status_info":
            
                print()
                print("========================")
                print("🤖 Bingo Status")
                print("========================")
                print()
            
                print(f"Clients: {response['clients']}")
                print(f"Total Connections: {response.get('total_connections', 0)}")
                print(f"Server Uptime: {response.get('uptime', 0)} seconds")
                print()
            
                print(f"Last command: {response['last_command']}")
                print()
            
                print("Programs:")
            
                for program in response["running_programs"]:
            
                    print(f" - {program}")
            
                print()

                clients_info = response.get("clients_info", [])
                if clients_info:
                    print("Connected Clients Info:")
                    for c in clients_info:
                        print(f" - Client #{c['id']} ({c['ip']}:{c['port']}) | Status: {c['status']} | Connected: {c['connected_time']}s | Last Heartbeat: {c['last_heartbeat']}")
                    print()
            else:
                print(response)
            
    finally:
        await client.close()

asyncio.run(main())