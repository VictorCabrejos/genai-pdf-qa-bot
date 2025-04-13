# Tarea: Refactorización siguiendo los Principios SOLID

## Descripción General

En esta tarea, identificarás violaciones a los principios SOLID en el código actual de nuestra aplicación GENAI-PDF-QA-BOT y propondrás refactorizaciones para corregirlas. El objetivo es mejorar la calidad del código siguiendo las mejores prácticas de diseño orientado a objetos.

## Instrucciones

1. Trabajarás en grupos de dos personas.
2. Cada grupo debe seleccionar **UNO** de los tres escenarios descritos a continuación.
3. Para el escenario seleccionado:
   - Identifica qué principios SOLID se están violando
   - Explica por qué constituyen una violación
   - Propón una refactorización que corrija estas violaciones sin romper la funcionalidad existente
   - Implementa tu solución en un archivo separado o rama de git
   - Escribe un breve informe explicando tu enfoque y los cambios realizados

## Escenarios

### Escenario 1: Servicio de Procesamiento de PDF (`app/routes/pdf_routes.py`)

El archivo `pdf_routes.py` contiene funciones para cargar PDFs, extraer texto, dividirlo en fragmentos y más. Actualmente, todas estas responsabilidades están mezcladas dentro del archivo de rutas.

Partes relevantes del código:

```python
# En app/routes/pdf_routes.py
def extract_text_from_pdf(pdf_file: bytes) -> List[str]:
    """Extract text content from PDF file."""
    pdf_document = fitz.open(stream=pdf_file, filetype="pdf")
    pages = []
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        pages.append(page.get_text())
    pdf_document.close()
    return pages

def chunk_text(pages: List[str], chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
    """Split text into overlapping chunks."""
    chunks = []
    for page_num, page_text in enumerate(pages):
        # Split page text into chunks
        start = 0
        while start < len(page_text):
            end = start + chunk_size
            if end > len(page_text):
                end = len(page_text)
                # If this is the last chunk and it's too small, merge with previous chunk
                if end - start < chunk_size // 2 and chunks:
                    chunks[-1]["text"] += " " + page_text[start:end].strip()
                    break

            chunk_text = page_text[start:end].strip()

            if chunk_text:  # Skip empty chunks
                chunk = {
                    "text": chunk_text,
                    "page_number": page_num + 1
                }
                chunks.append(chunk)

            # Move start position for next chunk, accounting for overlap
            start = end - overlap
            if start < 0:
                start = 0

    return chunks

@router.post("/upload", response_model=PDFUploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload a PDF file, extract and chunk text, create embeddings."""
    try:
        start_time = time.time()

        # Read file content
        pdf_content = await file.read()

        # Extract text from PDF
        pages = extract_text_from_pdf(pdf_content)

        # Generate a unique ID for this PDF
        pdf_id = str(uuid.uuid4())

        # Chunk text into smaller segments
        chunks = chunk_text(pages)

        # Create embeddings for each chunk
        chunks_with_metadata = []
        for i, chunk in enumerate(chunks):
            embedding = embedding_service.get_embedding(chunk["text"])
            chunk_with_metadata = {
                "chunk_id": str(i),
                "text": chunk["text"],
                "page_number": chunk["page_number"],
                "embedding": embedding
            }
            chunks_with_metadata.append(chunk_with_metadata)

        # Create PDF metadata
        pdf_metadata = {
            "pdf_id": pdf_id,
            "filename": file.filename,
            "upload_date": datetime.now().isoformat(),
            "num_pages": len(pages),
            "num_chunks": len(chunks_with_metadata)
        }

        # Save PDF information to user's library
        save_path = await get_user_pdf_path(current_user, pdf_id)

        # Ensure directory exists
        os.makedirs(save_path, exist_ok=True)

        # Save chunks with embeddings
        with open(os.path.join(save_path, "chunks.json"), "w") as f:
            json.dump(chunks_with_metadata, f)

        # Save PDF info
        with open(os.path.join(save_path, "pdf_info.json"), "w") as f:
            json.dump(pdf_metadata, f)

        # Update user's PDFs list
        await add_pdf_to_user(current_user, pdf_id, file.filename)

        processing_time = time.time() - start_time

        return PDFUploadResponse(
            pdf_id=pdf_id,
            filename=file.filename,
            num_pages=len(pages),
            num_chunks=len(chunks_with_metadata),
            processing_time=processing_time
        )

    except Exception as e:
        print(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
```

