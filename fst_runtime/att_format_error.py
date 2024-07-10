'''
att_format_error

This module defines custom exceptions used for handling errors specific to the AT&T file format (.att file) processing.
'''

class AttFormatError(Exception):
    """Exception raised for errors in the input AT&T file format (.att file)."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
