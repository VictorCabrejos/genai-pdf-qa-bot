import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
from pathlib import Path
import sys

# Add parent directory to path so we can import app
sys.path.append(str(Path(__file__).parent.parent))

from app.main import app


# Create a test client
client = TestClient(app)


@pytest.fixture
def mock_pdf_file():
    """Create a mock PDF file for testing"""
    # This is a simple fixture that returns a path to a test PDF
    # In a real test, you would have an actual PDF file for testing
    return os.path.join(os.path.dirname(__file__), "resources", "test.pdf")


# Mock the embedding service and other external dependencies
@pytest.fixture
def mock_services():
    """Mock the services that make external API calls"""
    with patch("app.routes.pdf_routes.embedding_service") as mock_embedding:
        with patch("app.routes.pdf_routes.retriever") as mock_retriever:
            with patch("app.routes.pdf_routes.llm_service") as mock_llm:
                # Configure the mocks
                mock_embedding.create_embeddings.return_value = [[0.1, 0.2, 0.3]]
                mock_retriever.add_document.return_value = "test-pdf-id"
                mock_retriever.search.return_value = [
                    {"text": "Test content", "page_number": 1, "score": 0.95}
                ]
                mock_llm.generate_answer.return_value = "This is a test answer."

                yield {
                    "embedding": mock_embedding,
                    "retriever": mock_retriever,
                    "llm": mock_llm
                }


# Tests would be expanded in a real implementation
def test_root_endpoint():
    """Test the root endpoint returns expected information"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "docs_url" in response.json()


# More tests would be added for actual endpoints
# For example:
"""
@pytest.mark.asyncio
async def test_upload_endpoint(mock_services, mock_pdf_file):
    # Create a test file
    with open(mock_pdf_file, "rb") as f:
        response = client.post(
            "/api/upload",
            files={"file": ("test.pdf", f, "application/pdf")}
        )

    assert response.status_code == 200
    assert "pdf_id" in response.json()
    assert response.json()["pdf_id"] == "test-pdf-id"


@pytest.mark.asyncio
async def test_ask_endpoint(mock_services):
    # Test the ask endpoint
    response = client.post(
        "/api/ask",
        json={"question": "What is in the document?", "pdf_id": "test-pdf-id"}
    )

    assert response.status_code == 200
    assert "answer" in response.json()
    assert response.json()["answer"] == "This is a test answer."
"""