**Tarea**: Identifica qué principios SOLID se están violando y refactoriza este código para separar las distintas responsabilidades en clases apropiadas.

### Escenario 2: Servicios de IA en Rutas (`app/routes/quiz_routes.py`)

El archivo `quiz_routes.py` inicializa y utiliza servicios directamente, creando un acoplamiento fuerte:

```python
# En app/routes/quiz_routes.py
# Initialize services with explicit error handling
try:
    llm_service = LLMService()
    logger.debug(f"LLM service initialized with model: {llm_service.model}")
    # Check if we can access the OpenAI API key (using the get_llm_client function)
    client = get_llm_client()
    logger.debug(f"LLM client API key exists: {bool(client.api_key)}")
except Exception as e:
    logger.critical(f"Failed to initialize LLM service: {str(e)}")
    logger.critical(traceback.format_exc())
    llm_service = None

try:
    retriever = Retriever()
    logger.debug(f"Retriever service initialized with pdfs_dir: {retriever.pdfs_dir}")
except Exception as e:
    logger.critical(f"Failed to initialize Retriever service: {str(e)}")
    logger.critical(traceback.format_exc())
    retriever = None

@router.post("/generate")
async def generate_quiz(
    request: QuizRequest = Body(...),
    current_user: dict = Depends(get_current_user)  # Add authentication dependency
):
    """Generate a quiz from a PDF document."""

    if not llm_service:
        raise HTTPException(status_code=500, detail="LLM service is not available")

    if not retriever:
        raise HTTPException(status_code=500, detail="Retriever service is not available")

    try:
        start_time = time.time()

        # Get PDF content chunks to generate questions from
        retrieval_results = await retriever.get_chunks_by_pdf_id(
            request.pdf_id,
            current_user["username"]
        )

        # Format the content for the LLM
        pdf_content = "\n\n".join([chunk["text"] for chunk in retrieval_results])

        # Generate quiz using LLM service
        if not pdf_content:
            raise HTTPException(status_code=404, detail="No content found in PDF")

        quiz_data = llm_service.generate_quiz(
            pdf_content,
            request.num_questions,
            request.question_type
        )

        # Process and return the quiz data
        end_time = time.time()
        generation_time = end_time - start_time

        return {
            "quiz_id": str(uuid.uuid4()),
            "questions": quiz_data,
            "pdf_id": request.pdf_id,
            "generation_time": generation_time
        }

    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error generating quiz: {str(e)}")
```

**Tarea**: Identifica qué principios SOLID se están violando y refactoriza este código para reducir el acoplamiento e implementar una mejor inyección de dependencias.

### Escenario 3: Autenticación de Usuarios (`app/auth/routes.py`)

El sistema de autenticación actual tiene varios métodos mezclados:

```python
# En app/auth/routes.py
@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    """Register a new user"""
    users_db = get_users_db()

    # Check if username already exists
    if user.username in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists
    for existing_user in users_db.values():
        if existing_user.get("email") == user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    # Create new user with hashed password
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user.password)

    users_db[user.username] = {
        "user_id": user_id,
        "email": user.email,
        "full_name": user.full_name,
        "hashed_password": hashed_password,
        "pdfs": []
    }

    save_users_db(users_db)

    return {
        "user_id": user_id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name
    }

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and provide access token"""
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token with expiration time
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/json", response_model=Token)
async def login_json(user_data: UserLogin):
    """Authenticate user with JSON request and provide access token"""
    user = authenticate_user(user_data.username, user_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token with expiration time
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}
```

**Tarea**: Identifica qué principios SOLID se están violando y refactoriza el código para mejorar la cohesión, reducir la duplicación y permitir diferentes estrategias de autenticación en el futuro.

## Criterios de evaluación

1. Correcta identificación de los principios SOLID violados (30%)
2. Calidad de la solución propuesta (40%)
3. Implementación funcional de los cambios (20%)
4. Claridad en la explicación del enfoque (10%)

## Fecha de entrega

La tarea debe ser entregada a más tardar el 27 de abril de 2025.

## Recursos adicionales

- [Tutorial sobre principios SOLID en Python](https://realpython.com/solid-principles-python/)
- [Ejemplos de refactorización en Python](https://refactoring.guru/refactoring/examples/python)