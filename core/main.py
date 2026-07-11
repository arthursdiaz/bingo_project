from server import start_server
from config import NAME, VERSION

def main():
    print(f"🤖 {NAME} Core {VERSION}")
    print("Starting server...\n")

    start_server()


if __name__ == "__main__":
    main()