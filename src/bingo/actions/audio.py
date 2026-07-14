import base64
from pathlib import Path

from bingo.logger import info
from bingo.protocol import (
    MessageType,
    create_message,
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

    info(f"Audio saved: {path}")

    size = Path(path).stat().st_size

    info(f"Audio size: {size} bytes")

    if path.suffix.lower() != ".wav":

        return create_message(
            MessageType.STATUS,
            success=False,
            message="Only WAV files are supported."
        )

    return create_message(
        MessageType.STATUS,
        success=True,
        message=f"Saved {filename}"
    )