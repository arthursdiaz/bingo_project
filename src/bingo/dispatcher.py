from bingo.handlers import HANDLERS


class Dispatcher:

    def dispatch(self, message):

        handler = HANDLERS.get(message.get("type"))

        if handler is None:
            return None

        return handler(message)