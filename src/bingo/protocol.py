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
    STATUS_INFO = "status_info"

    AUDIO = "audio"


def create_dict(message_type: MessageType, **kwargs):

    message = {
        "type": message_type.value
    }

    message.update(kwargs)

    return message


def create_message(message_type: MessageType, **kwargs):

    return json.dumps(
        create_dict(
            message_type,
            **kwargs
        )
    )

def parse_message(raw_message: str):
    """
    Converte uma mensagem JSON em dict.
    """

    return json.loads(raw_message)

def encode_message(message: dict):

    return json.dumps(message)