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
- Chunk and embed using `text-embedding-ada-002`
- Store vectors in FAISS (in-memory)
- Accept user questions via `/ask` endpoint or simple UI
- Retrieve top-k relevant chunks and pass to GPT-4o (or GPT-3.5)
- Return answers with source excerpts
- Optional: stream answers or summarize entire PDFs

---

## 🧱 Tech Stack

- `FastAPI` for API layer
- `PyMuPDF` or `pdfplumber` for text extraction
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

## 🛠️ To Do

- [ ] Set up repo and add file structure
- [ ] Paste prompt into VS Code Agent to scaffold full project
- [ ] Add .env config for API keys
- [ ] Deploy to Hugging Face Spaces or Railway
- [ ] Record short walkthrough (optional for Udemy)

---

## ✨ Credits

Inspired by OpenAI + FAISS + LangChain RAG architecture, this bot is part of my [ML Engineer Fast Track](https://github.com/VictorCabrejos) journey to build monetizable, deployable GenAI tools.

---

> “From Philly to Lima to Lambda — teaching the world how real AI gets built.”
