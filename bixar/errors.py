class XarError(Exception):
    pass


class XarChecksumError(Exception):
    """Raised when you attempt to extract a file with an invalid checksum."""
    pass
