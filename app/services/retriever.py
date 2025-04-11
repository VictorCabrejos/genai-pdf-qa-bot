from typing import List, Dict, Any, Tuple
import numpy as np
import faiss
import uuid
import time
import json
import os
from pathlib import Path
import logging
import traceback
from .embedding import EmbeddingService

# Configure logging
logger = logging.getLogger("retriever")
logger.setLevel(logging.DEBUG)

# Add file handler if not already added
if not logger.handlers:
    file_handler = logging.FileHandler("retriever.log")
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)


class Retriever:
    """Service for managing document chunks and retrieval using FAISS."""

    def __init__(self, embedding_service=None):
        """
        Initialize the retriever service.

        Args:
            embedding_service: Service for creating embeddings
        """
        self.embedding_service = embedding_service or EmbeddingService()
        logger.info("Retriever service initialized")

        # Get the path to the pdf database directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
        self.pdfs_dir = os.path.join(self.root_dir, "db", "pdfs")
        logger.info(f"PDF directory set to: {self.pdfs_dir}")

    def get_chunks_by_id(self, pdf_id: str) -> List[Dict]:
        """
        Get all chunks for a specific PDF by ID.

        Args:
            pdf_id: The unique ID of the PDF

        Returns:
            List of chunk dictionaries with content and metadata
        """
        logger.info(f"Getting all chunks for PDF ID: {pdf_id}")
        try:
            # Construct the path to the chunks file
            pdf_dir = os.path.join(self.pdfs_dir, pdf_id)
            chunks_file = os.path.join(pdf_dir, "chunks.json")

            logger.debug(f"Looking for chunks file at: {chunks_file}")

            # Check if the directory and file exist
            if not os.path.exists(pdf_dir):
                logger.error(f"PDF directory not found: {pdf_dir}")
                return []

            if not os.path.exists(chunks_file):
                logger.error(f"Chunks file not found: {chunks_file}")
                return []

            # Load the chunks from the file
            with open(chunks_file, 'r', encoding='utf-8') as f:
                chunks_data = json.load(f)

            if not chunks_data or not isinstance(chunks_data, list):
                logger.warning(f"Chunks file empty or invalid format: {chunks_file}")
                return []

            logger.info(f"Successfully loaded {len(chunks_data)} chunks for PDF ID: {pdf_id}")

            # Log a sample chunk for debugging
            if chunks_data:
                sample_chunk = chunks_data[0]
                keys = list(sample_chunk.keys())
                logger.debug(f"Sample chunk keys: {keys}")
                logger.debug(f"Sample chunk preview: {json.dumps(sample_chunk, default=str)[:200]}...")

            return chunks_data

        except Exception as e:
            logger.error(f"Error getting chunks for PDF ID {pdf_id}: {str(e)}")
            logger.error(traceback.format_exc())
            return []

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
        logger.info(f"Creating new document with ID: {pdf_id}")

        # Create embeddings for all chunks
        embeddings = await self.embedding_service.create_embeddings(chunks)

        # Create directory for this PDF if it doesn't exist
        pdf_dir = os.path.join(self.pdfs_dir, pdf_id)
        os.makedirs(pdf_dir, exist_ok=True)
        logger.info(f"Created directory for PDF: {pdf_dir}")

        # Combine chunk text with metadata and embeddings
        chunks_with_data = []
        for i, (chunk_text, chunk_metadata) in enumerate(zip(chunks, metadata)):
            chunk_data = {**chunk_metadata, "text": chunk_text, "embedding": embeddings[i]}
            chunks_with_data.append(chunk_data)

        # Save chunks with embeddings to a file
        chunks_file = os.path.join(pdf_dir, "chunks.json")
        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_with_data, f, ensure_ascii=False, default=str)

        logger.info(f"Saved {len(chunks_with_data)} chunks with embeddings to {chunks_file}")

        # Create PDF info file
        info = {
            "pdf_id": pdf_id,
            "chunk_count": len(chunks),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        info_file = os.path.join(pdf_dir, "pdf_info.json")
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(info, f)

        logger.info(f"Saved PDF info to {info_file}")

        return pdf_id

    async def search(self, query: str, pdf_id: str, top_k: int = 10) -> List[Dict]:
        """
        Search for relevant document chunks using semantic search.

        Args:
            query: The search query
            pdf_id: ID of the PDF to search within
            top_k: Number of chunks to return

        Returns:
            List of relevant document chunks
        """
        logger.info(f"Searching for query: '{query}' in PDF ID: {pdf_id}")
        try:
            # Get all chunks for the PDF
            chunks = self.get_chunks_by_id(pdf_id)

            if not chunks:
                logger.warning(f"No chunks found for PDF ID: {pdf_id}")
                return []

            logger.info(f"Found {len(chunks)} chunks for PDF ID: {pdf_id}")

            # Check if chunks have embeddings
            if "embedding" not in chunks[0]:
                logger.warning("Chunks don't have embeddings, attempting to retrieve content only")
                # Return chunks without ranking if no embeddings
                return chunks[:top_k]

            # Extract embeddings from chunks
            chunk_embeddings = np.array([chunk["embedding"] for chunk in chunks], dtype=np.float32)

            # Create a query embedding
            query_embedding = await self.embedding_service.create_single_embedding(query)
            query_embedding = np.array(query_embedding, dtype=np.float32).reshape(1, -1)

            # Set up a FAISS index for efficient similarity search
            dimension = query_embedding.shape[1]
            index = faiss.IndexFlatL2(dimension)
            index.add(chunk_embeddings)

            # Search for similar chunks
            distances, indices = index.search(query_embedding, top_k)

            # Get the relevant chunks
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(chunks):
                    chunk = chunks[idx]
                    chunk["score"] = float(1.0 / (1.0 + distances[0][i]))
                    results.append(chunk)

            logger.info(f"Returning {len(results)} relevant chunks")
            return results

        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            logger.error(traceback.format_exc())
            return []

# Function to get an instance of the Retriever class
def get_pdf_retriever(embedding_service: EmbeddingService) -> Retriever:
    """
    Returns an instance of the Retriever class.

    Args:
        embedding_service: Service for creating embeddings

    Returns:
        An initialized Retriever object
    """
    return Retriever(embedding_service)