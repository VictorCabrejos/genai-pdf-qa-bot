from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import json
import uuid
import sys
import traceback
import os
import io
from pathlib import Path
import logging
import time
import inspect

# Import auth utilities
from ..auth.utils import get_current_user

# Set up logging with more detailed formatting
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler("quiz_generation.log", mode='w'),  # 'w' mode to clear previous logs
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("quiz_routes")

def log_debug_info(message, data=None):
    """Helper function to log a message with caller information"""
    frame = inspect.currentframe().f_back
    file_name = os.path.basename(frame.f_code.co_filename)
    line_no = frame.f_lineno

    log_message = f"[{file_name}:{line_no}] {message}"
    if data:
        if isinstance(data, dict) or isinstance(data, list):
            try:
                data_str = json.dumps(data, indent=2)
                if len(data_str) > 500:
                    data_str = data_str[:500] + "... (truncated)"
                log_message += f"\nDATA: {data_str}"
            except:
                log_message += f"\nDATA: {str(data)[:500]}"
        else:
            log_message += f"\nDATA: {str(data)[:500]}"

    logger.debug(log_message)
    return log_message

# Get the root directory path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
logger.debug(f"ROOT_DIR set to: {ROOT_DIR}")

# Import services
try:
    from app.services.llm import LLMService, get_llm_client
    from app.services.retriever import Retriever
    logger.debug("Services imported successfully")
except Exception as e:
    logger.critical(f"Failed to import services: {str(e)}")
    logger.critical(traceback.format_exc())

router = APIRouter()

# Initialize services with explicit error handling
try:
    llm_service = LLMService()
    logger.debug(f"LLM service initialized with model: {llm_service.model}")
    # Check if we can access the OpenAI API key (using the get_llm_client function)
    client = get_llm_client()
    logger.debug(f"LLM client API key exists: {bool(client.api_key)}")
except Exception as e:
    logger.critical(f"Failed to initialize LLM service: {str(e)}")
    logger.critical(traceback.format_exc())
    llm_service = None

try:
    retriever = Retriever()
    logger.debug(f"Retriever service initialized with pdfs_dir: {retriever.pdfs_dir}")
except Exception as e:
    logger.critical(f"Failed to initialize Retriever service: {str(e)}")
    logger.critical(traceback.format_exc())
    retriever = None

class QuizRequest(BaseModel):
    pdf_id: str
    num_questions: int = 5

class QuizResponse(BaseModel):
    quiz_id: str
    questions: List[Dict]

class QuizSubmissionRequest(BaseModel):
    pdf_id: str
    answers: Dict[str, int]  # Question index -> selected answer index

class SubmissionResult(BaseModel):
    score: int
    total: int
    percentage: float
    feedback: List[Dict]

