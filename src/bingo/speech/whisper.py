from bingo.speech.service import SpeechService


class WhisperService(SpeechService):

    def transcribe(
        self,
        path
    ):

        print(path)

        return "placeholder"