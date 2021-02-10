class FetchFailureError(Exception):
    def __init__(self, reason: str):
        super(FetchFailureError, self).__init__()
        self.reason = reason
