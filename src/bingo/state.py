class BingoState:

    def __init__(self):

        self.connected_clients = 0

        self.last_command = None

        self.running_programs = set()


state = BingoState()