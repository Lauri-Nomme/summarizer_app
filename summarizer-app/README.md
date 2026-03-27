# GenAI Summarizer

A self-hosted Python application that summarizes text documents, web pages, and user input using Azure OpenAI.

## Features

- **Multi-format input**: Plain text, PDF, DOCX, and web URLs
- **Configurable summary length**: Short, medium, or long
- **REST API**: JWT-authenticated endpoints for integration
- **Web UI**: Responsive, accessible dashboard (Jinja2 templates)
- **Batch processing**: Up to 10 files per request (10MB max each)
- **History**: Per-user summary history tracking
- **Logging**: Structured logging with loguru

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env` and update with your Azure OpenAI credentials:

| Variable | Description |
|---|---|
| `AZURE_OPENAI_KEY` | Your Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Your Azure OpenAI endpoint URL |
| `AZURE_OPENAI_DEPLOYMENT` | Your model deployment name |
| `AZURE_OPENAI_API_VERSION` | API version (default: `2024-02-01`) |
| `JWT_SECRET` | Secret key for JWT authentication |
| `HOST` | Server host (default: `127.0.0.1`) |
| `PORT` | Server port (default: `8000`) |
| `LOG_LEVEL` | Logging level (default: `INFO`) |

### 4. Run the application

```bash
python run.py
```

The app will start at `http://127.0.0.1:8000`.

## Usage

### Web UI

- Navigate to `http://127.0.0.1:8000` in your browser
- Paste text, upload a file, or enter a URL
- Select summary length and click **Summarize**
- View history at `/history`

### REST API

All API endpoints require a JWT Bearer token in the `Authorization` header.

**Generate a JWT token** (for testing):

```python
from jose import jwt
token = jwt.encode({"sub": "your-user-id"}, "your-jwt-secret", algorithm="HS256")
```

**Summarize text:**

```bash
curl -X POST http://127.0.0.1:8000/api/summarize \
  -H "Authorization: Bearer <token>" \
  -F "text=Your text here" \
  -F "summary_length=short"
```

**Upload and summarize a file:**

```bash
curl -X POST http://127.0.0.1:8000/api/summarize \
  -H "Authorization: Bearer <token>" \
  -F "file=@document.pdf" \
  -F "summary_length=medium"
```

**Batch processing:**

```bash
curl -X POST http://127.0.0.1:8000/api/batch \
  -H "Authorization: Bearer <token>" \
  -F "files=@file1.pdf" \
  -F "files=@file2.docx" \
  -F "summary_length=short"
```

**Get summary history:**

```bash
curl http://127.0.0.1:8000/api/history \
  -H "Authorization: Bearer <token>"
```

## Running Tests

```bash
cd summarizer-app
pytest backend/tests/ -v --cov=backend --cov-report=term-missing
```

## Deployment

Use `startup.sh` for Linux/cloud deployments:

```bash
chmod +x startup.sh
./startup.sh
```

## Troubleshooting

| Issue | Solution |
|---|---|
| `SummarizationError: Azure OpenAI is not configured` | Set `AZURE_OPENAI_KEY` and `AZURE_OPENAI_ENDPOINT` environment variables |
| `AuthenticationError: Invalid or missing token` | Include a valid JWT Bearer token in the Authorization header |
| `FileTooLargeError` | File exceeds 10MB limit — reduce file size |
| `UnsupportedFormatError` | Only PDF, DOCX, and TXT files are supported |
| Import errors when running | Ensure you run from the `summarizer-app/` directory |
