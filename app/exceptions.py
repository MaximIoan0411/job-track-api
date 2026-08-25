class AppException(Exception):
    """Exceptie de baza"""


class ApplicationNotFoundError(AppException):
    pass


class InvalidStateError(AppException):
    pass


class VersionConflictError(AppException):
    pass