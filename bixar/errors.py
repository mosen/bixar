class XarError(Exception):
    """Catch-all error"""
    pass


class XarChecksumError(Exception):
    """Raised when you attempt to extract a file with an invalid checksum."""
    pass


class XarSigningError(Exception):
    """Raised when the xar signature is invalid."""
    pass

