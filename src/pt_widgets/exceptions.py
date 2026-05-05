class PTWidgetsError(Exception):
    """Base class for exceptions in this module."""
    pass


class FocusException(PTWidgetsError):
    """Raised when an element cannot be focused."""
    pass
