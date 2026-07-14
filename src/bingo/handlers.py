from bingo.actions import ping, command, status
from bingo.protocol import MessageType

HANDLERS = {
    MessageType.PING.value: ping.execute,
    MessageType.COMMAND.value: command.execute,
    MessageType.STATUS.value: status.execute,
}