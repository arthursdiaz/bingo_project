import subprocess

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

    subprocess.Popen([program])

    return create_message(
        MessageType.STATUS,
        success=True,
        message=f"Opened {target}."
    )