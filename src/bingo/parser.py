import string
from rapidfuzz import process
from bingo.protocol import (
    MessageType,
    create_dict,
)

ALIASES = {

    "config": "system_settings",
    "configuracao": "system_settings",
    "configuracoes": "system_settings",
    "configuração": "system_settings",
    "configurações": "system_settings",

    "terminal": "konsole",
    "console": "konsole",

    "vivaldi": "vivaldi",

    "steam": "steam",

    "zed": "zed",
}

OPEN_WORDS = (
    "abre",
    "abrir",
    "abra",
    "abri",
    "abra o",
    "abre o",
)

CLOSE_WORDS = (
    "fecha",
    "fechar",
    "feche",
    "encerra",
    "encerrar",
)

def fuzzy_target(word: str):

    result = process.extractOne(
        word,
        ALIASES.keys(),
        score_cutoff=70,
    )

    if result is None:
        return word

    return result[0]

def parse(text: str):

    text = text.lower().strip()
    text = text.translate(
        str.maketrans("", "", string.punctuation)
    )

    for word in OPEN_WORDS:

        if text.startswith(word):

            target = text.removeprefix(word).strip()

            # remove artigos
            for article in ("o ", "a ", "os ", "as "):
                if target.startswith(article):
                    target = target.removeprefix(article)

            target = fuzzy_target(target)

            target = ALIASES.get(
                target,
                target
            )

            return create_dict(
                MessageType.COMMAND,
                command="open_program",
                target=target,
            )

    for word in CLOSE_WORDS:

        if text.startswith(word):

            target = text.removeprefix(word).strip()

            for article in ("o ", "a ", "os ", "as "):
                if target.startswith(article):
                    target = target.removeprefix(article)

            target = fuzzy_target(target)

            target = ALIASES.get(
                target,
                target
            )

            return create_dict(
                MessageType.COMMAND,
                command="close_program",
                target=target,
            )

    return None