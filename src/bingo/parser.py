from bingo.protocol import (
    MessageType,
    create_message,
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


def parse(text: str):

    text = text.lower().strip()

    if text.startswith("abre"):

        target = text.removeprefix("abre").strip()

        # remove artigos
        for article in ("o ", "a ", "os ", "as "):
            if target.startswith(article):
                target = target.removeprefix(article)

        target = ALIASES.get(target, target)

        return create_message(
            MessageType.COMMAND,
            command="open_program",
            target=target,
        )

    return None