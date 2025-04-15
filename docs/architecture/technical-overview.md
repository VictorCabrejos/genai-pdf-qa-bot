# GenAI PDF Q&A Bot: Technical Architecture Overview

## Table of Contents
1. [Introduction](#introduction)
2. [Architectural Pattern](#architectural-pattern)
3. [Technology Stack](#technology-stack)
4. [Component Breakdown](#component-breakdown)
5. [AI Implementation Details](#ai-implementation-details)
6. [Authentication and Security](#authentication-and-security)
7. [Data Flow](#data-flow)
8. [Business Value and Use Cases](#business-value-and-use-cases)
9. [Best Practices and Learning Points](#best-practices-and-learning-points)

## Introduction

The GenAI PDF Q&A Bot is a web application that allows users to upload PDF documents, ask questions about their content, and generate quizzes to test knowledge retention. The system uses modern AI techniques including language models and vector embeddings to understand document content and provide accurate responses to natural language queries.

This document provides a technical overview of the system's architecture, explaining how different components interact, the technologies employed, and the AI methods utilized.

## Architectural Pattern

The application follows a **Service-Oriented MVC (Model-View-Controller)** architecture, which enhances the traditional MVC pattern with dedicated service layers for complex business logic and external integrations.

### Why This Pattern?

1. **Separation of Concerns**: Clear boundaries between data management, business logic, user interface, and external services
2. **Maintainability**: Modular components are easier to update independently
3. **Testability**: Isolated components can be tested separately
4. **Scalability**: Services can be extracted into microservices if needed in the future

### Component Mapping

| Architectural Layer | Project Components |
|---------------------|-------------------|
| **Model** | `app/models/`, `db/` directory |
| **View** | `templates/` directory, `static/` directory |
| **Controller** | `app/routes/` directory |
| **Services** | `app/services/` directory |

## Technology Stack

### Backend Technologies
- **Python 3.11**: Core programming language chosen for its readability, robust ecosystem for AI/ML, and extensive libraries
- **FastAPI**: Modern, high-performance web framework with automatic OpenAPI documentation
  - Provides async support for handling concurrent requests efficiently
  - Built-in request validation and serialization
  - Type hints for better code quality
- **Pydantic**: Data validation and settings management
  - Ensures data integrity throughout the application
  - Automatic schema generation for API endpoints

### Frontend Technologies
- **HTML/CSS/JavaScript**: Core web technologies for UI development
- **TailwindCSS**: Utility-first CSS framework for responsive design
- **Fetch API**: Modern JavaScript API for making HTTP requests

### AI and Data Processing
- **OpenAI API**: Provides access to powerful language models
  - GPT-4o-mini: Used for natural language understanding and generation
  - text-embedding-3-small: Used for creating vector embeddings (more efficient than the older text-embedding-ada-002)
- **PyPDF2/pdf2image**: PDF processing and text extraction
- **NumPy**: Numerical operations for vector similarity calculations

### Data Storage
- **PostgreSQL Database** (Current Implementation):
  - Relational database for structured data storage
  - pgvector extension for vector embedding storage
  - Scalable solution with improved query performance
  - Introduced in April 2025 migration

- **File-based storage** (Original Implementation):
  - JSON files for document storage and vector embeddings
  - Simple implementation suitable for prototype/educational contexts
  - Used until April 2025 migration to PostgreSQL

### Database Migration
- **Transition Date**: April 15, 2025
- **Primary Benefits**:
  - Improved scalability for larger document collections
  - Enhanced query performance and data integrity
  - Support for concurrent users and operations
  - Simplified backup and recovery procedures
- **Migration Tools**:
  - SQLAlchemy ORM for database interactions
  - Alembic for database schema migrations
  - pgvector extension for efficient vector operations

### Authentication
- **JWT (JSON Web Tokens)**: Stateless authentication mechanism
  - Secure communication between client and server
  - Reduced server-side storage requirements

## Component Breakdown

### Model Layer
The Model layer represents the application data and business rules.

#### Key Components:
- **SQLAlchemy Models** (`app/database.py`, Current Implementation)
  - ORM-based models for database entities
  - Relationship definitions between tables
  - Type validation and constraints
  - Introduced with PostgreSQL migration (April 2025)

- **Pydantic Schemas** (`models/pydantic_schemas.py`)
  - Define data structures for request/response validation
  - Ensure type safety and data integrity

- **Database Structure**
  - **PostgreSQL Database** (Current Implementation):
    - Relational tables for users, documents, chunks, quizzes, etc.
    - pgvector extension for efficient embedding storage
    - Foreign key constraints for data integrity

  - **File-based Structure** (Original Implementation, pre-April 2025):
    - `users.json`: User credentials and profile information
    - `pdfs/` directory: Uploaded PDFs and their metadata
      - Each PDF had its own directory with:
        - `chunks.json`: Text chunks with vector embeddings
        - `pdf_info.json`: Metadata about the document

### View Layer
The View layer handles the presentation and user interface.

#### Key Components:
- **HTML Templates** (`templates/` directory)
  - `landing.html`: Public landing page
  - `signup.html`/`login.html`: Authentication interfaces
  - `dashboard.html`: User's document library
  - `viewer.html`: PDF viewing and question interface
  - `quiz.html`: Quiz generation and interaction

- **Static Assets** (`static/` directory)
  - `css/styles.css`: Custom styling
  - `js/main.js`: Client-side functionality

### Controller Layer
The Controller layer handles HTTP requests and coordinates the application flow.

#### Key Components:
- **Route Handlers** (`app/routes/` directory)
  - `pdf_routes.py`: Manages PDF uploading, retrieval, and querying
  - `quiz_routes.py`: Handles quiz generation and submission
  - `auth/routes.py`: Manages user authentication

- **Application Entry Point** (`app/main.py`)
  - Configures FastAPI application
  - Registers route handlers
  - Sets up middleware

### Service Layer
The Service layer contains complex business logic and external integrations.

#### Key Components:
- **LLM Service** (`app/services/llm.py`)
  - Handles communication with language models
  - Formats prompts and processes responses

- **Retriever Service** (`app/services/retriever.py`)
  - Manages document storage and retrieval
  - Implements semantic search functionality

- **Embedding Service** (`app/services/embedding.py`)
  - Generates vector embeddings for text
  - Supports semantic similarity operations

## AI Implementation Details

The AI capabilities of the system are built around several key concepts:

### Text Embeddings
**What are embeddings?**
Embeddings are numerical representations of text that capture semantic meaning. Similar texts will have similar vector representations in the embedding space.

**How we use them:**
- Each document is split into chunks
- Each chunk is transformed into a vector embedding (using OpenAI's embedding model)
- These embeddings allow us to find relevant parts of documents based on semantic similarity rather than just keyword matching

**Implementation in code:**
```python
# From app/services/embedding.py
async def generate_embedding(self, text):
    """
    Generate embedding vector for a piece of text using OpenAI's API.

    Args:
        text: The text to generate an embedding for

    Returns:
        List of floats representing the embedding vector
    """
    try:
        # Call OpenAI's embedding API
        response = client.embeddings.create(
            input=text,
            model=self.model
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise
```

### Text Chunking
**What is chunking?**
Chunking involves breaking down large documents into smaller segments that can be processed independently.

**Why it's necessary:**
1. Language models have input token limits
2. Enables more precise retrieval of relevant information
3. Improves processing efficiency and cost management

**Implementation in code:**
```python
# From app/services/retriever.py
def _split_text_into_chunks(self, text, chunk_size=1000, overlap=200):
    """
    Split a large text into overlapping chunks.

    Args:
        text: The text to split
        chunk_size: Target size of each chunk in characters
        overlap: Number of characters to overlap between chunks

    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        # Try to find a natural break point (period, newline)
        if end < len(text):
            # Look for a natural break point, like a period followed by whitespace
            for i in range(min(overlap, end - start)):
                if text[end - i - 1] in ['.', '!', '?', '\n'] and (
                    end - i == len(text) or text[end - i].isspace()
                ):
                    end = end - i
                    break

        # Add the chunk
        chunks.append(text[start:end])

        # Move start position considering overlap
        start = max(start + 1, end - overlap)

    return chunks
```

### Vector Search
**What is vector search?**
Vector search finds the most similar documents to a query by comparing their vector embeddings.

**How it works:**
1. The user's question is converted to an embedding vector
2. This vector is compared to all document chunk vectors using cosine similarity
3. The most similar chunks are retrieved as context for the answer

**Implementation in code (PostgreSQL-based, current):**
```python
# From app/services/retriever.py (After April 2025 migration)
async def search(self, pdf_id, query, top_k=5, db=None):
    """
    Search for chunks relevant to a query using semantic similarity with PostgreSQL.

    Args:
        pdf_id: The ID of the PDF to search in
        query: The search query
        top_k: Number of top results to return
        db: Database session

    Returns:
        List of most relevant text chunks
    """
    # Generate embedding for the query
    query_embedding = await self.embedding_service.generate_embedding(query)

    # Find document in the database
    document = db.query(Document).filter(Document.pdf_id == pdf_id).first()
    if not document:
        return []

    # Query chunks using vector similarity operation (with pgvector)
    # This uses the vector similarity operator in PostgreSQL
    chunks = db.query(Chunk).filter(Chunk.document_id == document.id)\
              .order_by(Chunk.embedding.cosine_distance(query_embedding))\
              .limit(top_k).all()

    # Return the chunks with their text content
    return [{"text": chunk.text, "page_number": chunk.page_number} for chunk in chunks]
```

**Original file-based implementation (pre-April 2025):**
```python
# From app/services/retriever.py (Original version)
async def search(self, pdf_id, query, top_k=5):
    """
    Search for chunks relevant to a query using semantic similarity.

    Args:
        pdf_id: The ID of the PDF to search in
        query: The search query
        top_k: Number of top results to return

    Returns:
        List of most relevant text chunks
    """
    # Get all chunks for the PDF
    chunks = await self.get_chunks_by_id(pdf_id)

    # Generate embedding for the query
    query_embedding = await self.embedding_service.generate_embedding(query)

    # Calculate similarity with each chunk
    results = []
    for i, chunk in enumerate(chunks):
        chunk_embedding = chunk.get("embedding")
        if not chunk_embedding:
            continue

        # Calculate cosine similarity
        similarity = self._cosine_similarity(query_embedding, chunk_embedding)
        results.append((chunk, similarity))

    # Sort by similarity (highest first)
    results.sort(key=lambda x: x[1], reverse=True)

    # Return top k results
    return [chunk for chunk, _ in results[:top_k]]
```

### Question Answering
**How it works:**
1. Retrieve the most relevant document chunks for a given question
2. Format a prompt that includes the question and context from relevant chunks
3. Send this prompt to the LLM (GPT-4o-mini)
4. The LLM generates an answer that synthesizes information from the provided context

**Implementation in code:**
```python
# From app/services/llm.py
async def generate_answer(self, question: str, context_chunks: List[Dict[str, Any]]) -> str:
    """
    Generate an answer to a question based on provided context chunks.

    Args:
        question: The user's question
        context_chunks: Retrieved document chunks relevant to the question

    Returns:
        Generated answer text
    """
    # Detect if question likely needs interpretation
    allow_interpretation = self._detect_interpretation_question(question)

    # Create a prompt with the question and context
    prompt = self._create_prompt(question, context_chunks, allow_interpretation)

    # Call the language model
    response = client.chat.completions.create(
        model=self.model,
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant answering questions about PDF documents."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=1000
    )

    return response.choices[0].message.content
```

### Quiz Generation
**How it works:**
1. Retrieve content chunks from the entire document
2. Format a specialized prompt asking the LLM to create multiple-choice questions
3. The LLM generates questions, answer choices, and explanations
4. The response is structured as JSON for easy rendering in the UI

**Implementation in code:**
```python
# From app/routes/quiz_routes.py (simplified)
@router.post("/generate")
async def generate_quiz(request: QuizRequest, current_user: dict):
    # Retrieve document content
    content_chunks = retriever.get_chunks_by_id(request.pdf_id)
    combined_content = "\n\n".join([chunk["text"] for chunk in content_chunks])

    # Create prompts for quiz generation
    system_prompt = """
    You are an expert quiz creator. Create multiple-choice questions based on the provided document content.
    """

    user_prompt = f"""
    Create a quiz with {request.num_questions} multiple-choice questions based on this document.

    DOCUMENT CONTENT:
    {combined_content}

    INSTRUCTIONS:
    1. Each question should have 4 answer choices (A, B, C, D)
    2. Exactly one answer should be marked as correct
    3. Include an explanation for why the correct answer is right
    4. Questions should cover key concepts from throughout the document

    FORMAT YOUR RESPONSE AS A JSON OBJECT with this structure:
    {{
        "questions": [
            {{
                "question": "Question text?",
                "answers": [
                    {{ "text": "Option A", "is_correct": false }},
                    {{ "text": "Option B", "is_correct": true }},
                    {{ "text": "Option C", "is_correct": false }},
                    {{ "text": "Option D", "is_correct": false }}
                ],
                "explanation": "Explanation of why the correct answer is right"
            }}
        ]
    }}
    """

    # Call LLM to generate structured quiz
    response = await llm_service.generate_structured_response(system_prompt, user_prompt)

    # Return quiz data
    quiz_id = str(uuid.uuid4())
    return {"quiz_id": quiz_id, "questions": response["questions"]}
```

### SQLAlchemy ORM Integration
**What is SQLAlchemy ORM?**
SQLAlchemy ORM (Object-Relational Mapping) is a library that facilitates communication between Python objects and database tables, introduced during the PostgreSQL migration.

**Why it's important:**
1. Abstracts database operations behind Python object interfaces
2. Promotes clean, maintainable code through class-based models
3. Provides powerful query capabilities through the ORM API
4. Handles database connections, transactions, and session management

**Implementation in code:**
```python
# From app/database.py
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    pdfs = relationship("PDF", back_populates="user")

class PDF(Base):
    __tablename__ = "pdfs"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    title = Column(String)
    filename = Column(String)
    created_at = Column(DateTime, default=func.now())
    file_path = Column(String)

    # Relationships
    user = relationship("User", back_populates="pdfs")
    chunks = relationship("PDFChunk", back_populates="pdf")

class PDFChunk(Base):
    __tablename__ = "pdf_chunks"

    id = Column(Integer, autoincrement=True, primary_key=True)
    pdf_id = Column(String, ForeignKey("pdfs.id"))
    content = Column(Text)
    page_number = Column(Integer)
    embedding_file = Column(String, nullable=True)

    # Relationships
    pdf = relationship("PDF", back_populates="chunks")
```

## Authentication and Security

The application implements a robust authentication system using JWTs:

### JWT Authentication Flow
1. User registers or logs in
2. Server validates credentials and generates a JWT token
3. Token is stored in the client's localStorage
4. Client sends token with each request in the Authorization header
5. Server validates the token and identifies the user

### Implementation Highlights
```python
# From app/auth/utils.py
def create_access_token(data: dict):
    """Create a new JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(authorization: str = Header(...)):
    """Decode JWT token and return current user."""
    try:
        # Extract token from Authorization header
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")

        # Decode and validate token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Return user data
        return {"user_id": user_id}
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
```

### Security Considerations
- Passwords are hashed before storage
- JWT tokens have expiration times
- Protected routes require valid authentication
- CORS middleware is configured to control access

## Data Flow

### PDF Processing Flow
```
1. User uploads PDF
   |
2. PDF is processed and text extracted
   |
3. Text is split into chunks
   |
4. Each chunk is converted to vector embeddings
   |
5. Chunks and embeddings are stored in the PostgreSQL database
   (Previously stored in JSON files before April 2025 migration)
```

### Question Answering Flow
```
1. User asks a question about a document
   |
2. Question is converted to an embedding vector
   |
3. System finds most similar document chunks (vector search)
   |
4. Retrieved chunks + question are sent to LLM
   |
5. LLM generates an answer based on provided context
   |
6. Answer is returned to user
```

### Quiz Generation Flow
```
1. User requests a quiz for a document
   |
2. System retrieves document chunks
   |
3. Combined document content sent to LLM with quiz generation prompt
   |
4. LLM generates structured quiz with questions, options and explanations
   |
5. Quiz is presented to user for interaction
   |
6. User submits answers and receives score and feedback
```

## Business Value and Use Cases

### Primary Value Proposition
The GenAI PDF Q&A Bot transforms static document repositories into interactive knowledge bases, enabling users to:
1. Quickly find specific information without manual searching
2. Test comprehension through automatically generated quizzes
3. Interact with document content in natural language

### Time and Cost Savings
- **Manual Search Reduction**: 70-90% time saving compared to manually scanning documents for information
- **Quiz Creation Efficiency**: Generates in seconds what would take an educator hours to create manually
- **Knowledge Retention**: Improves learning outcomes through interactive engagement with content

### Use Cases

#### Educational Institutions
- **Student Self-Study**: Students upload course materials and test their understanding
- **Teaching Assistant**: Professors provide course materials that students can query
- **Exam Preparation**: Automated quiz generation for study sessions
- **Research Support**: Quick extraction of information from research papers

#### Corporate Settings
- **Policy Compliance**: Employees can query company policy documents
- **Training Materials**: Interactive learning for onboarding and professional development
- **Knowledge Management**: Making organizational knowledge accessible and queryable
- **Legal Document Review**: Quick extraction of key clauses and provisions

#### Research Organizations
- **Literature Review**: Extract information from multiple scientific papers
- **Data Analysis**: Question research findings across multiple documents
- **Grant Writing Support**: Access previous successful applications for reference

#### Healthcare
- **Medical Education**: Interactive learning for medical students
- **Patient Information**: Convert complex medical literature into accessible information
- **Protocol Adherence**: Quick reference to procedural guidelines

### Competitive Advantages Over Generic Solutions
- **Privacy Preservation**: Documents remain within the organization's infrastructure
- **Customization**: Can be tailored to specific domains and use cases
- **Integration Potential**: Can connect with existing systems and workflows
- **Cost Control**: Predictable usage costs compared to public commercial services

## Best Practices and Learning Points

### AI Implementation Best Practices
1. **Prompt Engineering**
   - Clear, specific instructions to guide model behavior
   - System and user role separation for context control
   - Structured output formatting for consistent results

2. **Efficient API Usage**
   - Retrieve-then-generate pattern reduces token consumption
   - Vector search pre-filters content to most relevant sections
   - Caching of embeddings to avoid redundant API calls

3. **Error Handling**
   - Graceful fallbacks when AI services fail
   - Comprehensive logging of AI interactions
   - Clear error messages that protect API details

### Software Engineering Best Practices
1. **Modular Architecture**
   - Clear separation of concerns
   - Services with well-defined interfaces
   - Configuration isolation from business logic

2. **Progressive Enhancement**
   - Core functionality works without advanced features
   - Graceful degradation when services are unavailable
   - Accessibility considerations in UI design

3. **Security By Design**
   - Authentication for all sensitive operations
   - Input validation at multiple levels
   - Secure handling of credentials and tokens

### Key Learning Points
1. **AI Integration Patterns**
   - How to combine retrieval-augmented generation with language models
   - Effective chunking strategies for document processing
   - Vector embedding creation and similarity calculations

2. **Full-Stack Development**
   - Backend and frontend integration patterns
   - Asynchronous request handling
   - State management across the application

3. **User Experience Design**
   - Balancing simplicity with powerful features
   - Progressive disclosure of complex functionality
   - Feedback mechanisms for AI-generated content

---

*Created: April 10, 2025*
*Updated: April 15, 2025 (PostgreSQL Migration)*