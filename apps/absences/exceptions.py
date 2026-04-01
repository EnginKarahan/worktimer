class InsufficientVacationError(Exception):
    def __init__(self, available, requested):
        self.available = available
        self.requested = requested
        super().__init__(f"Unzureichend Urlaub: {available} Tage verfügbar, {requested} beantragt.")


class InsufficientOvertimeError(Exception):
    def __init__(self, available, requested):
        self.available = available
        self.requested = requested
        super().__init__(f"Unzureichend Überstunden: {available:.1f} Tage verfügbar.")
