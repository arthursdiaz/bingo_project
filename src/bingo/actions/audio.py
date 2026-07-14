import base64

from bingo.protocol import (
    create_message,
    MessageType,
)

from bingo.speech.receiver import AudioReceiver

receiver = AudioReceiver()


def execute(message):

    filename = message["filename"]

    data = base64.b64decode(
        message["data"]
    )

    path = receiver.save(
        filename,
        data
    )

    print(path)

    return create_message(
        MessageType.STATUS,
        success=True,
        message=f"Saved {filename}"
    )