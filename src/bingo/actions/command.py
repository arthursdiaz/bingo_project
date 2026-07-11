import subprocess
from bingo.state import state
from bingo.logger import info
from bingo.protocol import (
    MessageType,
    create_message,
)

PROGRAMS = {
    "system_settings": "systemsettings",
    "vivaldi": "vivaldi",
    "steam": "steam",
    "zed": "zed",
    "konsole": "konsole",
}


def execute(message):

    command = message.get("command")
    target = message.get("target")

    if command != "open_program":

        return create_message(
            MessageType.STATUS,
            success=False,
            message="Invalid command."
        )

    program = PROGRAMS.get(target)

    if program is None:

        return create_message(
            MessageType.STATUS,
            success=False,
            message=f"Unknown program: {target}"
        )

    try:
        subprocess.Popen([program])
        
        state.running_programs.add(target)
        state.last_command = f"open {target}"
        
        info(f"Connected clients: {state.connected_clients}")
        info(f"Running programs: {list(state.running_programs)}")
        info(f"Last command: {state.last_command}")
        
        return create_message(
            MessageType.STATUS,
            success=True,
            message=f"Opened {target}."
        )
    
    except Exception as e:
    
        return create_message(
            MessageType.STATUS,
            success=False,
            message=str(e)
        )