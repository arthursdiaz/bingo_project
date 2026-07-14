from bingo.speech.processor import AudioProcessor

from bingo.protocol import (
    MessageType,
    create_message,
)

processor = AudioProcessor()


def execute(message):

    text = processor.process(
        message["filename"],
        message["data"],
    )

    return create_message(
        MessageType.STATUS,
        success=True,
        message=text,
    )