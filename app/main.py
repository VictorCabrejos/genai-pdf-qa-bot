from fastapi import FastAPI, HTTPException, Request, Body, Depends
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from .routes import pdf_routes, quiz_routes
from .auth import routes as auth_routes
from jose import JWTError
import os
import logging
import traceback
from dotenv import load_dotenv
from .database import create_tables, get_db
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("main_app")

# Get base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables with explicit path
load_dotenv(BASE_DIR / '.env')

# Check if OpenAI API key is available
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Warning: OPENAI_API_KEY environment variable not set. Set this in .env file.")
else:
    print(f"API key loaded successfully in main app: {api_key[:5]}...{api_key[-4:]}")

# Create tables in the database
create_tables()

# Create templates and static paths
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Create FastAPI application
app = FastAPI(
    title="GenAI PDF Q&A Bot",
    description="A GPT-powered question-answering assistant for PDF documents",
    version="1.0.0",
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Include PDF routes
app.include_router(pdf_routes.router, prefix="/api", tags=["pdf"])

# Include Authentication routes
app.include_router(auth_routes.router, prefix="/api", tags=["auth"])

# Include Quiz routes
app.include_router(quiz_routes.router, prefix="/api", tags=["quiz"])

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the landing page"""
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/quiz", response_class=HTMLResponse)
async def quiz_page(request: Request):
    """Serve the quiz page"""
    return templates.TemplateResponse("quiz.html", {"request": request})

@app.get("/old", response_class=HTMLResponse)
async def old_index(request: Request):
    """Serve the old frontend HTML template"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve the login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Serve the signup page"""
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Serve the user dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/view/{pdf_id}", response_class=HTMLResponse)
async def view_pdf_page(request: Request, pdf_id: str):
    """Serve the PDF viewer page"""
    return templates.TemplateResponse("viewer.html", {"request": request, "pdf_id": pdf_id})

@app.post("/api/quiz/submit-direct")
async def direct_quiz_submit(request: Request):
    """
    Direct quiz submission endpoint to bypass any router issues.
    """
    try:
        # Parse the JSON body
        json_data = await request.json()

        # Extract data from request
        pdf_id = json_data.get('pdf_id', 'unknown')
        answers = json_data.get('answers', {})
        quiz_data = json_data.get('quizData', {})

        logger.info(f"[DIRECT] Processing quiz submission for PDF: {pdf_id} with {len(answers)} answers")

        # Get questions from quiz data
        questions = quiz_data.get('questions', [])
        if not questions:
            logger.warning("[DIRECT] Quiz submission missing questions data")
            return JSONResponse(
                status_code=400,
                content={"message": "Missing quiz question data"}
            )

        # Number of questions
        num_questions = len(questions)

        # Evaluate answers
        correct_count = 0
        feedback = []

        for q_idx, question in enumerate(questions):
            q_idx_str = str(q_idx)

            # Check if user answered this question
            selected_answer_idx = answers.get(q_idx_str)
            is_answered = selected_answer_idx is not None

            # Find the correct answer
            correct_answer_idx = None
            for idx, answer in enumerate(question.get('answers', [])):
                if answer.get('is_correct', False):
                    correct_answer_idx = idx
                    break

            # Evaluate if answer is correct
            is_correct = False
            if is_answered and selected_answer_idx == correct_answer_idx:
                is_correct = True
                correct_count += 1

            feedback_item = {
                "question_index": q_idx_str,
                "result": "correct" if is_correct else "incorrect",
                "selected_answer": selected_answer_idx,
                "correct_answer": correct_answer_idx
            }
            feedback.append(feedback_item)

        # Calculate percentage
        percentage = (correct_count / num_questions) * 100 if num_questions > 0 else 0

        # Create the result object
        result = {
            "score": correct_count,
            "total": num_questions,
            "percentage": percentage,
            "feedback": feedback
        }

        logger.info(f"[DIRECT] Quiz submission scored: {correct_count}/{num_questions} ({percentage:.1f}%)")
        return result

    except Exception as e:
        error_msg = f"[DIRECT] Error processing quiz submission: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())

        return JSONResponse(
            status_code=500,
            content={
                "message": "Error scoring quiz",
                "error": str(e)
            }
        )

@app.middleware("http")
async def debug_request(request: Request, call_next):
    """Middleware to debug requests and responses"""
    path = request.url.path
    method = request.method

    # Only debug API requests
    if path.startswith("/api"):
        logger.debug(f"Request: {method} {path}")
        logger.debug(f"Headers: {request.headers.get('authorization', 'No Auth Header')[:15]}...")

        try:
            response = await call_next(request)
            logger.debug(f"Response: {method} {path} - Status: {response.status_code}")
            return response
        except Exception as e:
            logger.error(f"Error processing {method} {path}: {str(e)}")
            logger.error(traceback.format_exc())
            return JSONResponse(
                status_code=500,
                content={"detail": f"Server error: {str(e)}"}
            )
    else:
        return await call_next(request)

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions"""
    logger.error(f"Uncaught exception: {str(exc)} - Path: {request.url.path}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": f"An unexpected error occurred: {str(exc)}"},
    )

@app.exception_handler(JWTError)
async def jwt_exception_handler(request: Request, exc: JWTError):
    """Handle JWT authentication errors"""
    logger.error(f"JWT Error: {str(exc)} - Path: {request.url.path}")
    return JSONResponse(
        status_code=401,
        content={"detail": "Authentication failed. Please log in again."},
        headers={"WWW-Authenticate": "Bearer"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)