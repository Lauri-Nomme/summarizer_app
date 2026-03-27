import pytest
from unittest.mock import patch, MagicMock
from backend.app.summarizer.service import SummarizerService, summary_history
from backend.app.errors import (
    FileTooLargeError,
    BatchLimitExceededError,
    ExtractionError,
    UnsupportedFormatError,
    SummarizationError,
)


class TestServiceMultiFormatInput:
    """Feature: Multi-format Input Support
    Verifies the service correctly routes text, PDF, DOCX, and URL inputs
    through extraction and summarization, and returns user-friendly errors
    for unsupported or corrupted inputs.
    """

    def setup_method(self):
        summary_history.clear()

    @patch("backend.app.summarizer.service.summarize")
    @patch("backend.app.summarizer.service.extract_text")
    def test_plain_text_input(self, mock_extract, mock_summarize):
        mock_extract.return_value = "Extracted text"
        mock_summarize.return_value = "Summary of text"

        record = SummarizerService.process_and_summarize(
            content="Some plain text", summary_length="short", user_id="user1"
        )

        mock_extract.assert_called_once_with(
            content="Some plain text", file_bytes=None, filename=None, url=None
        )
        mock_summarize.assert_called_once_with(
            "Extracted text", length="short", user_id="user1"
        )
        assert record["summary"] == "Summary of text"
        assert record["source_type"] == "text"
        assert record["summary_length"] == "short"

    @patch("backend.app.summarizer.service.summarize")
    @patch("backend.app.summarizer.service.extract_text")
    def test_pdf_file_input(self, mock_extract, mock_summarize):
        mock_extract.return_value = "PDF content extracted"
        mock_summarize.return_value = "PDF summary"

        record = SummarizerService.process_and_summarize(
            file_bytes=b"fake-pdf-bytes",
            filename="report.pdf",
            summary_length="medium",
            user_id="user1",
        )

        mock_extract.assert_called_once_with(
            content=None, file_bytes=b"fake-pdf-bytes", filename="report.pdf", url=None
        )
        assert record["source_type"] == "file"
        assert record["summary"] == "PDF summary"

    @patch("backend.app.summarizer.service.summarize")
    @patch("backend.app.summarizer.service.extract_text")
    def test_docx_file_input(self, mock_extract, mock_summarize):
        mock_extract.return_value = "DOCX content extracted"
        mock_summarize.return_value = "DOCX summary"

        record = SummarizerService.process_and_summarize(
            file_bytes=b"fake-docx-bytes",
            filename="document.docx",
            summary_length="long",
            user_id="user1",
        )

        mock_extract.assert_called_once_with(
            content=None, file_bytes=b"fake-docx-bytes", filename="document.docx", url=None
        )
        assert record["source_type"] == "file"
        assert record["summary"] == "DOCX summary"

    @patch("backend.app.summarizer.service.summarize")
    @patch("backend.app.summarizer.service.extract_text")
    def test_url_input(self, mock_extract, mock_summarize):
        mock_extract.return_value = "Web page content"
        mock_summarize.return_value = "URL summary"

        record = SummarizerService.process_and_summarize(
            url="https://example.com/article",
            summary_length="short",
            user_id="user1",
        )

        mock_extract.assert_called_once_with(
            content=None, file_bytes=None, filename=None, url="https://example.com/article"
        )
        assert record["source_type"] == "url"
        assert record["summary"] == "URL summary"

    @patch("backend.app.summarizer.service.extract_text")
    def test_unsupported_format_returns_clear_error(self, mock_extract):
        mock_extract.side_effect = UnsupportedFormatError(".xyz")

        with pytest.raises(UnsupportedFormatError, match="Unsupported file format: .xyz"):
            SummarizerService.process_and_summarize(
                file_bytes=b"data", filename="file.xyz"
            )

    @patch("backend.app.summarizer.service.extract_text")
    def test_corrupted_file_returns_clear_error(self, mock_extract):
        mock_extract.side_effect = ExtractionError("Could not read PDF: corrupt file")

        with pytest.raises(ExtractionError, match="Could not read PDF"):
            SummarizerService.process_and_summarize(
                file_bytes=b"corrupt", filename="bad.pdf"
            )

    def test_file_too_large_returns_clear_error(self):
        large_bytes = b"x" * (10 * 1024 * 1024 + 1)

        with pytest.raises(FileTooLargeError, match="10MB limit"):
            SummarizerService.process_and_summarize(
                file_bytes=large_bytes, filename="huge.pdf"
            )

    @patch("backend.app.summarizer.service.extract_text")
    def test_no_input_returns_clear_error(self, mock_extract):
        mock_extract.side_effect = ExtractionError("No input provided")

        with pytest.raises(ExtractionError, match="No input provided"):
            SummarizerService.process_and_summarize()


