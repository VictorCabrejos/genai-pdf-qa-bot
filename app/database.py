import os
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json

# Check if we're using PostgreSQL or SQLite (fallback for local development)
USE_POSTGRES = os.getenv("USE_POSTGRES", "false").lower() == "true"
DATABASE_URL = os.getenv("DATABASE_URL")

if USE_POSTGRES and DATABASE_URL:
    # Using PostgreSQL
    engine = create_engine(DATABASE_URL)
else:
    # Using SQLite as fallback for local development
    engine = create_engine("sqlite:///./pdf_qa.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define database models
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    pdfs = relationship("PDF", back_populates="user")

class PDF(Base):
    __tablename__ = "pdfs"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    title = Column(String)
    filename = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    chunks = relationship("PDFChunk", back_populates="pdf")
    user = relationship("User", back_populates="pdfs")
    file_path = Column(String)  # Store the path where the file is saved (could be S3 URL in the future)

class PDFChunk(Base):
    __tablename__ = "pdf_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pdf_id = Column(String, ForeignKey("pdfs.id"))
    content = Column(Text)
    page_number = Column(Integer)
    embedding_file = Column(String, nullable=True)  # Path to embedding file (could be replaced with actual embeddings)
    pdf = relationship("PDF", back_populates="chunks")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    pdf_id = Column(String, ForeignKey("pdfs.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    is_user = Column(Boolean, default=True)  # True if user message, False if AI message
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    conversation = relationship("Conversation", back_populates="messages")

class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(String, primary_key=True)
    pdf_id = Column(String, ForeignKey("pdfs.id"))
    user_id = Column(String, ForeignKey("users.id"))
    title = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    questions = Column(JSON)  # Store questions as JSON

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)

# Get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()