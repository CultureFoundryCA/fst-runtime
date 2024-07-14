"""
att_format_error

This module defines custom exceptions used for handling errors specific to the AT&T file format (.att file) processing.

Classes
-------
AttFormatError
    Exception raised for errors in the input AT&T file format (.att file).
"""


class AttFormatError(Exception):
    """
    Exception raised for errors in the input AT&T file format (.att file).

    Parameters
    ----------
    message : str
        The error message to be displayed.

    Attributes
    ----------
    message : str
        The error message to be displayed.
    """

    def __init__(self, message: str):
        """
        Initializes the AttFormatError with a given error message.

        Parameters
        ----------
        message : str
            The error message to be displayed.
        """
        self.message = message
        super().__init__(self.message)
