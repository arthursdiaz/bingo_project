import datetime
from bingo.logger import info
from bingo.state import state
from bingo.protocol import MessageType, create_message
from bingo.network.client_manager import client_manager


def execute(message):

    uptime = int((datetime.datetime.now() - state.start_time).total_seconds()) if hasattr(state, "start_time") else 0
    clients_info = [s.to_dict() for s in client_manager.get_all_sessions()]

    response = create_message(
        MessageType.STATUS_INFO,
        clients=state.connected_clients,
        last_command=state.last_command,
        running_programs=list(state.running_programs),
        uptime=uptime,
        clients_info=clients_info,
        total_connections=client_manager.total_connections,
    )

    return response