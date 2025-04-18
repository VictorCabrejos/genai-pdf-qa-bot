from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form, Query, Path
from fastapi.responses import JSONResponse, FileResponse
from fastapi.encoders import jsonable_encoder
from typing import Optional, List, Dict, Any
import time
import fitz  # PyMuPDF
import io
import os
import uuid
from datetime import datetime
from pathlib import Path as PathLib
from sqlalchemy.orm import Session
from ..services.embedding import EmbeddingService
from ..services.retriever import Retriever
from ..services.llm import LLMService
from ..auth.utils import get_current_user, get_user_pdf_path, get_user_pdfs, add_conversation_to_pdf
from ..database import get_db, PDF, PDFChunk, Quiz
from models.pydantic_schemas import QuestionRequest, AnswerResponse, PDFUploadResponse, ChunkInfo, PDFInfo, QuizRequest, QuizResponse, QuizSubmission, QuizResult

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
async def upload_pdf(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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

        # Save the PDF to user's storage
        user_id = current_user["user_id"]
        user_pdf_dir = get_user_pdf_path(user_id)
        pdf_path = user_pdf_dir / f"{pdf_id}.pdf"

        # Write PDF file to disk
        with open(pdf_path, "wb") as f:
            # Reset file position to beginning
            await file.seek(0)
            # Write the content
            f.write(content)

        # Create PDF record in database
        new_pdf = PDF(
            id=pdf_id,
            user_id=user_id,
            title=file.filename,
            filename=file.filename,
            file_path=str(pdf_path)
        )
        db.add(new_pdf)

        # Add chunks to database
        for i, chunk in enumerate(chunks_with_metadata):
            pdf_chunk = PDFChunk(
                pdf_id=pdf_id,
                content=chunk["text"],
                page_number=chunk["page_number"]
            )
            db.add(pdf_chunk)

        db.commit()

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
async def ask_question(
    request: QuestionRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Answer a question about a previously uploaded PDF.
    """
    start_time = time.time()

    try:
        # Check if the PDF belongs to the user
        user_id = current_user["user_id"]

        # Check if PDF exists and belongs to user
        pdf = db.query(PDF).filter(PDF.id == request.pdf_id, PDF.user_id == user_id).first()
        if not pdf:
            raise HTTPException(status_code=404, detail="PDF not found in your library")

        # Find relevant chunks
        context_chunks = await retriever.search(request.question, request.pdf_id, top_k=5)

        if not context_chunks:
            raise HTTPException(status_code=404, detail="No relevant content found")

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

        # Save this Q&A to conversation history using database
        add_conversation_to_pdf(
            user_id,
            request.pdf_id,
            request.question,
            answer,
            [chunk.dict() for chunk in source_chunks],
            db
        )

        return AnswerResponse(
            answer=answer,
            source_chunks=source_chunks,
            processing_time=processing_time
        )

    except Exception as e:
        print(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}")


@router.get("/library")
async def get_user_library(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get a list of all PDFs in the user's library.
    """
    user_id = current_user["user_id"]
    return get_user_pdfs(user_id, db)


@router.get("/pdf/{pdf_id}")
async def get_pdf_file(
    pdf_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the PDF file for viewing/download.
    """
    user_id = current_user["user_id"]

    # Check if PDF exists and belongs to user
    pdf = db.query(PDF).filter(PDF.id == pdf_id, PDF.user_id == user_id).first()
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found in your library")

    pdf_path = PathLib(pdf.file_path)

    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found on server")

    return FileResponse(
        path=pdf_path,
        filename=pdf.filename,
        media_type="application/pdf"
    )


@router.get("/pdf/{pdf_id}/history")
async def get_conversation_history(
    pdf_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the conversation history for a specific PDF.
    """
    user_id = current_user["user_id"]

    # Check if PDF exists and belongs to user
    pdf = db.query(PDF).filter(PDF.id == pdf_id, PDF.user_id == user_id).first()
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found in your library")

    # Get conversations for this PDF
    pdf_info = get_user_pdfs(user_id, db)
    if pdf_id in pdf_info:
        return pdf_info[pdf_id].conversation_history

    return []


@router.delete("/pdf/{pdf_id}")
async def delete_pdf(
    pdf_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a PDF from the user's library.
    """
    user_id = current_user["user_id"]

    # Check if PDF exists and belongs to user
    pdf = db.query(PDF).filter(PDF.id == pdf_id, PDF.user_id == user_id).first()
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found in your library")

    # Delete the PDF file if it exists
    pdf_path = PathLib(pdf.file_path)
    if pdf_path.exists():
        os.remove(pdf_path)

    # Delete PDF chunks from database
    db.query(PDFChunk).filter(PDFChunk.pdf_id == pdf_id).delete()

    # Delete the PDF from database
    db.delete(pdf)
    db.commit()

    return {"status": "success", "message": "PDF deleted successfully"}


@router.get("/pdf/{pdf_id}/preview/{page_num}")
async def get_page_preview(
    pdf_id: str,
    page_num: int = Path(..., ge=1),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    width: int = Query(800, description="Width of the preview image")
):
    """
    Generate a preview image for a specific page of a PDF.
    """
    user_id = current_user["user_id"]

    # Check if PDF exists and belongs to user
    pdf = db.query(PDF).filter(PDF.id == pdf_id, PDF.user_id == user_id).first()
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found in your library")

    pdf_path = PathLib(pdf.file_path)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found on server")

    try:
        # Open the PDF
        doc = fitz.open(pdf_path)

        # Check if page number is valid
        if page_num < 1 or page_num > len(doc):
            raise HTTPException(status_code=400, detail=f"Page number out of range. PDF has {len(doc)} pages.")

        # Get the page (0-indexed in PyMuPDF)
        page = doc.load_page(page_num - 1)

        # Render page to a pixmap
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

        # Create an image from the pixmap
        img_data = pix.tobytes("png")

        # Create temp file path for image
        preview_dir = get_user_pdf_path(user_id) / "previews"
        preview_dir.mkdir(exist_ok=True)
        preview_path = preview_dir / f"{pdf_id}_page_{page_num}.png"

        # Write the image to disk
        with open(preview_path, "wb") as f:
            f.write(img_data)

        return FileResponse(
            path=preview_path,
            media_type="image/png"
        )

    except Exception as e:
        print(f"Error generating preview: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating preview: {str(e)}")


@router.post("/quiz/generate", response_model=QuizResponse)
async def generate_quiz(
    request: QuizRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a multiple-choice quiz based on a previously uploaded PDF.
    """
    start_time = time.time()

    try:
        # Check if the PDF belongs to the user
        user_id = current_user["user_id"]

        # Check if PDF exists and belongs to user
        pdf = db.query(PDF).filter(PDF.id == request.pdf_id, PDF.user_id == user_id).first()
        if not pdf:
            raise HTTPException(status_code=404, detail="PDF not found in your library")

        # Get comprehensive context from the PDF for quiz generation
        all_chunks = await retriever.search(
            "Generate comprehensive quiz questions",
            request.pdf_id,
            top_k=10  # Increase for broader context
        )

        if not all_chunks:
            raise HTTPException(status_code=404, detail="Could not extract enough content for quiz generation")

        # Concatenate context for the LLM
        context = "\n\n".join([chunk["text"] for chunk in all_chunks])

        # Prepare the prompt for quiz generation
        system_prompt = f"""
        You are an educational quiz generator. Based on the provided content, create {request.num_questions} multiple-choice
        questions at {request.difficulty} difficulty level.

        For each question:
        1. Create a clear, concise question based on important concepts in the material
        2. Generate four possible answers where only one is correct
        3. Include a brief explanation for why the correct answer is right

        Ensure questions test understanding, not just memorization. Vary question types to test different cognitive skills.
        """

        user_prompt = f"""
        Please generate {request.num_questions} multiple-choice questions based on this content:

        {context}

        Format your response as a JSON object with the following structure:
        {{
            "questions": [
                {{
                    "question": "Question text here?",
                    "answers": [
                        {{"text": "First option", "is_correct": false}},
                        {{"text": "Second option", "is_correct": false}},
                        {{"text": "Correct option", "is_correct": true}},
                        {{"text": "Fourth option", "is_correct": false}}
                    ],
                    "explanation": "Explanation of why the correct answer is right"
                }}
            ]
        }}
        """

        # Generate quiz using the LLM
        quiz_json = await llm_service.generate_structured_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )

        processing_time = time.time() - start_time

        # Store quiz in database
        quiz_id = str(uuid.uuid4())
        quiz = Quiz(
            id=quiz_id,
            pdf_id=request.pdf_id,
            user_id=user_id,
            title=f"Quiz for {pdf.filename}",
            questions=quiz_json
        )
        db.add(quiz)
        db.commit()

        # Return the quiz
        return QuizResponse(
            pdf_id=request.pdf_id,
            filename=pdf.filename,
            questions=quiz_json["questions"],
            processing_time=processing_time
        )

    except Exception as e:
        print(f"Error generating quiz: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating quiz: {str(e)}")


@router.post("/quiz/submit", response_model=QuizResult)
async def submit_quiz(
    submission: QuizSubmission,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a quiz for grading.
    """
    try:
        # First, check if the PDF belongs to the user
        pdf_id = submission.pdf_id
        user_id = current_user["user_id"]

        # Check if PDF exists and belongs to user
        pdf = db.query(PDF).filter(PDF.id == pdf_id, PDF.user_id == user_id).first()
        if not pdf:
            raise HTTPException(status_code=404, detail="PDF not found in your library")

        # Get the latest quiz for this PDF
        quiz = db.query(Quiz).filter(
            Quiz.pdf_id == pdf_id,
            Quiz.user_id == user_id
        ).order_by(Quiz.created_at.desc()).first()

        if not quiz:
            raise HTTPException(status_code=400, detail="No quiz found for this PDF")

        quiz_data = quiz.questions

        # Calculate score and generate feedback
        questions = quiz_data["questions"]
        total_questions = len(questions)
        correct_count = 0
        feedback = []

        for question_index_str, selected_answer_index in submission.answers.items():
            question_index = int(question_index_str)
            if question_index >= total_questions:
                continue

            question = questions[question_index]

            # Find if the selected answer is correct
            is_correct = False
            correct_answer_idx = None

            for i, answer in enumerate(question["answers"]):
                if answer.get("is_correct", False):
                    correct_answer_idx = i
                    if i == selected_answer_index:
                        is_correct = True
                    break

            # Add to correct count if answer is right
            if is_correct:
                correct_count += 1

            # Add feedback
            feedback.append({
                "question_index": question_index,
                "result": "correct" if is_correct else "incorrect",
                "selected_answer": selected_answer_index,
                "correct_answer": correct_answer_idx
            })

        # Calculate percentage score
        percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0

        # Create and return QuizResult
        result = QuizResult(
            score=correct_count,
            total=total_questions,
            percentage=percentage,
            feedback=feedback
        )

        return result

    except Exception as e:
        print(f"Error submitting quiz: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing quiz submission: {str(e)}")