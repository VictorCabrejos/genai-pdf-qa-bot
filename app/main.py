from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from .routes import pdf_routes, quiz_routes
from .auth import routes as auth_routes
import os
from dotenv import load_dotenv

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

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions"""
    return JSONResponse(
        status_code=500,
        content={"detail": f"An unexpected error occurred: {str(exc)}"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)