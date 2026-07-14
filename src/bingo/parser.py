import string
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

    "vivaldi": "vivaldi",

    "steam": "steam",
    "zed": "zed",
}

OPEN_WORDS = (
    "abre",
    "abrir",
    "abra",
)


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

            target = ALIASES.get(target, target)

            return create_dict(
                MessageType.COMMAND,
                command="open_program",
                target=target,
            )

    return None