from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Optional, List, Dict, Any
import time
import fitz  # PyMuPDF
import io
import os
from ..services.embedding import EmbeddingService
from ..services.retriever import Retriever
from ..services.llm import LLMService
from models.pydantic_schemas import QuestionRequest, AnswerResponse, PDFUploadResponse, ChunkInfo

router = APIRouter()

# Initialize services
embedding_service = EmbeddingService()
retriever = Retriever(embedding_service)
llm_service = LLMService()


def extract_text_from_pdf(pdf_file: bytes) -> List[str]:
    """
    Extract text from a PDF file by page.

    Args:
        pdf_file: PDF file bytes

    Returns:
        List of text strings, one per page
    """
    try:
        doc = fitz.open(stream=pdf_file, filetype="pdf")
        pages = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            pages.append(text)

        return pages
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


def chunk_text(pages: List[str], chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
    """
    Chunk text from PDF pages with specified size and overlap.

    Args:
        pages: List of page texts
        chunk_size: Maximum characters per chunk
        overlap: Overlap between consecutive chunks in characters

    Returns:
        List of dictionaries with chunk text and metadata
    """
    chunks = []

    for page_num, page_text in enumerate(pages):
        if not page_text.strip():  # Skip empty pages
            continue

        # Process each page
        start = 0
        while start < len(page_text):
            # Extract chunk with specified size
            end = min(start + chunk_size, len(page_text))

            # Don't create tiny chunks at the end
            if end - start < chunk_size // 3 and len(chunks) > 0:
                # Add this small chunk to the previous chunk if on same page
                if chunks[-1]["page_number"] == page_num + 1:
                    chunks[-1]["text"] += " " + page_text[start:end].strip()
                break

            chunk_text = page_text[start:end].strip()

            if chunk_text:  # Skip empty chunks
                chunk = {
                    "text": chunk_text,
                    "page_number": page_num + 1
                }
                chunks.append(chunk)

            # Move start position for next chunk, accounting for overlap
            start = end - overlap
            if start < 0:
                start = 0

    return chunks


@router.post("/upload", response_model=PDFUploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file, extract and chunk text, create embeddings.
    """
    start_time = time.time()

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    # Read the PDF file
    content = await file.read()

    try:
        # Extract text from the PDF by page
        pages = extract_text_from_pdf(content)

        # Chunk the text
        chunks_with_metadata = chunk_text(pages)

        if not chunks_with_metadata:
            raise HTTPException(status_code=400, detail="No text could be extracted from the PDF")

        # Get just the text for embedding
        chunk_texts = [chunk["text"] for chunk in chunks_with_metadata]

        # Add document to retriever
        pdf_id = await retriever.add_document(chunk_texts, chunks_with_metadata)

        processing_time = time.time() - start_time

        return PDFUploadResponse(
            pdf_id=pdf_id,
            filename=file.filename,
            num_pages=len(pages),
            num_chunks=len(chunks_with_metadata),
            processing_time=processing_time
        )

    except Exception as e:
        print(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@router.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """
    Answer a question about a previously uploaded PDF.
    """
    start_time = time.time()

    try:
        # Find relevant chunks
        context_chunks = await retriever.search(request.question, request.pdf_id, top_k=5)

        if not context_chunks:
            raise HTTPException(status_code=404, detail="No relevant content found or PDF ID not found")

        # Generate answer using LLM
        answer = await llm_service.generate_answer(request.question, context_chunks)

        # Format response with source chunks
        source_chunks = [
            ChunkInfo(
                text=chunk["text"],
                page_number=chunk["page_number"],
                score=chunk["score"]
            )
            for chunk in context_chunks
        ]

        processing_time = time.time() - start_time

        return AnswerResponse(
            answer=answer,
            source_chunks=source_chunks,
            processing_time=processing_time
        )

    except Exception as e:
        print(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}")