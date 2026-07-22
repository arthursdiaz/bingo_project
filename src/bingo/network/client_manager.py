from typing import Dict, List
from bingo.logger import info
from bingo.network.session import ClientSession, ClientStatus

class ClientManager:
    def __init__(self):
        self._sessions: Dict[int, ClientSession] = {}
        self._id_counter = 0
        self._total_connections = 0
        self._past_ips = set()

    def create_session(self, websocket) -> ClientSession:
        self._id_counter += 1
        self._total_connections += 1
        ip, port = websocket.remote_address

        if ip in self._past_ips:
            info("Reconnected")
        else:
            self._past_ips.add(ip)

        session = ClientSession(self._id_counter, ip, port, websocket)
        self._sessions[session.id] = session
        info(f"Client #{session.id} connected")
        return session

    def get_session(self, client_id: int) -> ClientSession:
        return self._sessions.get(client_id)

    def get_all_sessions(self) -> List[ClientSession]:
        return list(self._sessions.values())

    @property
    def total_connections(self) -> int:
        return self._total_connections

    def disconnect_session(self, session: ClientSession):
        if session.status == ClientStatus.CONNECTED:
            session.status = ClientStatus.DISCONNECTED

    def remove_session(self, session: ClientSession):
        if session.id in self._sessions:
            del self._sessions[session.id]
            info("Client removed")

client_manager = ClientManager()
