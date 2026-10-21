import asyncio
import sys
from bingo.client.websocket import BingoClient
from bingo.parser import parse
from bingo.protocol import (
    MessageType,
    create_dict,
)

async def main():
    non_interactive = len(sys.argv) > 1
    cli_arg_command = " ".join(sys.argv[1:]).strip() if non_interactive else None

    if not non_interactive:
        print("======================")
        print("🤖 Bingo CLI")
        print("======================")

    client = BingoClient()

    try:
        await client.connect()
    except Exception as e:
        print(f"❌ Não foi possível conectar ao servidor Bingo: {e}")
        return
    
    try:
        while True:
            if non_interactive:
                command = cli_arg_command
            else:
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
            elif command in ("music", "musica", "playlist", "chromecast"):
                await client.send(
                    create_dict(
                        MessageType.COMMAND,
                        command="play_music",
                        target="playlist",
                    )
                )
            else:
                message = parse(command)
                if message is None:
                    print("❌ Não entendi.")
                    if non_interactive:
                        break
                    continue
                await client.send(message)

            response = await client.recv()

            if response.get("type") == "status_info":
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
            elif response.get("type") == "status":
                icon = "✅" if response.get("success") else "❌"
                print(f"\n{icon} {response.get('message')}\n")
            else:
                print(response)

            if non_interactive:
                break
            
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())