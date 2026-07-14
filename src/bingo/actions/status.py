from bingo.logger import info
from bingo.state import state
from bingo.protocol import MessageType, create_message


def execute(message):

    response = create_message(
        MessageType.STATUS_INFO,
        clients=state.connected_clients,
        last_command=state.last_command,
        running_programs=list(state.running_programs),
    )

    return response