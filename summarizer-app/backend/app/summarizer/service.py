import uuid
from datetime import datetime, timezone
from typing import Optional
from ..config import settings
from ..errors import FileTooLargeError, BatchLimitExceededError, SummarizerError
from ..logger import get_logger
from .utils import extract_text
from .engine import summarize

# In-memory history store (per user)
summary_history: dict = {}


class SummarizerService:
    """Orchestrates input parsing, AI summarization, and history tracking.

    All AI logic and multi-format input processing is handled here.
    Routing layers (api.py, ui.py) delegate to this service.
    """

    @staticmethod
    def process_and_summarize(
        content: Optional[str] = None,
        file_bytes: Optional[bytes] = None,
        filename: Optional[str] = None,
        url: Optional[str] = None,
        summary_length: str = "medium",
        user_id: str = "anonymous",
    ) -> dict:
        """Parse input from any supported format, summarize via Azure OpenAI,
        and store the result in history."""
        log = get_logger(user_id)
        log.info(f"Summarize request: length={summary_length}")

        # Validate file size and determine source type
        source_type = "text"
        if file_bytes and filename:
            if len(file_bytes) > settings.MAX_FILE_SIZE:
                raise FileTooLargeError()
            source_type = "file"
        elif url:
            source_type = "url"

        # Extract text from the provided input format
        extracted = extract_text(
            content=content, file_bytes=file_bytes, filename=filename, url=url
        )

        # Send extracted text to Azure OpenAI for summarization
        result = summarize(extracted, length=summary_length, user_id=user_id)

        # Store in per-user history and return the record
        record = SummarizerService.store_summary(
            user_id, result, summary_length, source_type
        )
        log.info(f"Summarization completed: source={source_type}")
        return record

    @staticmethod
    def batch_process(
        files_data: list,
        summary_length: str = "medium",
        user_id: str = "anonymous",
    ) -> dict:
        """Process multiple files in a single batch request."""
        log = get_logger(user_id)
        if len(files_data) > settings.MAX_BATCH_SIZE:
            raise BatchLimitExceededError()

        results = []
        errors = []

        for file_bytes, filename in files_data:
            try:
                record = SummarizerService.process_and_summarize(
                    file_bytes=file_bytes,
                    filename=filename,
                    summary_length=summary_length,
                    user_id=user_id,
                )
                results.append(record)
                log.info(f"Batch item '{filename}' summarized successfully")
            except SummarizerError as e:
                log.warning(f"Batch item '{filename}' failed: {e.message}")
                errors.append({"filename": filename, "error": e.message})
            except Exception as e:
                log.error(f"Batch item '{filename}' unexpected error: {str(e)}")
                errors.append({"filename": filename, "error": str(e)})

        return {"results": results, "errors": errors}

    @staticmethod
    def store_summary(
        user_id: str, summary: str, length: str, source_type: str
    ) -> dict:
        """Create a history record and store it for the given user."""
        record = {
            "id": str(uuid.uuid4()),
            "summary": summary,
            "summary_length": length,
            "source_type": source_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if user_id not in summary_history:
            summary_history[user_id] = []
        summary_history[user_id].append(record)
        return record

    @staticmethod
    def get_history(user_id: str) -> list:
        """Retrieve summary history for a specific user."""
        return summary_history.get(user_id, [])
