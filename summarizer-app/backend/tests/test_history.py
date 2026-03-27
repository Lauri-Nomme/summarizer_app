import pytest
from unittest.mock import patch
from backend.app.summarizer.service import SummarizerService, summary_history


class TestHistoryTracking:
    """Tests for summary history storage and retrieval."""

    def setup_method(self):
        summary_history.clear()

    def test_store_summary_creates_record(self):
        record = SummarizerService.store_summary("user1", "Test summary", "short", "text")
        assert record["summary"] == "Test summary"
        assert record["summary_length"] == "short"
        assert record["source_type"] == "text"
        assert "id" in record
        assert "timestamp" in record

    def test_store_multiple_summaries(self):
        SummarizerService.store_summary("user1", "Summary 1", "short", "text")
        SummarizerService.store_summary("user1", "Summary 2", "medium", "file")
        assert len(summary_history["user1"]) == 2

    def test_separate_user_histories(self):
        SummarizerService.store_summary("user1", "Summary A", "short", "text")
        SummarizerService.store_summary("user2", "Summary B", "long", "url")
        assert len(summary_history["user1"]) == 1
        assert len(summary_history["user2"]) == 1
        assert summary_history["user1"][0]["summary"] == "Summary A"
        assert summary_history["user2"][0]["summary"] == "Summary B"

    def test_get_history_returns_user_data(self):
        SummarizerService.store_summary("user1", "Sum", "short", "text")
        history = SummarizerService.get_history("user1")
        assert len(history) == 1
        assert history[0]["summary"] == "Sum"

    def test_get_history_empty_for_new_user(self):
        assert SummarizerService.get_history("nonexistent") == []

    def test_history_endpoint_returns_user_data(self, client, auth_headers):
        mock_record = {
            "id": "abc", "summary": "API summary",
            "summary_length": "short", "source_type": "text",
            "timestamp": "2026-01-01T00:00:00",
        }
        with patch("backend.app.api.SummarizerService.process_and_summarize") as mock_svc:
            mock_svc.return_value = mock_record
            client.post(
                "/api/summarize",
                data={"text": "Some text", "summary_length": "short"},
                headers=auth_headers,
            )
        response = client.get("/api/history", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_history_empty_for_new_user_via_api(self, client, auth_headers):
        summary_history.clear()
        response = client.get("/api/history", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_store_summary_fields(self):
        record = SummarizerService.store_summary("u1", "sum", "long", "url")
        assert set(record.keys()) == {"id", "summary", "summary_length", "source_type", "timestamp"}
