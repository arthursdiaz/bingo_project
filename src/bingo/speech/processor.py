import base64

from bingo.logger import info
from bingo.parser import parse
from bingo.speech.receiver import AudioReceiver
from bingo.speech.whisper import WhisperService
from bingo.speech.normalizer import SpeechNormalizer


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

        transcript = self.whisper.transcribe(path)

        normalizer = SpeechNormalizer()

        info(f"Transcript : {transcript}")

        normalized = normalizer.normalize(
            transcript
        )

        info(f"Normalized: {normalized}")
        
        return parse(normalized)