# 🧠 GenAI PDF Q&A Bot

> **🔄 UPDATED: April 15, 2025** - Major database migration from file-based storage to PostgreSQL, improving scalability and performance. [View the full migration report](docs/architecture/database-migration-report.md).

A sophisticated AI-powered platform for document analysis, question answering, and quiz generation. This system leverages advanced natural language processing techniques including vector embeddings, semantic search, and large language models to transform static PDF documents into interactive knowledge bases.

## 🚀 Project Evolution

This project is continuously evolving through planned development phases:

### Phase 1: ✅ Document Q&A System (Completed)
- PDF upload and parsing with advanced text extraction
- Semantic chunking with optimized segmentation algorithms
- Vector embedding generation using OpenAI's embedding models
- Retrieval-Augmented Generation (RAG) for contextual question answering
- User authentication and document management

### Phase 2: ✅ Automated Quiz Generation (Completed)
- Intelligent quiz creation from document content
- Multiple-choice question formatting with distractors
- Answer validation and explanation generation
- Interactive quiz interface with scoring
- Customizable difficulty levels

### Phase 2.5: ✅ Database Migration (Completed)
- Migration from file-based storage to PostgreSQL database
- Enhanced data integrity and relational data management
- Improved performance for concurrent users
- Better scalability for increasing document collections
- Animated landing page with interactive PDF robot visualization

### Phase 3: 🔄 Advanced Analytics (Planned)
- Document comprehension metrics
- User knowledge gap identification
- Learning progress tracking
- Performance visualization dashboards
- Content recommendation engine

### Phase 4: 🔄 Enterprise Integration (Planned)
- Multi-tenant architecture
- Role-based access control
- API for third-party integration
- Enhanced data security features
- Custom model fine-tuning options

## ⚙️ AI Engineering Architecture

The system implements a sophisticated AI pipeline:

### Vector Embeddings
Using dimensional reduction techniques to convert text into dense numerical representations that capture semantic meaning. This allows the system to understand relationships between concepts beyond simple keyword matching.

```python
# Semantic understanding through vector embeddings
embedding = embedding_service.generate_embedding(text_chunk)
```

### Semantic Text Chunking
Advanced document segmentation that respects semantic boundaries, maintaining context coherence while optimizing for retrieval precision.

```python
# Smart chunking with natural breakpoints
chunks = retriever._split_text_into_chunks(text, chunk_size=1000, overlap=200)
```

### Vector Similarity Search
High-performance nearest neighbor search using cosine similarity to identify the most relevant document sections for any given query.

```python
# Semantic search using vector similarity
similarity = np.dot(query_vector, document_vector) / (np.linalg.norm(query_vector) * np.linalg.norm(document_vector))
```

### Prompt Engineering
Carefully crafted prompts with context management that guide the language model to produce accurate, contextually relevant responses based on retrieved document sections.

### Structured Output Generation
Specialized prompting techniques to generate consistent JSON responses for quiz questions, ensuring valid structure and data integrity.

## 📊 Business Applications

The GenAI PDF Q&A Bot offers transformative capabilities across multiple domains:

### Education
- Automated study guide creation from textbooks and lecture notes
- Personalized learning through targeted questioning
- Exam preparation with custom quizzes
- Teaching assistant for answering student questions

### Enterprise
- Knowledge base interrogation for policy and procedure documents
- Training material conversion into interactive learning tools
- Legal document analysis and contract review
- Research and development knowledge management

### Research
- Scientific literature question answering
- Research paper summarization and key finding extraction
- Cross-document knowledge synthesis
- Hypothesis testing against published literature

## 🛠️ Technical Details

For a deeper understanding of the system architecture, please see our [Technical Architecture Overview](docs/architecture/technical-overview.md).

## 🔧 Setup and Installation

### Quick Start

1. Clone the repository
2. Install dependencies with `pip install -r requirements.txt`
3. Configure your `.env` file:
   ```
   # Required: Your OpenAI API key
   OPENAI_API_KEY=your_api_key_here

   # Optional: Database configuration (defaults to SQLite if not specified)
   DATABASE_URL=postgresql://username:password@localhost/pdf_qa_bot

   # Optional: Model selection (defaults shown)
   OPENAI_MODEL=gpt-4o-mini
   EMBEDDING_MODEL=text-embedding-3-small
   ```
4. Run database migrations with `alembic upgrade head`
5. Start the application with `uvicorn app.main:app --reload`

> **Database Note**: The application supports both PostgreSQL (recommended for production) and SQLite (simpler for development). If no DATABASE_URL is provided, it will default to using a local SQLite database.

For detailed setup instructions, particularly for students and new developers, please refer to our [Student Setup Guide](docs/guides/student-setup-guide.md).

## 📋 Usage Instructions

### User Authentication
```bash
# Register a new user
curl -X POST http://localhost:8000/api/auth/register -d '{"username":"user","password":"pass"}'

# Login to get JWT token
curl -X POST http://localhost:8000/api/auth/login -d '{"username":"user","password":"pass"}'
```

### Document Management
```bash
# Upload a PDF (replace TOKEN with your JWT token)
curl -X POST -H "Authorization: Bearer TOKEN" \
  -F "file=@document.pdf" http://localhost:8000/api/upload
```

### Question Answering
```bash
# Ask a question about a document
curl -X POST -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" \
  -d '{"question":"What are the key concepts?","pdf_id":"YOUR_PDF_ID"}' \
  http://localhost:8000/api/ask
```

### Quiz Generation
```bash
# Generate a quiz from a document
curl -X POST -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" \
  -d '{"pdf_id":"YOUR_PDF_ID","num_questions":5}' \
  http://localhost:8000/api/quiz/generate
```

## 🐋 Docker Deployment

```bash
# Build and run with Docker
docker build -t genai-pdf-qa-bot .
docker run -p 8000:8000 -e OPENAI_API_KEY=your-key genai-pdf-qa-bot
```

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📁 Project Structure

```
.
├── app/               # Application code
│   ├── main.py        # Entry point
│   ├── database.py    # Database connection and models
│   ├── routes/        # API endpoints
│   │   ├── pdf_routes.py
│   │   └── quiz_routes.py
│   └── services/      # Business logic
│       ├── embedding.py     # Vector embedding generation
│       ├── llm.py          # Language model interaction
│       └── retriever.py    # Document storage and retrieval
├── docs/              # Documentation
│   ├── architecture/  # System design docs
│   ├── bug-reports/   # Bug documentation
│   └── guides/        # User and developer guides
├── migrations/        # Alembic database migrations
├── models/            # Data models
├── templates/         # Frontend templates
├── static/            # Static assets
│   ├── css/           # Stylesheets
│   ├── js/            # JavaScript files
│   └── images/        # Image assets
└── tests/             # Unit and integration tests
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

> "Transforming static documents into interactive knowledge through the power of AI."
