from protocol import MessageType, create_message


def execute(message):

    return create_message(
        MessageType.PONG
    )