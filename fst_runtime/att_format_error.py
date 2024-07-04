class AttFormatError(Exception):
    """Exception raised for errors in the input ATT file format."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
