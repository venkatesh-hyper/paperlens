"""
PaperLens API Test Suite — matches actual main.py
Run: pytest tests/test_api.py -v
"""

import pytest
import numpy as np
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.api.main import app

client = TestClient(app)


# ── MOCK DATA ─────────────────────────────────────────────────────────────────

MOCK_PAPER = {
    "id":       "test_paper_001",
    "title":    "Attention Is All You Need",
    "abstract": "We propose the Transformer, based solely on attention mechanisms.",
    "authors":  "Vaswani, Shazeer, Parmar",
    "year":     2017,
    "field":    "cs.AI",
    "url":      "https://arxiv.org/abs/1706.03762",
}


# ── /health ───────────────────────────────────────────────────────────────────

class TestHealth:

    def test_health_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_has_status_field(self):
        assert "status" in client.get("/health").json()

    def test_health_status_is_string(self):
        assert isinstance(client.get("/health").json()["status"], str)

    def test_health_has_paper_indexed(self):
        # field is paper_indexed (not papers_indexed)
        assert "paper_indexed" in client.get("/health").json()

    def test_health_paper_indexed_is_non_negative_int(self):
        val = client.get("/health").json()["paper_indexed"]
        assert isinstance(val, int) and val >= 0

    def test_health_has_index_loading(self):
        assert "index_loading" in client.get("/health").json()

    def test_health_has_embedding_loading(self):
        assert "embedding_loading" in client.get("/health").json()


# ── /search ───────────────────────────────────────────────────────────────────

class TestSearch:

    def _make_mock_state(self):
        mock_index = MagicMock()
        mock_index.search.return_value = (
            np.array([[0.92]], dtype="float32"),
            np.array([[0]],    dtype="int64"),
        )
        return {
            "index":    mock_index,
            "id_map":   {"0": "test_paper_001"},
            "model":    MagicMock(),
            "db_conn":  MagicMock(),
            "n_papers": 956,
        }

    def test_search_missing_query_returns_422(self):
        assert client.get("/search").status_code == 422

    def test_search_top_k_too_large_returns_422(self):
        assert client.get("/search?query=test&top_k=999").status_code == 422

    def test_search_top_k_zero_returns_422(self):
        assert client.get("/search?query=test&top_k=0").status_code == 422

    @patch("src.api.main.get_cached_response", return_value=None)
    @patch("src.api.main.set_cache")
    @patch("src.api.main.embed_query")
    @patch("src.api.main.get_paper_by_id")
    def test_search_returns_200(self, mock_paper, mock_embed, *_):
        mock_embed.return_value = np.zeros((1, 384), dtype="float32")
        mock_paper.return_value = MOCK_PAPER
        mock_state = self._make_mock_state()
        with patch("src.api.main.state", mock_state):
            response = client.get("/search?query=transformer")
        assert response.status_code == 200

    @patch("src.api.main.get_cached_response", return_value=None)
    @patch("src.api.main.set_cache")
    @patch("src.api.main.embed_query")
    @patch("src.api.main.get_paper_by_id")
    def test_search_response_has_results_field(self, mock_paper, mock_embed, *_):
        mock_embed.return_value = np.zeros((1, 384), dtype="float32")
        mock_paper.return_value = MOCK_PAPER
        with patch("src.api.main.state", self._make_mock_state()):
            data = client.get("/search?query=transformer").json()
        assert "results" in data
        assert isinstance(data["results"], list)

    @patch("src.api.main.get_cached_response", return_value=None)
    @patch("src.api.main.set_cache")
    @patch("src.api.main.embed_query")
    @patch("src.api.main.get_paper_by_id")
    def test_search_has_latency_ms(self, mock_paper, mock_embed, *_):
        mock_embed.return_value = np.zeros((1, 384), dtype="float32")
        mock_paper.return_value = MOCK_PAPER
        with patch("src.api.main.state", self._make_mock_state()):
            data = client.get("/search?query=transformer").json()
        assert "latency_ms" in data

    @patch("src.api.main.get_cached_response", return_value=None)
    @patch("src.api.main.set_cache")
    @patch("src.api.main.embed_query")
    @patch("src.api.main.get_paper_by_id")
    def test_search_result_fields(self, mock_paper, mock_embed, *_):
        mock_embed.return_value = np.zeros((1, 384), dtype="float32")
        mock_paper.return_value = MOCK_PAPER
        with patch("src.api.main.state", self._make_mock_state()):
            data = client.get("/search?query=transformer").json()
        if data["results"]:
            r = data["results"][0]
            assert "title"    in r
            assert "abstract" in r
            assert "score"    in r

    def test_search_empty_query_returns_400(self):
        with patch("src.api.main.get_cached_response", return_value=None):
            assert client.get("/search?query=   ").status_code == 400


