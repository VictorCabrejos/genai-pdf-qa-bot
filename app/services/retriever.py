from typing import List, Dict, Any, Tuple
import numpy as np
import faiss
import uuid
import time
from .embedding import EmbeddingService


class Retriever:
    """Service for managing document chunks and retrieval using FAISS."""

    def __init__(self, embedding_service: EmbeddingService):
        """
        Initialize the retriever service.

        Args:
            embedding_service: Service for creating embeddings
        """
        self.embedding_service = embedding_service
        self.pdf_stores = {}  # Dictionary to store FAISS indices by PDF ID
        self.chunk_metadata = {}  # Stores metadata for chunks indexed in FAISS

    async def add_document(self, chunks: List[str], metadata: List[Dict[str, Any]]) -> str:
        """
        Add document chunks to a new FAISS index.

        Args:
            chunks: List of text chunks from the document
            metadata: List of metadata for each chunk (must match chunks length)

        Returns:
            pdf_id: Unique ID for the indexed document
        """
        if len(chunks) != len(metadata):
            raise ValueError("Chunks and metadata must have the same length")

        if not chunks:
            raise ValueError("No chunks provided")

        # Generate a unique ID for this PDF
        pdf_id = str(uuid.uuid4())

        # Create embeddings for all chunks
        embeddings = await self.embedding_service.create_embeddings(chunks)

        # Convert to numpy array with correct dimensions
        embeddings_np = np.array(embeddings).astype('float32')

        # Get embedding dimension
        dimension = len(embeddings[0])

        # Create FAISS index (using L2 distance)
        index = faiss.IndexFlatL2(dimension)

        # Add vectors to the index
        index.add(embeddings_np)

        # Store the index and metadata
        self.pdf_stores[pdf_id] = index
        self.chunk_metadata[pdf_id] = metadata

        return pdf_id

    async def search(
        self,
        query: str,
        pdf_id: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for the most similar chunks to the query.

        Args:
            query: Query text
            pdf_id: ID of the PDF to search
            top_k: Number of results to return

        Returns:
            List of dicts containing chunk text, metadata, and similarity score
        """
        if pdf_id not in self.pdf_stores:
            raise ValueError(f"PDF ID {pdf_id} not found")

        # Get the index and metadata for this PDF
        index = self.pdf_stores[pdf_id]
        metadata_list = self.chunk_metadata[pdf_id]

        # Create embedding for the query
        query_embedding = await self.embedding_service.create_single_embedding(query)
        query_np = np.array([query_embedding]).astype('float32')

        # Search the index
        start_time = time.time()
        distances, indices = index.search(query_np, min(top_k, len(metadata_list)))
        search_time = time.time() - start_time

        # Prepare results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < 0:  # FAISS may return -1 if not enough results
                continue

            # Convert L2 distance to similarity score (closer to 1 is better)
            # This is a simple conversion, could be refined
            similarity = 1 / (1 + distances[0][i])

            result = {
                **metadata_list[idx],  # Include all metadata
                "score": float(similarity)
            }
            results.append(result)

        return results