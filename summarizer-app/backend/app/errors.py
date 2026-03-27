from fastapi import Request
from fastapi.responses import JSONResponse


class SummarizerError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class UnsupportedFormatError(SummarizerError):
    def __init__(self, format_name: str):
        super().__init__(f"Unsupported file format: {format_name}", 400)


class FileTooLargeError(SummarizerError):
    def __init__(self):
        super().__init__("File size exceeds the 10MB limit.", 413)


class BatchLimitExceededError(SummarizerError):
    def __init__(self):
        super().__init__(
            "Batch processing is limited to 10 files per request.", 400
        )


class ExtractionError(SummarizerError):
    def __init__(self, detail: str = ""):
        super().__init__(
            f"Failed to extract text from the provided input. {detail}".strip(), 422
        )


class SummarizationError(SummarizerError):
    def __init__(self, detail: str = ""):
        super().__init__(f"Summarization failed. {detail}".strip(), 500)


class AuthenticationError(SummarizerError):
    def __init__(self):
        super().__init__("Invalid or missing authentication token.", 401)


async def summarizer_error_handler(request: Request, exc: SummarizerError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message},
    )
