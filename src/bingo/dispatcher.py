from bingo.protocol import (
    MessageType,
    create_message,
)

from bingo.actions import ping
from bingo.actions import command


class Dispatcher:

    def dispatch(self, message):

        message_type = message.get("type")

        handlers = {

            MessageType.PING.value:
                ping.execute,

            MessageType.COMMAND.value:
                command.execute,
        }

        handler = handlers.get(message_type)

        if handler:

            return handler(message)

        return create_message(
            MessageType.STATUS,
            success=False,
            message="Unknown message type."
        )