# ── /papers/{id} ─────────────────────────────────────────────────────────────

class TestGetPaper:

    @patch("src.api.main.get_paper_by_id")
    def test_get_paper_returns_200(self, mock_get):
        mock_get.return_value = MOCK_PAPER
        assert client.get("/papers/test_paper_001").status_code == 200

    @patch("src.api.main.get_paper_by_id")
    def test_get_paper_has_required_fields(self, mock_get):
        mock_get.return_value = MOCK_PAPER
        data = client.get("/papers/test_paper_001").json()
        assert "id"       in data
        assert "title"    in data
        assert "abstract" in data

    @patch("src.api.main.get_paper_by_id")
    def test_get_paper_not_found_returns_404(self, mock_get):
        mock_get.return_value = None
        assert client.get("/papers/does_not_exist").status_code == 404

    @patch("src.api.main.get_paper_by_id")
    def test_get_paper_title_is_string(self, mock_get):
        mock_get.return_value = MOCK_PAPER
        title = client.get("/papers/test_paper_001").json()["title"]
        assert isinstance(title, str) and len(title) > 0

    @patch("src.api.main.get_paper_by_id")
    def test_get_paper_id_matches(self, mock_get):
        mock_get.return_value = MOCK_PAPER
        assert client.get("/papers/test_paper_001").json()["id"] == "test_paper_001"


# ── /summarize/{id} ──────────────────────────────────────────────────────────

class TestSummarize:

    @patch("src.api.main.get_paper_by_id")
    @patch("src.api.main.summarize_paper")
    def test_summarize_returns_200(self, mock_sum, mock_get):
        mock_get.return_value = MOCK_PAPER
        mock_sum.return_value = "**What it does:** Introduces Transformer."
        assert client.get("/summarize/test_paper_001").status_code == 200

    @patch("src.api.main.get_paper_by_id")
    @patch("src.api.main.summarize_paper")
    def test_summarize_has_summary_field(self, mock_sum, mock_get):
        mock_get.return_value = MOCK_PAPER
        mock_sum.return_value = "Some summary text"
        assert "summary" in client.get("/summarize/test_paper_001").json()

    @patch("src.api.main.get_paper_by_id")
    @patch("src.api.main.summarize_paper")
    def test_summarize_has_title_field(self, mock_sum, mock_get):
        mock_get.return_value = MOCK_PAPER
        mock_sum.return_value = "Some summary text"
        assert "title" in client.get("/summarize/test_paper_001").json()

    @patch("src.api.main.get_paper_by_id")
    @patch("src.api.main.summarize_paper")
    def test_summarize_has_paper_id_field(self, mock_sum, mock_get):
        mock_get.return_value = MOCK_PAPER
        mock_sum.return_value = "Some summary text"
        assert "paper_id" in client.get("/summarize/test_paper_001").json()

    @patch("src.api.main.get_paper_by_id")
    def test_summarize_not_found_returns_404(self, mock_get):
        mock_get.return_value = None
        assert client.get("/summarize/does_not_exist").status_code == 404

    @patch("src.api.main.get_paper_by_id")
    @patch("src.api.main.summarize_paper")
    def test_summarize_summary_is_non_empty_string(self, mock_sum, mock_get):
        mock_get.return_value = MOCK_PAPER
        mock_sum.return_value = "Some summary text"
        summary = client.get("/summarize/test_paper_001").json()["summary"]
        assert isinstance(summary, str) and len(summary) > 0


# ── MISC ──────────────────────────────────────────────────────────────────────

class TestMisc:

    def test_invalid_route_returns_404(self):
        assert client.get("/nonexistent_route").status_code == 404