@router.post("/generate")
async def generate_quiz(
    request: QuizRequest = Body(...),
    current_user: dict = Depends(get_current_user)  # Add authentication dependency
):
    """
    Generate a quiz based on PDF content.

    Args:
        request: The quiz generation request containing pdf_id and num_questions
        current_user: Current authenticated user

    Returns:
        Quiz data with questions and answers
    """
    start_time = time.time()
    logger.info(f"Starting quiz generation for PDF ID: {request.pdf_id} by user: {current_user['user_id']}")

    # Check if services were properly initialized
    if llm_service is None or retriever is None:
        error_msg = "Quiz service initialization failed. See logs for details."
        logger.error(error_msg)
        return JSONResponse(
            status_code=500,
            content={"message": error_msg}
        )

    try:
        pdf_id = request.pdf_id
        num_questions = request.num_questions

        # Log the incoming request
        log_debug_info(f"Processing quiz generation request", {
            "pdf_id": pdf_id,
            "num_questions": num_questions
        })

        # Validate PDF ID exists
        pdf_path = ROOT_DIR / "db" / "pdfs" / pdf_id
        log_debug_info(f"Checking if PDF directory exists at {pdf_path}")

        if not pdf_path.exists():
            error_msg = f"PDF directory not found: {pdf_path}"
            logger.error(error_msg)
            return JSONResponse(
                status_code=404,
                content={"message": "PDF not found", "path_checked": str(pdf_path)}
            )

        log_debug_info(f"PDF directory exists")

        # Get a list of all files in the PDF directory
        try:
            dir_contents = list(pdf_path.glob('*'))
            log_debug_info(f"Contents of PDF directory:", [str(f.name) for f in dir_contents])
        except Exception as e:
            log_debug_info(f"Error listing directory contents: {str(e)}")

        # Load PDF metadata
        pdf_info_path = pdf_path / "pdf_info.json"
        log_debug_info(f"Checking if PDF info file exists at {pdf_info_path}")

        if not pdf_info_path.exists():
            error_msg = f"PDF info file not found: {pdf_info_path}"
            logger.error(error_msg)
            return JSONResponse(
                status_code=404,
                content={"message": "PDF metadata not found", "path_checked": str(pdf_info_path)}
            )

        log_debug_info(f"PDF info file exists, loading it")
        try:
            with open(pdf_info_path, "r", encoding='utf-8') as f:
                pdf_info = json.load(f)
                log_debug_info(f"Loaded PDF info", pdf_info)
        except Exception as e:
            error_msg = f"Error reading PDF info: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return JSONResponse(
                status_code=500,
                content={"message": error_msg}
            )

        # Retrieve PDF content chunks
        log_debug_info(f"Retrieving content chunks for PDF {pdf_id}")
        chunks_start = time.time()

        # Get key chunks from the PDF for quiz generation
        try:
            content_chunks = retriever.get_chunks_by_id(pdf_id)
            retrieval_time = time.time() - chunks_start
            log_debug_info(f"Retrieved {len(content_chunks) if content_chunks else 0} chunks in {retrieval_time:.2f}s")
        except Exception as e:
            error_msg = f"Error retrieving chunks: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return JSONResponse(
                status_code=500,
                content={"message": error_msg}
            )

        if not content_chunks:
            error_msg = f"No content chunks found for PDF {pdf_id}"
            logger.error(error_msg)
            return JSONResponse(
                status_code=404,
                content={"message": "No content found for this PDF"}
            )

        # Check structure of first chunk to debug
        try:
            first_chunk = content_chunks[0]
            log_debug_info(f"First chunk structure", {
                "keys": list(first_chunk.keys()),
                "has_text": "text" in first_chunk,
                "has_embedding": "embedding" in first_chunk,
                "has_page_number": "page_number" in first_chunk,
            })

            # Show sample of text content
            if "text" in first_chunk:
                text_sample = first_chunk["text"][:100] + "..." if len(first_chunk["text"]) > 100 else first_chunk["text"]
                log_debug_info(f"Sample text from first chunk", text_sample)
        except Exception as e:
            log_debug_info(f"Error examining first chunk: {str(e)}")

        # Create combined content for quiz generation
        log_debug_info(f"Creating combined content from chunks")
        try:
            # Correctly access the text field in each chunk
            if "text" in content_chunks[0]:
                combined_content = "\n\n".join([chunk["text"] for chunk in content_chunks])
            else:
                # Fallback if the structure is different
                log_debug_info(f"Chunk structure doesn't contain 'text' field, attempting to identify content field")
                # Try to guess which field might contain the text content
                potential_content_fields = ["content", "text_content", "chunk_text", "data"]
                found_field = None

                for field in potential_content_fields:
                    if field in content_chunks[0]:
                        found_field = field
                        break

                if found_field:
                    log_debug_info(f"Using '{found_field}' as content field")
                    combined_content = "\n\n".join([chunk[found_field] for chunk in content_chunks])
                else:
                    # Last resort: convert each chunk to string
                    log_debug_info(f"No recognized content field found, using string representation of chunks")
                    combined_content = "\n\n".join([str(chunk) for chunk in content_chunks])

            content_length = len(combined_content)
            log_debug_info(f"Created combined content with {content_length} characters")
            # Log a preview of the combined content
            if content_length > 0:
                content_preview = combined_content[:200] + "..." if content_length > 200 else combined_content
                log_debug_info(f"Content preview", content_preview)
        except Exception as e:
            error_msg = f"Error creating combined content: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return JSONResponse(
                status_code=500,
                content={"message": error_msg}
            )

        # Prepare quiz generation prompt
        pdf_title = f"Document {pdf_id[:8]}"
        log_debug_info(f"Creating quiz generation prompts")

        system_prompt = """
        You are an expert quiz creator. Your task is to create multiple-choice questions based on the provided document content.
        Each question should test understanding of key concepts from the document.
        """

        user_prompt = f"""
        Create a quiz with {num_questions} multiple-choice questions based on this document titled "{pdf_title}".

        DOCUMENT CONTENT:
        {combined_content}

        INSTRUCTIONS:
        1. Each question should have 4 answer choices (A, B, C, D)
        2. Exactly one answer should be marked as correct
        3. Include an explanation for why the correct answer is right
        4. Questions should cover key concepts from throughout the document
        5. Questions should test understanding, not just memorization

        FORMAT YOUR RESPONSE AS A JSON OBJECT with this structure:
        {{
            "questions": [
                {{
                    "question": "Question text goes here?",
                    "answers": [
                        {{ "text": "Option A", "is_correct": false }},
                        {{ "text": "Option B", "is_correct": true }},
                        {{ "text": "Option C", "is_correct": false }},
                        {{ "text": "Option D", "is_correct": false }}
                    ],
                    "explanation": "Explanation of why the correct answer is right"
                }},
                ... more questions ...
            ]
        }}
        """

        # Log prompt sizes
        log_debug_info(f"Prompt statistics", {
            "system_prompt_length": len(system_prompt),
            "user_prompt_length": len(user_prompt),
            "combined_content_length": len(combined_content)
        })

        # Call LLM to generate quiz
        log_debug_info(f"Calling LLM service to generate quiz")
        generation_start = time.time()

        try:
            log_debug_info(f"About to call LLM service with prompts")
            response = await llm_service.generate_structured_response(system_prompt, user_prompt)
            generation_time = time.time() - generation_start
            log_debug_info(f"LLM response received in {generation_time:.2f}s", {
                "response_type": type(response).__name__,
                "has_error": "error" in response if isinstance(response, dict) else "N/A",
                "keys": list(response.keys()) if isinstance(response, dict) else "N/A"
            })

            # Log a preview of the raw response if it's large
            if isinstance(response, dict) and "raw_response" in response:
                raw_preview = response["raw_response"][:300] + "..." if len(response["raw_response"]) > 300 else response["raw_response"]
                log_debug_info("Raw response preview", raw_preview)

            # Validate the structure of the response
            if isinstance(response, dict) and "error" in response:
                error_msg = f"LLM error: {response.get('error', 'Unknown error')}"
                logger.error(error_msg)
                if "raw_response" in response:
                    logger.error(f"Raw response preview: {response['raw_response'][:300]}...")
                return JSONResponse(
                    status_code=500,
                    content={"message": "Failed to generate quiz", "error": error_msg}
                )

            if not isinstance(response, dict) or "questions" not in response or not isinstance(response["questions"], list):
                error_keys = list(response.keys()) if isinstance(response, dict) else "not a dict"
                error_msg = f"Invalid response format from LLM: missing or invalid 'questions' field. Response keys: {error_keys}"
                logger.error(error_msg)
                return JSONResponse(
                    status_code=500,
                    content={"message": "Invalid quiz format", "error": error_msg}
                )

            # Log the number of questions generated
            questions = response["questions"]
            log_debug_info(f"Successfully generated {len(questions)} questions")

            # Log the first question as a sample
            if questions:
                log_debug_info(f"Sample question", questions[0])

            # Generate a unique ID for the quiz
            quiz_id = str(uuid.uuid4())
            log_debug_info(f"Generated quiz ID: {quiz_id}")

            # Return the quiz data
            return {"quiz_id": quiz_id, "questions": questions}

        except Exception as e:
            error_msg = f"Error during LLM quiz generation: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())

            # Generate a fallback quiz to help debugging
            error_details = str(e)
            quiz_id = str(uuid.uuid4())

            fallback_quiz = {
                "quiz_id": quiz_id,
                "questions": [
                    {
                        "question": f"ERROR: Could not generate quiz. Please check logs.",
                        "answers": [
                            {"text": "API key issue", "is_correct": False},
                            {"text": "Content processing error", "is_correct": False},
                            {"text": "Model limitation", "is_correct": False},
                            {"text": "Server error", "is_correct": True}
                        ],
                        "explanation": f"Error details: {error_details[:100]}..."
                    }
                ],
                "error": error_details
            }

            logger.info("Returning fallback quiz due to error")
            return JSONResponse(
                status_code=500,
                content={"message": "Error generating quiz. Please try again.", "error": str(e)[:100], "fallback_quiz": fallback_quiz}
            )

    except Exception as e:
        error_msg = f"Unhandled exception in generate_quiz: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"message": "Error generating quiz. Please try again.", "error": str(e)[:100]}
        )

