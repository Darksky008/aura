"""Customer-safe error types. Technical detail goes to logs, never to the response."""


class AppError(Exception):
    status_code = 400
    public_message = "Something went wrong. Please try again."

    def __init__(self, public_message: str | None = None, *, status_code: int | None = None):
        super().__init__(public_message or self.public_message)
        if public_message:
            self.public_message = public_message
        if status_code:
            self.status_code = status_code


class NotFoundError(AppError):
    status_code = 404
    public_message = "We couldn't find that."


class ForbiddenError(AppError):
    status_code = 403
    public_message = "You don't have access to that."


class UnavailableError(AppError):
    status_code = 503
    public_message = "This service is temporarily unavailable."
