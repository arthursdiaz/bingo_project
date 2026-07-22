class BingoState:

    def __init__(self):

        import datetime
        self.start_time = datetime.datetime.now()

        self.connected_clients = 0

        self.last_command = None

        self.running_programs = set()


state = BingoState()