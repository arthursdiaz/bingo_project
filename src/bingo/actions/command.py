import subprocess

from bingo.logger import info
from bingo.state import state
from bingo.protocol import (
    MessageType,
    create_dict,
)

PROGRAMS = {
    "system_settings": "systemsettings",
    "vivaldi": "vivaldi",
    "steam": "steam",
    "zed": "zed",
    "konsole": "konsole",
}

PROGRAM_PROCESSES = {
    "vivaldi": "vivaldi",
    "steam": "steam",
    "zed": "zed",
    "konsole": "konsole",
}


def execute(message):

    command = message.get("command")
    target = message.get("target")

    if target not in PROGRAMS:

        return create_dict(
            MessageType.STATUS,
            success=False,
            message=f"Unknown program: {target}"
        )

    try:

        if command == "open_program":

            subprocess.Popen([PROGRAMS[target]])

            state.running_programs.add(target)
            state.last_command = f"open {target}"

            action = "Opened"

        elif command == "close_program":

            process = PROGRAM_PROCESSES.get(target)

            if process is None:

                return create_dict(
                    MessageType.STATUS,
                    success=False,
                    message=f"Cannot close {target}"
                )

            subprocess.run(
                ["pkill", "-f", process],
                check=False,
            )

            state.running_programs.discard(target)
            state.last_command = f"close {target}"

            action = "Closed"

        else:

            return create_dict(
                MessageType.STATUS,
                success=False,
                message="Invalid command."
            )

        info(f"Connected clients: {state.connected_clients}")
        info(f"Running programs: {list(state.running_programs)}")
        info(f"Last command: {state.last_command}")

        return create_dict(
            MessageType.STATUS,
            success=True,
            message=f"{action} {target}."
        )

    except Exception as e:

        return create_dict(
            MessageType.STATUS,
            success=False,
            message=str(e)
        )