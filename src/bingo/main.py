from bingo.server import start_server
from bingo.config import NAME, VERSION
from bingo.logger import info

def main():
    print(f"🤖 {NAME} Core {VERSION}")
    info("Starting server...")

    start_server()


if __name__ == "__main__":
    main()