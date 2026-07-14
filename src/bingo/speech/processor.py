from bingo.speech.receiver import AudioReceiver
from bingo.speech.whisper import WhisperService


class AudioProcessor:

    def __init__(self):

        self.receiver = AudioReceiver()
        self.whisper = WhisperService()