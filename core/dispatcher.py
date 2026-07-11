# TODO:
# - Command Handler
# - Speech Handler
# - Emotion Handler
# - Status Handler

from protocol import (
    MessageType,
    create_message,
)


class Dispatcher:

    def dispatch(self, message):

        message_type = message.get("type")

        match message_type:

            case MessageType.PING.value:

                return create_message(
                    MessageType.PONG
                )

            case _:

                print(f"Unknown message type: {message_type}")

                return None