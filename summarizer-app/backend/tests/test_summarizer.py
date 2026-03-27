import pytest
from unittest.mock import patch, MagicMock
from backend.app.summarizer.utils import (
    extract_text,
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_url,
)
from backend.app.summarizer.engine import summarize, SUMMARY_PROMPTS
from backend.app.errors import (
    ExtractionError,
    UnsupportedFormatError,
    SummarizationError,
)


class TestExtractText:
    """Tests for text extraction from various formats."""

    def test_extract_plain_text(self):
        result = extract_text(content="  Hello world  ")
        assert result == "Hello world"

    def test_extract_text_from_txt_file(self):
        result = extract_text(file_bytes=b"File content here", filename="doc.txt")
        assert result == "File content here"

    def test_extract_no_input_raises_error(self):
        with pytest.raises(ExtractionError, match="No input provided"):
            extract_text()

    def test_extract_unsupported_format(self):
        with pytest.raises(UnsupportedFormatError, match="Unsupported file format"):
            extract_text(file_bytes=b"data", filename="file.xyz")

    def test_extract_pdf(self):
        with patch("backend.app.summarizer.utils.PdfReader") as mock_reader:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "PDF text content"
            mock_reader.return_value.pages = [mock_page]
            result = extract_text_from_pdf(b"fake-pdf-bytes")
            assert result == "PDF text content"

    def test_extract_pdf_empty(self):
        with patch("backend.app.summarizer.utils.PdfReader") as mock_reader:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = ""
            mock_reader.return_value.pages = [mock_page]
            with pytest.raises(ExtractionError, match="no extractable text"):
                extract_text_from_pdf(b"fake-pdf-bytes")

    def test_extract_pdf_corrupt(self):
        with patch("backend.app.summarizer.utils.PdfReader") as mock_reader:
            mock_reader.side_effect = Exception("corrupt file")
            with pytest.raises(ExtractionError, match="Could not read PDF"):
                extract_text_from_pdf(b"bad-bytes")

    def test_extract_docx(self):
        with patch("backend.app.summarizer.utils.Document") as mock_doc:
            mock_para = MagicMock()
            mock_para.text = "Paragraph text"
            mock_doc.return_value.paragraphs = [mock_para]
            result = extract_text_from_docx(b"fake-docx-bytes")
            assert result == "Paragraph text"

    def test_extract_docx_empty(self):
        with patch("backend.app.summarizer.utils.Document") as mock_doc:
            mock_para = MagicMock()
            mock_para.text = ""
            mock_doc.return_value.paragraphs = [mock_para]
            with pytest.raises(ExtractionError, match="no extractable text"):
                extract_text_from_docx(b"fake-docx-bytes")

    def test_extract_url(self):
        with patch("backend.app.summarizer.utils.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.text = "<html><body><p>Web content</p></body></html>"
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            result = extract_text_from_url("https://example.com")
            assert "Web content" in result

    def test_extract_url_failure(self):
        with patch("backend.app.summarizer.utils.requests.get") as mock_get:
            import requests
            mock_get.side_effect = requests.RequestException("Connection error")
            with pytest.raises(ExtractionError, match="Could not fetch URL"):
                extract_text_from_url("https://bad-url.com")

    def test_extract_text_via_file_pdf(self):
        with patch("backend.app.summarizer.utils.extract_text_from_pdf") as mock_pdf:
            mock_pdf.return_value = "PDF content"
            result = extract_text(file_bytes=b"data", filename="report.pdf")
            assert result == "PDF content"

    def test_extract_text_via_file_docx(self):
        with patch("backend.app.summarizer.utils.extract_text_from_docx") as mock_docx:
            mock_docx.return_value = "DOCX content"
            result = extract_text(file_bytes=b"data", filename="report.docx")
            assert result == "DOCX content"

    def test_extract_text_via_url(self):
        with patch("backend.app.summarizer.utils.extract_text_from_url") as mock_url:
            mock_url.return_value = "URL content"
            result = extract_text(url="https://example.com")
            assert result == "URL content"


class TestSummarize:
    """Tests for the summarization engine."""

    def test_invalid_length(self):
        with pytest.raises(SummarizationError, match="Invalid summary length"):
            summarize("text", length="tiny")

    def test_missing_config(self):
        with patch("backend.app.summarizer.engine.settings") as mock_settings:
            mock_settings.AZURE_OPENAI_KEY = ""
            mock_settings.AZURE_OPENAI_ENDPOINT = ""
            mock_settings.AZURE_OPENAI_DEPLOYMENT = ""
            mock_settings.azure_openai_configured = False
            mock_settings.MAX_INPUT_CHARS = 50000
            with pytest.raises(SummarizationError, match="not configured"):
                summarize("text", length="short")

    def test_successful_summarization(self):
        with patch("backend.app.summarizer.engine.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = "  Generated summary  "
            mock_client.chat.completions.create.return_value.choices = [mock_choice]
            mock_get_client.return_value = mock_client

            result = summarize("Long text here", length="medium")
            assert result == "Generated summary"

    def test_api_error(self):
        with patch("backend.app.summarizer.engine.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = RuntimeError("API down")
            mock_get_client.return_value = mock_client

            with pytest.raises(SummarizationError, match="Azure OpenAI error"):
                summarize("text", length="short")

    def test_summary_prompts_exist(self):
        assert "short" in SUMMARY_PROMPTS
        assert "medium" in SUMMARY_PROMPTS
        assert "long" in SUMMARY_PROMPTS
