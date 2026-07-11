import subprocess

from protocol import (
    MessageType,
    create_message
)


def execute(message):

    command = message.get("command")
    target = message.get("target")

    if command == "open_program":

        if target == "system_settings":

            subprocess.Popen(["systemsettings"])

            return create_message(
                MessageType.STATUS,
                success=True,
                message="Opened system settings."
            )

    return create_message(
        MessageType.STATUS,
        success=False,
        message="Unknown command."
    )