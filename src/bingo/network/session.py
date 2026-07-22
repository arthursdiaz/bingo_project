import datetime
from enum import Enum

class ClientStatus(str, Enum):
    CONNECTED = "CONNECTED"
    TIMEOUT = "TIMEOUT"
    DISCONNECTED = "DISCONNECTED"

class ClientSession:
    def __init__(self, client_id: int, ip: str, port: int, websocket):
        self.id = client_id
        self.ip = ip
        self.port = port
        self.websocket = websocket
        self.connected_at = datetime.datetime.now()
        self.last_heartbeat = datetime.datetime.now()
        self.status = ClientStatus.CONNECTED
        self.missed_pings = 0

    @property
    def connection_time(self) -> int:
        """Returns the connection time in seconds."""
        return int((datetime.datetime.now() - self.connected_at).total_seconds())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ip": self.ip,
            "port": self.port,
            "last_heartbeat": self.last_heartbeat.strftime("%H:%M:%S") if self.last_heartbeat else None,
            "connected_time": self.connection_time,
            "status": self.status.value,
        }
