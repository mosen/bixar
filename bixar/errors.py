class XarError(Exception):
    """Catch-all error"""
    pass


class XarFormatError(Exception):
    """Raised when the format of the XAR isnt something we can handle."""
    pass


class XarChecksumError(Exception):
    """Raised when you attempt to extract a file with an invalid checksum."""
    pass


class XarSigningError(Exception):
    """Raised when the xar signature is invalid."""
    pass

