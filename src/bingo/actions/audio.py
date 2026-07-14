from bingo.speech.processor import AudioProcessor

from bingo.protocol import (
    MessageType,
    create_message,
)

processor = AudioProcessor()

def execute(message):

    command = processor.process(
        message["filename"],
        message["data"],
    )

    if command is None:

        return create_message(
            MessageType.STATUS,
            success=False,
            message="Couldn't understand speech."
        )

    return command