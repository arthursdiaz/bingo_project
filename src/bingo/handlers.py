from bingo.actions import ping, command, status, audio
from bingo.protocol import MessageType

HANDLERS = {
    MessageType.PING.value: ping.execute,
    MessageType.COMMAND.value: command.execute,
    MessageType.STATUS.value: status.execute,
    MessageType.AUDIO.value: audio.execute,
}