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

# Database file paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_DIR = BASE_DIR / "db"
USERS_FILE = DB_DIR / "users.json"
PDFS_DIR = DB_DIR / "pdfs"

# Create database directories if they don't exist
DB_DIR.mkdir(exist_ok=True)
PDFS_DIR.mkdir(exist_ok=True)

# Initialize empty users database if it doesn't exist
if not USERS_FILE.exists():
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)


def get_users_db():
    """Get the users database from the JSON file."""
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_users_db(users_db):
    """Save the users database to the JSON file."""
    with open(USERS_FILE, "w") as f:
        json.dump(users_db, f, indent=2)


def verify_password(plain_password, hashed_password):
    """Verify if the plain password matches the hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Generate a hashed password."""
    return pwd_context.hash(password)


def get_user(username: str):
    """Get a user by username or email."""
    users_db = get_users_db()
    # Check if username exists directly
    if username in users_db:
        user_data = users_db[username]
        user_data["username"] = username
        return user_data

    # Check if email matches any user
    for user_name, user_data in users_db.items():
        if user_data.get("email") == username:
            user_data["username"] = user_name
            return user_data

    return None


def authenticate_user(username: str, password: str):
    """Authenticate a user with username/email and password."""
    user = get_user(username)
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


async def get_current_user(token: str = Depends(oauth2_scheme)):
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

    user = get_user(username)
    if user is None:
        raise credentials_exception

    return user


# PDF Management Functions
def get_user_pdf_path(user_id: str):
    """Get the path to a user's PDF storage directory."""
    user_pdf_dir = PDFS_DIR / user_id
    user_pdf_dir.mkdir(exist_ok=True)
    return user_pdf_dir


def get_user_pdf_info_path(user_id: str):
    """Get the path to a user's PDF info file."""
    return get_user_pdf_path(user_id) / "pdf_info.json"


def get_user_pdfs(user_id: str) -> Dict[str, PDFInfo]:
    """Get all PDFs info for a user."""
    pdf_info_path = get_user_pdf_info_path(user_id)

    if not pdf_info_path.exists():
        return {}

    try:
        with open(pdf_info_path, "r") as f:
            pdf_info_dict = json.load(f)

        # Convert json to PDFInfo objects
        result = {}
        for pdf_id, info in pdf_info_dict.items():
            # Convert conversation history items
            conversations = []
            for convo in info.get("conversation_history", []):
                conversations.append(ConversationItem(**convo))

            # Create PDFInfo object
            result[pdf_id] = PDFInfo(
                pdf_id=pdf_id,
                filename=info["filename"],
                upload_date=info["upload_date"],
                num_pages=info["num_pages"],
                num_chunks=info["num_chunks"],
                conversation_history=conversations
            )

        return result
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_user_pdfs(user_id: str, pdfs: Dict[str, PDFInfo]):
    """Save PDF info for a user."""
    pdf_info_path = get_user_pdf_info_path(user_id)

    # Convert PDFInfo objects to dictionaries
    pdf_dict = {}
    for pdf_id, pdf_info in pdfs.items():
        pdf_dict[pdf_id] = pdf_info.dict()

    with open(pdf_info_path, "w") as f:
        json.dump(pdf_dict, f, indent=2)


def add_conversation_to_pdf(
    user_id: str,
    pdf_id: str,
    question: str,
    answer: str,
    sources: list
):
    """Add a conversation item to a PDF's history."""
    pdfs = get_user_pdfs(user_id)

    if pdf_id not in pdfs:
        return False

    # Create conversation item
    convo_item = ConversationItem(
        question=question,
        answer=answer,
        timestamp=datetime.now().isoformat(),
        sources=sources
    )

    # Add to PDF's conversation history
    pdf_info = pdfs[pdf_id]
    if not hasattr(pdf_info, "conversation_history") or pdf_info.conversation_history is None:
        pdf_info.conversation_history = []

    pdf_info.conversation_history.append(convo_item)

    # Save updated PDFs
    save_user_pdfs(user_id, pdfs)

    return True