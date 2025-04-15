# GenAI PDF Q&A Bot Project Structure

**Date:** April 15, 2025
**Status:** Current

This document provides an overview of the GenAI PDF Q&A Bot project structure, explaining the purpose of key directories and files.

## Root Directory

The root directory contains configuration files and entry points for the application:

- **alembic.ini**: Configuration for the Alembic database migration tool
- **Dockerfile**: Container definition for Docker deployment
- **render.yaml**: Configuration for deployment on Render.com
- **requirements.txt**: Python dependencies for the application
- **.env**: Environment variables (not committed to version control)
- **.env.example**: Template for environment variables
- **README.md**: Project overview and setup instructions
- **pdf_qa.db**: SQLite database file (local development fallback)

## Core Application (`app/`)

The `app/` directory contains the main application code:

- **app/main.py**: Application entry point and FastAPI setup
- **app/database.py**: Database connection and SQLAlchemy models

### Authentication (`app/auth/`)

- **app/auth/routes.py**: API endpoints for user authentication (signup, login)
- **app/auth/utils.py**: Authentication utilities including JWT handling

### API Routes (`app/routes/`)

- **app/routes/pdf_routes.py**: Endpoints for PDF upload, retrieval, and querying
- **app/routes/quiz_routes.py**: Endpoints for quiz generation and submission

### Services (`app/services/`)

- **app/services/embedding.py**: Vector embedding generation service
- **app/services/llm.py**: Language model integration service
- **app/services/retriever.py**: Document storage and retrieval service

## Database and Storage (`db/`)

The `db/` directory contains data files:

- **db/users.json**: User credentials and profile information (legacy storage)
- **db/pdfs/**: Directory containing uploaded PDFs and their metadata
  - Each PDF has its own directory with:
    - Original PDF file
    - `chunks.json`: Text chunks with vector embeddings
    - `pdf_info.json`: Document metadata

## Database Migrations (`migrations/`)

The `migrations/` directory contains database schema definitions and version history:

- **migrations/env.py**: Alembic environment configuration
- **migrations/versions/**: Directory containing migration scripts
  - **migrations/versions/001_initial_migration.py**: Initial database schema

## Data Models (`models/`)

- **models/pydantic_schemas.py**: Pydantic models for API request/response validation

## Frontend (`templates/`, `static/`)

### Templates (`templates/`)

HTML templates for the application's web interface:

- **templates/landing.html**: Public landing page
- **templates/signup.html**: User registration page
- **templates/login.html**: User login page
- **templates/dashboard.html**: User's document dashboard
- **templates/viewer.html**: PDF viewer and question interface
- **templates/quiz.html**: Quiz generation and interaction interface

### Static Assets (`static/`)

- **static/css/styles.css**: Custom CSS styling
- **static/js/main.js**: Frontend JavaScript functionality
- **static/images/**: Directory containing images

## Documentation (`docs/`)

The `docs/` directory contains project documentation:

### Architecture (`docs/architecture/`)

- **docs/architecture/technical-overview.md**: Detailed system architecture documentation
- **docs/architecture/database-migration-report.md**: Report on the PostgreSQL migration

### Developer Guides (`docs/guides/`)

- **docs/guides/student-setup-guide.md**: Setup instructions for students
- **docs/guides/gitflow-guide.md**: Git workflow documentation
- **docs/guides/instructor-gitflow-guide.md**: Git workflow guidance for instructors

### Bug Reports (`docs/bug-reports/`)

- **docs/bug-reports/database-migration-format-inconsistency.md**: Database migration issues
- **docs/bug-reports/quiz-submission-routing-bug.md**: Bug in quiz submission routing
- **docs/bug-reports/quiz-generation-auth-bug.md**: Authentication bug in quiz generation

### SOLID Principles Examples (`docs/demos/`)

- **docs/demos/class_demo/**: Example implementations of SOLID principles
- **docs/demos/solution1/**: Example solution for text processing
- **docs/demos/solution2/**: Example solution for notification system

### Assignments (`docs/assignments/`)

- **docs/assignments/solid_principles_assignment.md**: SOLID principles assignment
- **docs/assignments/solid_principles_solutions.md**: Solutions for SOLID principles assignment

## Tests (`tests/`)

- **tests/test_endpoints.py**: API endpoint tests

## Log Files

- **api_debug.log**: Debug logs for API operations
- **llm_service.log**: Logs for language model service
- **retriever.log**: Logs for document retrieval operations
- **quiz_generation.log**: Logs for quiz generation

## Deployment Files

- **Dockerfile**: Container configuration for Docker deployment
- **render.yaml**: Deployment configuration for Render.com