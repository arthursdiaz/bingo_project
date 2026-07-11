from enum import Enum
import json


class MessageType(str, Enum):
    PING = "ping"
    PONG = "pong"

    COMMAND = "command"

    SPEECH = "speech"
    SPEAK = "speak"

    EMOTION = "emotion"

    STATUS = "status"


def create_message(message_type: MessageType, **kwargs):
    """
    Cria uma mensagem JSON padronizada.
    """

    message = {
        "type": message_type.value
    }

    message.update(kwargs)

    return json.dumps(message)


def parse_message(raw_message: str):
    """
    Converte uma mensagem JSON em dict.
    """

    return json.loads(raw_message)