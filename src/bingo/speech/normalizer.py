import re

VERBS = {
    "abrir": "abre",
    "abri": "abre",
    "abra": "abre",
    "abre": "abre",
}

STOPWORDS = {
    "o",
    "a",
    "os",
    "as",
    "um",
    "uma",
    "por",
    "favor",
    "pra",
    "para",
    "você",
    "voce",
    "consegue",
    "pode",
    "porfavor",
}


class SpeechNormalizer:

    def normalize(self, text: str) -> str:

        text = text.lower()

        text = re.sub(
            r"[^\w\s]",
            "",
            text
        )

        words = []

        for word in text.split():

            word = VERBS.get(
                word,
                word
            )

            if word in STOPWORDS:
                continue

            words.append(word)

        return " ".join(words)