class TestServiceConfigurableSummaryLength:
    """Feature: Configurable Summary Length
    Verifies the service passes the correct summary_length parameter
    (short, medium, long) through to the AI engine.
    """

    def setup_method(self):
        summary_history.clear()

    @patch("backend.app.summarizer.service.summarize")
    @patch("backend.app.summarizer.service.extract_text")
    def test_short_summary_length(self, mock_extract, mock_summarize):
        mock_extract.return_value = "text"
        mock_summarize.return_value = "Short."

        record = SummarizerService.process_and_summarize(
            content="text", summary_length="short"
        )
        mock_summarize.assert_called_once_with("text", length="short", user_id="anonymous")
        assert record["summary_length"] == "short"

    @patch("backend.app.summarizer.service.summarize")
    @patch("backend.app.summarizer.service.extract_text")
    def test_medium_summary_length(self, mock_extract, mock_summarize):
        mock_extract.return_value = "text"
        mock_summarize.return_value = "Medium paragraph summary."

        record = SummarizerService.process_and_summarize(
            content="text", summary_length="medium"
        )
        mock_summarize.assert_called_once_with("text", length="medium", user_id="anonymous")
        assert record["summary_length"] == "medium"

    @patch("backend.app.summarizer.service.summarize")
    @patch("backend.app.summarizer.service.extract_text")
    def test_long_summary_length(self, mock_extract, mock_summarize):
        mock_extract.return_value = "text"
        mock_summarize.return_value = "Long detailed comprehensive summary."

        record = SummarizerService.process_and_summarize(
            content="text", summary_length="long"
        )
        mock_summarize.assert_called_once_with("text", length="long", user_id="anonymous")
        assert record["summary_length"] == "long"

    @patch("backend.app.summarizer.service.summarize")
    @patch("backend.app.summarizer.service.extract_text")
    def test_default_summary_length_is_medium(self, mock_extract, mock_summarize):
        mock_extract.return_value = "text"
        mock_summarize.return_value = "Default summary."

        record = SummarizerService.process_and_summarize(content="text")
        mock_summarize.assert_called_once_with("text", length="medium", user_id="anonymous")
        assert record["summary_length"] == "medium"

    @patch("backend.app.summarizer.service.extract_text")
    def test_invalid_summary_length_propagates_error(self, mock_extract):
        mock_extract.return_value = "text"
        with patch("backend.app.summarizer.service.summarize") as mock_summarize:
            mock_summarize.side_effect = SummarizationError(
                "Invalid summary length 'tiny'."
            )
            with pytest.raises(SummarizationError, match="Invalid summary length"):
                SummarizerService.process_and_summarize(
                    content="text", summary_length="tiny"
                )


