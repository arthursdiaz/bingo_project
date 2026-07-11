from datetime import datetime


def _timestamp():
    return datetime.now().strftime("%H:%M:%S")


def info(message: str):
    print(f"[{_timestamp()}] INFO    {message}")


def success(message: str):
    print(f"[{_timestamp()}] SUCCESS {message}")


def warning(message: str):
    print(f"[{_timestamp()}] WARNING {message}")


def error(message: str):
    print(f"[{_timestamp()}] ERROR   {message}")

def debug(message: str):
    print(f"[{_timestamp()}] DEBUG   {message}")