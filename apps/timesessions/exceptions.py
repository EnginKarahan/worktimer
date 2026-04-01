class AlreadyClockedInError(Exception):
    def __init__(self, entry=None):
        self.entry = entry
        super().__init__("Mitarbeiter ist bereits eingestempelt.")


class NotClockedInError(Exception):
    pass
