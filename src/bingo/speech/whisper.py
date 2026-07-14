from faster_whisper import WhisperModel

from bingo.logger import info


class WhisperService:

    def __init__(self):

        info("Loading Whisper model...")

        self.model = WhisperModel(
            "base",
            device="cpu",
            compute_type="int8",
        )

        info("Whisper loaded!")

    def transcribe(self, path):

        segments, info_data = self.model.transcribe(
            str(path),
            language="pt",
        )

        text = ""

        for segment in segments:
            text += segment.text

        return text.strip()