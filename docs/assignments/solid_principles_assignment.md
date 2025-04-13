# Tarea: Refactorización siguiendo los Principios SOLID

## Descripción General

En esta tarea, identificarás violaciones a los principios SOLID en el código actual de nuestra aplicación GENAI-PDF-QA-BOT y propondrás refactorizaciones simples para corregirlas. El objetivo es mejorar la calidad del código aplicando los principios SOLID que hemos aprendido en clase.

## Instrucciones

1. Trabajarás en grupos de dos personas.
2. Cada grupo debe seleccionar **UNO** de los tres escenarios descritos a continuación.
3. Para el escenario seleccionado:
   - Identifica qué principios SOLID se están violando (máximo 2 principios)
   - Explica por qué constituyen una violación
   - Implementa una solución sencilla siguiendo las pistas proporcionadas
   - Escribe un breve informe explicando tu enfoque y los cambios realizados

## Escenarios

### Escenario 1: Procesamiento de PDF (`app/routes/pdf_routes.py`)

El archivo `pdf_routes.py` contiene funciones que mezclan responsabilidades de extracción de texto de PDFs y segmentación de texto.

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
```

**Tarea**: Refactoriza estas dos funciones aplicando el Principio de Responsabilidad Única (SRP).

**Pistas**:
1. Crea un archivo `app/services/pdf/extractor.py` con una clase `PDFExtractor` que maneje la extracción de texto.
2. Crea un archivo `app/services/pdf/chunker.py` con una clase `TextChunker` que maneje la división del texto en fragmentos.
3. Modifica `pdf_routes.py` para usar estas nuevas clases en lugar de las funciones directas.

### Escenario 2: Duplicación de Código en Autenticación (`app/auth/routes.py`)

El sistema de autenticación tiene código duplicado en las rutas de login:

```python
# En app/auth/routes.py
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

**Tarea**: Refactoriza este código para eliminar la duplicación, aplicando el Principio DRY y mejorando SRP.

**Pistas**:
1. Crea un archivo `app/auth/services/auth_service.py` con una clase `AuthService` que contenga el método común de autenticación.
2. Modifica `routes.py` para usar esta nueva clase y reducir la duplicación.

### Escenario 3: Acoplamiento entre componentes (`app/routes/quiz_routes.py`)

El archivo `quiz_routes.py` tiene un fuerte acoplamiento con las implementaciones de servicios:

```python
# En app/routes/quiz_routes.py (versión simplificada)
# Inicialización directa de servicios
try:
    llm_service = LLMService()
    logger.debug(f"LLM service initialized with model: {llm_service.model}")
except Exception as e:
    logger.critical(f"Failed to initialize LLM service: {str(e)}")
    llm_service = None

try:
    retriever = Retriever()
    logger.debug(f"Retriever service initialized with pdfs_dir: {retriever.pdfs_dir}")
except Exception as e:
    logger.critical(f"Failed to initialize Retriever service: {str(e)}")
    retriever = None

@router.post("/generate")
async def generate_quiz(request: QuizRequest = Body(...), current_user: dict = Depends(get_current_user)):
    if not llm_service:
        raise HTTPException(status_code=500, detail="LLM service is not available")
    if not retriever:
        raise HTTPException(status_code=500, detail="Retriever service is not available")

    # Uso directo de las instancias de servicio
    retrieval_results = await retriever.get_chunks_by_pdf_id(request.pdf_id, current_user["username"])
    pdf_content = "\n\n".join([chunk["text"] for chunk in retrieval_results])
    quiz_data = llm_service.generate_quiz(pdf_content, request.num_questions, request.question_type)

    # Resto del código...
```

**Tarea**: Refactoriza este código para reducir el acoplamiento aplicando el Principio de Inversión de Dependencias (DIP).

**Pistas**:
1. Crea un archivo `app/services/quiz/quiz_generator.py` con una clase `QuizGenerator` que reciba sus dependencias por inyección en el constructor.
2. Modifica `quiz_routes.py` para crear la instancia de `QuizGenerator` y pasar las dependencias.
3. No es necesario crear interfaces abstractas completas, solo enfócate en la inyección de dependencias.

## Criterios de evaluación

1. Correcta identificación de los principios SOLID violados (30%)
2. Claridad y simplicidad de la solución propuesta (40%)
3. Implementación funcional de los cambios (20%)
4. Explicación del enfoque y aprendizajes (10%)

## Fecha de entrega

La tarea debe ser entregada a más tardar el 27 de abril de 2025.

## Recursos adicionales

- [Tutorial sobre principios SOLID en Python](https://realpython.com/solid-principles-python/)
- [Ejemplos de refactorización en Python](https://refactoring.guru/refactoring/examples/python)