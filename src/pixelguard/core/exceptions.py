class PixelGuardError(Exception):
    """Base exception for PixelGuard."""


class ImageLoadError(PixelGuardError):
    pass


class DetectionError(PixelGuardError):
    pass


class ConfigurationError(PixelGuardError):
    pass


class ReportingError(PixelGuardError):
    pass
