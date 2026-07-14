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

            command = input("\n> ").strip()

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
                print()
            
                print(f"Last command: {response['last_command']}")
                print()
            
                print("Programs:")
            
                for program in response["running_programs"]:
            
                    print(f" - {program}")
            
                print()
            else:
                print(response)
            
    finally:
        await client.close()

asyncio.run(main())