import os
from typing import List, Dict, Any
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class EmbeddingService:
    """Service for creating embeddings using OpenAI's API."""

    def __init__(self, model: str = "text-embedding-3-small"):
        """
        Initialize the embedding service.

        Args:
            model: The OpenAI embedding model to use
        """
        self.model = model
        if not client.api_key:
            raise ValueError("OpenAI API key is not set")

    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for the provided texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        try:
            # Handle empty list
            if not texts:
                return []

            # OpenAI recommends replacing newlines with spaces for best results
            texts = [text.replace("\n", " ") for text in texts]

            response = client.embeddings.create(
                input=texts,
                model=self.model,
                encoding_format="float"
            )

            # Extract embeddings from response
            embeddings = [item.embedding for item in response.data]
            return embeddings

        except Exception as e:
            print(f"Error creating embeddings: {e}")
            raise

    async def create_single_embedding(self, text: str) -> List[float]:
        """
        Create an embedding for a single text string.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        embeddings = await self.create_embeddings([text])
        return embeddings[0] if embeddings else []