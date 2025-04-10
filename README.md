# 🧠 GenAI PDF Q&A Bot

This project is a **GPT-powered question-answering assistant** for PDF documents.
Built with `FastAPI`, `OpenAI API`, and `FAISS`, it allows users to upload a PDF and ask natural-language questions about its content.

Designed for:
- 🔍 Personal document understanding
- 🧑‍🏫 Teaching demo for LLMs, embeddings, and RAG
- 💸 Monetizable template for platforms like Gumroad or Hugging Face Spaces

---

## 🚀 Features

- Upload a PDF and extract its text
- Chunk and embed using `text-embedding-3-small` (improved embedding model)
- Store vectors in FAISS (in-memory)
- Accept user questions via `/ask` endpoint or simple UI
- Retrieve top-k relevant chunks and pass to GPT-4o-mini (affordable but powerful)
- Return answers with source excerpts and page numbers
- Optional: stream answers or summarize entire PDFs

---

## 📋 Setup Instructions

### Prerequisites

- Python 3.9+ installed
- OpenAI API key ([get one here](https://platform.openai.com/account/api-keys))
- Git (for cloning the repository)

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/genai-pdf-qa-bot.git
cd genai-pdf-qa-bot
```

### Step 2: Set Up Environment

1. Create a virtual environment (recommended):
   ```bash
   python -m venv venv

   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   # Copy the example environment file
   cp .env.example .env

   # Edit the .env file and add your OpenAI API key
   # OPENAI_API_KEY=your-api-key-here
   ```

### Step 3: Run the Application

```bash
uvicorn app.main:app --reload
```

The application will be available at http://localhost:8000, with API documentation at http://localhost:8000/docs

---

## 🧑‍💻 How to Use

### Method 1: Using the Swagger UI (Recommended for beginners)

1. Open your browser and go to http://localhost:8000/docs
2. Expand the `/api/upload` endpoint
3. Click "Try it out" and upload a PDF file
4. Note the `pdf_id` returned in the response
5. Expand the `/api/ask` endpoint
6. Enter your question and the `pdf_id` from step 4
7. Click "Execute" to get your answer

### Method 2: Using cURL or Postman

#### Upload a PDF:
```bash
curl -X 'POST' \
  'http://localhost:8000/api/upload' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@path/to/your/document.pdf'
```

#### Ask a question:
```bash
curl -X 'POST' \
  'http://localhost:8000/api/ask' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "question": "What is the main topic of this document?",
  "pdf_id": "your-pdf-id-here"
}'
```

### Response Format

The `/ask` endpoint returns:
- The generated answer
- Source chunks that were used with page numbers
- Relevance scores for each chunk
- Processing time

---

## 🐋 Docker Deployment

Build and run with Docker:

```bash
# Build the Docker image
docker build -t genai-pdf-qa-bot .

# Run the container
docker run -p 8000:8000 -e OPENAI_API_KEY=your-api-key genai-pdf-qa-bot
```

---

## 🧱 Tech Stack

- `FastAPI` for API layer
- `PyMuPDF` for text extraction
- `OpenAI API` (embeddings + completions)
- `FAISS` for local vector store
- `Docker` for deployment
- `GitHub Actions` for CI
- Designed to deploy on:
  - Hugging Face Spaces (Docker)
  - Railway or AWS Lambda

---

## 📁 Project Structure

```bash
.
├── app/
│   ├── main.py               # FastAPI app
│   ├── routes/
│   │   └── pdf_routes.py     # Upload and Q&A endpoint
│   └── services/
│       ├── embedding.py      # OpenAI embedding logic
│       ├── retriever.py      # FAISS setup and query
│       └── llm.py            # GPT prompt formatting & call
├── models/
│   └── pydantic_schemas.py   # Request/response models
├── tests/
│   └── test_endpoints.py     # Optional test coverage
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## ✨ Credits

Inspired by OpenAI + FAISS + LangChain RAG architecture, this bot is part of my [ML Engineer Fast Track](https://github.com/VictorCabrejos) journey to build monetizable, deployable GenAI tools.

---

> "From Philly to Lima to Lambda — teaching the world how real AI gets built."
