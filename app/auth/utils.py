from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os
import uuid
import json
from pathlib import Path
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from ..database import get_db, User, PDF, PDFChunk, Conversation, Message, Quiz
from models.pydantic_schemas import UserResponse, PDFInfo, ConversationItem

# Load environment variables
load_dotenv()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_please_change_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# Base directory for file storage (used for PDF files)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PDFS_DIR = BASE_DIR / "db" / "pdfs"
PDFS_DIR.mkdir(exist_ok=True, parents=True)

# Database functions using SQLAlchemy
def verify_password(plain_password, hashed_password):
    """Verify if the plain password matches the hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Generate a hashed password."""
    return pwd_context.hash(password)

def get_user_by_username(db: Session, username: str):
    """Get a user by username from the database."""
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    """Get a user by email from the database."""
    return db.query(User).filter(User.email == email).first()

def get_user(username: str, db: Session = Depends(get_db)):
    """Get a user by username or email from the database."""
    # Check if username exists directly
    user = get_user_by_username(db, username)
    if user:
        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "hashed_password": user.password,
            "full_name": user.username  # Add a full_name field to User model if needed
        }

    # Check if email matches any user
    user = get_user_by_email(db, username)
    if user:
        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "hashed_password": user.password,
            "full_name": user.username  # Add a full_name field to User model if needed
        }

    return None

def create_user_db(db: Session, username: str, email: str, password: str, full_name: str = None):
    """Create a new user in the database."""
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(password)

    user = User(
        id=user_id,
        username=username,
        email=email,
        password=hashed_password
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

def authenticate_user(username: str, password: str, db: Session = Depends(get_db)):
    """Authenticate a user with username/email and password."""
    user = get_user(username, db)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Get the current authenticated user from the JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user(username, db)
    if user is None:
        raise credentials_exception

    return user

# PDF Management Functions
def get_user_pdf_path(user_id: str):
    """Get the path to a user's PDF storage directory."""
    user_pdf_dir = PDFS_DIR / user_id
    user_pdf_dir.mkdir(exist_ok=True)
    return user_pdf_dir

def get_user_pdfs(user_id: str, db: Session = Depends(get_db)) -> Dict[str, PDFInfo]:
    """Get all PDFs info for a user from the database."""
    # Add debug logging
    pdfs = db.query(PDF).filter(PDF.user_id == user_id).all()
    print(f"Found {len(pdfs)} PDFs for user {user_id}")

    result = {}
    for pdf in pdfs:
        print(f"Processing PDF: {pdf.id}, {pdf.filename}")
        # Get conversations for this PDF
        conversations = []
        db_conversations = db.query(Conversation).filter(Conversation.pdf_id == pdf.id).all()

        for convo in db_conversations:
            messages = db.query(Message).filter(Message.conversation_id == convo.id).order_by(Message.timestamp).all()

            # Group messages into question/answer pairs
            for i in range(0, len(messages), 2):
                if i + 1 < len(messages):
                    question = messages[i].content
                    answer = messages[i+1].content

                    conversations.append(ConversationItem(
                        question=question,
                        answer=answer,
                        timestamp=messages[i].timestamp.isoformat(),
                        sources=[]  # Sources handling would need additional implementation
                    ))

        # Count chunks
        num_chunks = db.query(PDFChunk).filter(PDFChunk.pdf_id == pdf.id).count()

        # Calculate num_pages by counting unique page numbers in chunks
        distinct_pages = db.query(PDFChunk.page_number).filter(PDFChunk.pdf_id == pdf.id).distinct().count()
        # Use at least 1 page if no chunks have page numbers
        num_pages = max(1, distinct_pages)

        result[pdf.id] = PDFInfo(
            pdf_id=pdf.id,
            filename=pdf.filename,
            upload_date=pdf.created_at.isoformat(),
            num_pages=num_pages,
            num_chunks=num_chunks,
            conversation_history=conversations
        )

    return result

def add_conversation_to_pdf(
    user_id: str,
    pdf_id: str,
    question: str,
    answer: str,
    sources: list,
    db: Session = Depends(get_db)
):
    """Add a conversation item to a PDF's history in the database."""
    # Check if PDF exists and belongs to the user
    pdf = db.query(PDF).filter(PDF.id == pdf_id, PDF.user_id == user_id).first()
    if not pdf:
        return False

    # Create a new conversation
    conversation_id = str(uuid.uuid4())
    conversation = Conversation(
        id=conversation_id,
        user_id=user_id,
        pdf_id=pdf_id
    )
    db.add(conversation)

    # Add question message
    question_msg = Message(
        conversation_id=conversation_id,
        is_user=True,
        content=question
    )
    db.add(question_msg)

    # Add answer message
    answer_msg = Message(
        conversation_id=conversation_id,
        is_user=False,
        content=answer
    )
    db.add(answer_msg)

    db.commit()

    return True