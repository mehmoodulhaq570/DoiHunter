"""Backward-compatible import for the removed interactive proxy prompt."""


def waithIPchange():
    """Return false; automatic retry handling now lives in the HTTP session."""
    return False