class TestServiceBatchProcessing:
    """Feature: Batch Processing
    Verifies the service handles batch file processing with proper
    error isolation, logging, and the 10-file limit.
    """

    def setup_method(self):
        summary_history.clear()

    @patch("backend.app.summarizer.service.summarize")
    @patch("backend.app.summarizer.service.extract_text")
    def test_batch_multiple_files_success(self, mock_extract, mock_summarize):
        mock_extract.return_value = "content"
        mock_summarize.return_value = "summary"

        files = [(b"data1", "f1.txt"), (b"data2", "f2.pdf"), (b"data3", "f3.docx")]
        result = SummarizerService.batch_process(files, summary_length="short", user_id="u1")

        assert len(result["results"]) == 3
        assert len(result["errors"]) == 0
        for r in result["results"]:
            assert r["summary"] == "summary"
            assert r["summary_length"] == "short"

    def test_batch_exceeds_10_file_limit(self):
        files = [(b"d", f"f{i}.txt") for i in range(11)]

        with pytest.raises(BatchLimitExceededError, match="10 files"):
            SummarizerService.batch_process(files)

    @patch("backend.app.summarizer.service.summarize")
    @patch("backend.app.summarizer.service.extract_text")
    def test_batch_partial_failure_isolates_errors(self, mock_extract, mock_summarize):
        """One file failing should not prevent other files from being processed."""
        mock_extract.side_effect = [
            "content1",
            ExtractionError("corrupt file"),
            "content3",
        ]
        mock_summarize.return_value = "summary"

        files = [(b"d1", "ok1.txt"), (b"d2", "bad.xyz"), (b"d3", "ok2.txt")]
        result = SummarizerService.batch_process(files, user_id="u1")

        assert len(result["results"]) == 2
        assert len(result["errors"]) == 1
        assert "corrupt file" in result["errors"][0]["error"]
        assert result["errors"][0]["filename"] == "bad.xyz"

    @patch("backend.app.summarizer.service.summarize")
    @patch("backend.app.summarizer.service.extract_text")
    def test_batch_all_fail(self, mock_extract, mock_summarize):
        mock_extract.side_effect = ExtractionError("bad")

        files = [(b"d", "f1.txt"), (b"d", "f2.txt")]
        result = SummarizerService.batch_process(files)

        assert len(result["results"]) == 0
        assert len(result["errors"]) == 2

    @patch("backend.app.summarizer.service.summarize")
    @patch("backend.app.summarizer.service.extract_text")
    def test_batch_stores_history_for_successes(self, mock_extract, mock_summarize):
        mock_extract.return_value = "text"
        mock_summarize.return_value = "sum"

        files = [(b"d", "f1.txt"), (b"d", "f2.txt")]
        SummarizerService.batch_process(files, user_id="batch_user")

        history = SummarizerService.get_history("batch_user")
        assert len(history) == 2


class TestServiceErrorHandling:
    """Feature: Logging & Error Handling
    Verifies the service returns user-friendly error messages for all
    failure modes, and that errors from the AI engine propagate correctly.
    """

    def setup_method(self):
        summary_history.clear()

    @patch("backend.app.summarizer.service.extract_text")
    def test_extraction_error_is_user_friendly(self, mock_extract):
        mock_extract.side_effect = ExtractionError("Could not read PDF: invalid header")

        with pytest.raises(ExtractionError) as exc_info:
            SummarizerService.process_and_summarize(
                file_bytes=b"bad", filename="bad.pdf"
            )
        assert "Failed to extract text" in exc_info.value.message
        assert exc_info.value.status_code == 422

    @patch("backend.app.summarizer.service.summarize")
    @patch("backend.app.summarizer.service.extract_text")
    def test_summarization_error_is_user_friendly(self, mock_extract, mock_summarize):
        mock_extract.return_value = "text"
        mock_summarize.side_effect = SummarizationError(
            "The AI service is temporarily overloaded. Please try again in a few moments."
        )

        with pytest.raises(SummarizationError) as exc_info:
            SummarizerService.process_and_summarize(content="text")
        assert "temporarily overloaded" in exc_info.value.message
        assert exc_info.value.status_code == 500

    @patch("backend.app.summarizer.service.summarize")
    @patch("backend.app.summarizer.service.extract_text")
    def test_connection_error_message(self, mock_extract, mock_summarize):
        mock_extract.return_value = "text"
        mock_summarize.side_effect = SummarizationError(
            "Unable to connect to the AI service. Please check your network and try again."
        )

        with pytest.raises(SummarizationError) as exc_info:
            SummarizerService.process_and_summarize(content="text")
        assert "Unable to connect" in exc_info.value.message

    @patch("backend.app.summarizer.service.summarize")
    @patch("backend.app.summarizer.service.extract_text")
    def test_timeout_error_message(self, mock_extract, mock_summarize):
        mock_extract.return_value = "text"
        mock_summarize.side_effect = SummarizationError(
            "The AI service took too long to respond. Please try again."
        )

        with pytest.raises(SummarizationError) as exc_info:
            SummarizerService.process_and_summarize(content="text")
        assert "too long to respond" in exc_info.value.message

    def test_file_too_large_error_message(self):
        with pytest.raises(FileTooLargeError) as exc_info:
            SummarizerService.process_and_summarize(
                file_bytes=b"x" * (10 * 1024 * 1024 + 1), filename="big.pdf"
            )
        assert "10MB limit" in exc_info.value.message
        assert exc_info.value.status_code == 413

    def test_batch_limit_error_message(self):
        with pytest.raises(BatchLimitExceededError) as exc_info:
            SummarizerService.batch_process([(b"d", f"f{i}.txt") for i in range(11)])
        assert "10 files" in exc_info.value.message
        assert exc_info.value.status_code == 400

    @patch("backend.app.summarizer.service.extract_text")
    def test_unsupported_format_error_message(self, mock_extract):
        mock_extract.side_effect = UnsupportedFormatError(".exe")

        with pytest.raises(UnsupportedFormatError) as exc_info:
            SummarizerService.process_and_summarize(
                file_bytes=b"data", filename="virus.exe"
            )
        assert "Unsupported file format: .exe" in exc_info.value.message
        assert exc_info.value.status_code == 400


