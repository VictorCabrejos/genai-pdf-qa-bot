from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .routes import pdf_routes
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if OpenAI API key is available
if not os.getenv("OPENAI_API_KEY"):
    print("Warning: OPENAI_API_KEY environment variable not set. Set this in .env file.")

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

# Include PDF routes
app.include_router(pdf_routes.router, prefix="/api", tags=["pdf"])


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to the GenAI PDF Q&A Bot API",
        "docs_url": "/docs",
        "upload_endpoint": "/api/upload",
        "ask_endpoint": "/api/ask",
    }


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