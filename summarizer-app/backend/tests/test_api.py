import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO


class TestSummarizeEndpoint:
    """Tests for POST /api/summarize"""

    def test_summarize_text_success(self, client, auth_headers):
        mock_record = {
            "id": "abc-123", "summary": "This is a summary.",
            "summary_length": "short", "source_type": "text",
            "timestamp": "2026-01-01T00:00:00",
        }
        with patch("backend.app.api.SummarizerService.process_and_summarize") as mock_svc:
            mock_svc.return_value = mock_record
            response = client.post(
                "/api/summarize",
                data={"text": "Some long text to summarize.", "summary_length": "short"},
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["summary"] == "This is a summary."
            assert data["summary_length"] == "short"
            assert data["source_type"] == "text"
            assert "id" in data
            assert "timestamp" in data
            mock_svc.assert_called_once()

    def test_summarize_url_success(self, client, auth_headers):
        mock_record = {
            "id": "abc-456", "summary": "URL summary.",
            "summary_length": "medium", "source_type": "url",
            "timestamp": "2026-01-01T00:00:00",
        }
        with patch("backend.app.api.SummarizerService.process_and_summarize") as mock_svc:
            mock_svc.return_value = mock_record
            response = client.post(
                "/api/summarize",
                data={"url": "https://example.com", "summary_length": "medium"},
                headers=auth_headers,
            )
            assert response.status_code == 200
            assert response.json()["source_type"] == "url"

    def test_summarize_file_upload(self, client, auth_headers):
        mock_record = {
            "id": "abc-789", "summary": "File summary.",
            "summary_length": "long", "source_type": "file",
            "timestamp": "2026-01-01T00:00:00",
        }
        with patch("backend.app.api.SummarizerService.process_and_summarize") as mock_svc:
            mock_svc.return_value = mock_record
            response = client.post(
                "/api/summarize",
                data={"summary_length": "long"},
                files={"file": ("test.txt", BytesIO(b"Hello world"), "text/plain")},
                headers=auth_headers,
            )
            assert response.status_code == 200
            assert response.json()["source_type"] == "file"

    def test_summarize_no_auth_returns_401(self, client):
        response = client.post(
            "/api/summarize",
            data={"text": "Some text"},
        )
        assert response.status_code in [401, 403]

    def test_summarize_file_too_large(self, client, auth_headers):
        from backend.app.errors import FileTooLargeError
        with patch("backend.app.api.SummarizerService.process_and_summarize") as mock_svc:
            mock_svc.side_effect = FileTooLargeError()
            large_content = b"x" * (10 * 1024 * 1024 + 1)
            response = client.post(
                "/api/summarize",
                data={"summary_length": "short"},
                files={"file": ("big.txt", BytesIO(large_content), "text/plain")},
                headers=auth_headers,
            )
            assert response.status_code == 413


class TestBatchEndpoint:
    """Tests for POST /api/batch"""

    def test_batch_success(self, client, auth_headers):
        mock_result = {
            "results": [
                {"id": "1", "summary": "s1", "summary_length": "short",
                 "source_type": "file", "timestamp": "t1"},
                {"id": "2", "summary": "s2", "summary_length": "short",
                 "source_type": "file", "timestamp": "t2"},
            ],
            "errors": [],
        }
        with patch("backend.app.api.SummarizerService.batch_process") as mock_svc:
            mock_svc.return_value = mock_result
            files = [
                ("files", ("f1.txt", BytesIO(b"text 1"), "text/plain")),
                ("files", ("f2.txt", BytesIO(b"text 2"), "text/plain")),
            ]
            response = client.post(
                "/api/batch",
                data={"summary_length": "short"},
                files=files,
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) == 2
            assert len(data["errors"]) == 0

    def test_batch_exceeds_limit(self, client, auth_headers):
        from backend.app.errors import BatchLimitExceededError
        with patch("backend.app.api.SummarizerService.batch_process") as mock_svc:
            mock_svc.side_effect = BatchLimitExceededError()
            files = [
                ("files", (f"f{i}.txt", BytesIO(b"text"), "text/plain"))
                for i in range(11)
            ]
            response = client.post(
                "/api/batch",
                data={"summary_length": "short"},
                files=files,
                headers=auth_headers,
            )
            assert response.status_code == 400

    def test_batch_no_auth(self, client):
        files = [("files", ("f1.txt", BytesIO(b"text"), "text/plain"))]
        response = client.post("/api/batch", files=files)
        assert response.status_code in [401, 403]


class TestHistoryEndpoint:
    """Tests for GET /api/history"""

    def test_get_history(self, client, auth_headers):
        response = client.get("/api/history", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_history_no_auth(self, client):
        response = client.get("/api/history")
        assert response.status_code in [401, 403]