class TestServiceHistoryIntegration:
    """Feature: Per-user History
    Verifies the service stores summaries per user and records
    are accessible after summarization.
    """

    def setup_method(self):
        summary_history.clear()

    @patch("backend.app.summarizer.service.summarize")
    @patch("backend.app.summarizer.service.extract_text")
    def test_summary_stored_in_history_after_processing(self, mock_extract, mock_summarize):
        mock_extract.return_value = "text"
        mock_summarize.return_value = "A nice summary"

        SummarizerService.process_and_summarize(
            content="text", summary_length="short", user_id="alice"
        )

        history = SummarizerService.get_history("alice")
        assert len(history) == 1
        assert history[0]["summary"] == "A nice summary"
        assert history[0]["summary_length"] == "short"

    @patch("backend.app.summarizer.service.summarize")
    @patch("backend.app.summarizer.service.extract_text")
    def test_multiple_summaries_accumulate(self, mock_extract, mock_summarize):
        mock_extract.return_value = "text"
        mock_summarize.side_effect = ["First", "Second", "Third"]

        for _ in range(3):
            SummarizerService.process_and_summarize(content="text", user_id="bob")

        assert len(SummarizerService.get_history("bob")) == 3

    @patch("backend.app.summarizer.service.summarize")
    @patch("backend.app.summarizer.service.extract_text")
    def test_users_have_separate_histories(self, mock_extract, mock_summarize):
        mock_extract.return_value = "text"
        mock_summarize.side_effect = ["Alice sum", "Bob sum"]

        SummarizerService.process_and_summarize(content="text", user_id="alice")
        SummarizerService.process_and_summarize(content="text", user_id="bob")

        assert len(SummarizerService.get_history("alice")) == 1
        assert len(SummarizerService.get_history("bob")) == 1
        assert SummarizerService.get_history("alice")[0]["summary"] == "Alice sum"
        assert SummarizerService.get_history("bob")[0]["summary"] == "Bob sum"

    @patch("backend.app.summarizer.service.summarize")
    @patch("backend.app.summarizer.service.extract_text")
    def test_record_contains_all_required_fields(self, mock_extract, mock_summarize):
        mock_extract.return_value = "text"
        mock_summarize.return_value = "sum"

        record = SummarizerService.process_and_summarize(
            content="text", summary_length="long", user_id="u1"
        )

        assert set(record.keys()) == {
            "id", "summary", "summary_length", "source_type", "timestamp"
        }
        assert record["summary_length"] == "long"
        assert record["source_type"] == "text"

    @patch("backend.app.summarizer.service.extract_text")
    def test_failed_summarization_does_not_store_history(self, mock_extract):
        mock_extract.side_effect = ExtractionError("bad input")

        with pytest.raises(ExtractionError):
            SummarizerService.process_and_summarize(content=None, user_id="u1")

        assert SummarizerService.get_history("u1") == []
