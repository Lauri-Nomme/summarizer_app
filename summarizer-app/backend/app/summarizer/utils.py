import io
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from docx import Document
from ..errors import ExtractionError, UnsupportedFormatError
from ..logger import get_logger

logger = get_logger()

SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx"}


def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        if not text.strip():
            raise ExtractionError("PDF appears to contain no extractable text.")
        return text.strip()
    except ExtractionError:
        raise
    except Exception as e:
        raise ExtractionError(f"Could not read PDF: {str(e)}")


def extract_text_from_docx(file_bytes: bytes) -> str:
    try:
        doc = Document(io.BytesIO(file_bytes))
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        if not text.strip():
            raise ExtractionError("DOCX appears to contain no extractable text.")
        return text.strip()
    except ExtractionError:
        raise
    except Exception as e:
        raise ExtractionError(f"Could not read DOCX: {str(e)}")


def extract_text_from_url(url: str) -> str:
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        if not text.strip():
            raise ExtractionError("Web page appears to contain no extractable text.")
        return text.strip()
    except ExtractionError:
        raise
    except requests.RequestException as e:
        raise ExtractionError(f"Could not fetch URL: {str(e)}")


def extract_text(
    content: str = None,
    file_bytes: bytes = None,
    filename: str = None,
    url: str = None,
) -> str:
    if url:
        return extract_text_from_url(url)
    if file_bytes and filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext == ".pdf":
            return extract_text_from_pdf(file_bytes)
        elif ext == ".docx":
            return extract_text_from_docx(file_bytes)
        elif ext == ".txt":
            return file_bytes.decode("utf-8", errors="replace").strip()
        else:
            raise UnsupportedFormatError(ext or "unknown")
    if content:
        return content.strip()
    raise ExtractionError("No input provided. Please provide text, a file, or a URL.")
