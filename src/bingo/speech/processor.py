import base64

from bingo.logger import info

from bingo.speech.receiver import AudioReceiver
from bingo.speech.whisper import WhisperService


class AudioProcessor:

    def __init__(self):

        self.receiver = AudioReceiver()
        self.whisper = WhisperService()

    def process(self, filename, encoded_audio):

        data = base64.b64decode(
            encoded_audio
        )

        path = self.receiver.save(
            filename,
            data
        )

        info(f"Saved: {path}")

        text = self.whisper.transcribe(
            path
        )

        info(f"Transcript: {text}")

        return text