@router.post("/submit")
async def submit_quiz(
    request: QuizSubmissionRequest = Body(...),
    current_user: dict = Depends(get_current_user)  # Add authentication dependency
):
    """
    Submit quiz answers for scoring.

    Args:
        request: The quiz submission containing pdf_id and answers
        current_user: Current authenticated user

    Returns:
        Quiz result with score and feedback
    """
    logger.info(f"Processing quiz submission for PDF ID: {request.pdf_id} by user: {current_user['user_id']}")
    
    try:
        # Get the answers and PDF ID from request
        pdf_id = request.pdf_id
        submitted_answers = request.answers
        
        # Log submission details
        log_debug_info("Quiz submission details", {
            "pdf_id": pdf_id,
            "answer_count": len(submitted_answers),
            "answer_keys": list(submitted_answers.keys())
        })
        
        # In a full implementation, we would look up the correct answers
        # For now, simulate scoring by accepting any submission
        
        # Convert string keys to integers (JSON serialization turns keys to strings)
        submitted_answers_int_keys = {int(k): v for k, v in submitted_answers.items()}
        
        # Number of questions is the highest question index + 1
        num_questions = max(int(k) for k in submitted_answers.keys()) + 1 if submitted_answers else 0
        
        # For demo purposes, simulate scoring
        # In a real implementation, we would compare with stored correct answers
        score = len(submitted_answers)
        correct_answers = []
        
        # Generate feedback for each question
        feedback = []
        for question_index in range(num_questions):
            q_idx_str = str(question_index)
            is_correct = question_index in submitted_answers_int_keys
            
            feedback_item = {
                "question_index": q_idx_str,
                "result": "correct" if is_correct else "incorrect",
                "selected_answer": submitted_answers.get(q_idx_str, None)
            }
            feedback.append(feedback_item)
            
            if is_correct:
                correct_answers.append(question_index)
        
        # Calculate percentage score
        percentage = (score / num_questions) * 100 if num_questions > 0 else 0
        
        # Compose and return the result
        result = {
            "score": score,
            "total": num_questions,
            "percentage": percentage,
            "feedback": feedback
        }
        
        logger.info(f"Quiz submission scored: {score}/{num_questions} ({percentage:.1f}%)")
        return result
        
    except Exception as e:
        error_msg = f"Error processing quiz submission: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"message": "Error scoring quiz. Please try again.", "error": str(e)}
        )