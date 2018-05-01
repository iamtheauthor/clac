"""This module defines exceptions common the CLAC package."""


class NoConfigKey(LookupError):
    """The requested configuration key was not found."""
    pass


class MissingLayer(LookupError):
    """The layer specified was not found."""
    pass
