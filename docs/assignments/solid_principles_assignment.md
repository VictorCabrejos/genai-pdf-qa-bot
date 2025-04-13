# Tarea: Refactorización siguiendo los Principios SOLID

## Descripción General

En esta tarea, identificarás violaciones a los principios SOLID en el código actual de nuestra aplicación GENAI-PDF-QA-BOT y propondrás refactorizaciones simples para corregirlas. El objetivo es mejorar la calidad del código aplicando los principios SOLID que hemos aprendido en clase.

## Instrucciones

1. Trabajarás en grupos asignados.
2. A cada grupo se le asignará **UNO** de los escenarios descritos a continuación.
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

El sistema de autenticación tiene código duplicado en las rutas de login como puedes ver a continuación. Observa cómo las dos funciones (`login_for_access_token` y `login_json`) contienen casi exactamente el mismo código para autenticar usuarios y generar tokens:

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

**Tarea**: Refactoriza este código para eliminar la duplicación, aplicando el Principio de Responsabilidad Única (SRP) de SOLID.

**Pistas**:
1. El principio DRY (Don't Repeat Yourself - No te repitas) no es parte de SOLID, pero es un principio complementario que promueve la eliminación de duplicación de código. Al eliminar esta duplicación, estarás mejorando la aplicación del SRP.
2. La duplicación específica está en el proceso de autenticación y creación del token, que se repite en ambas funciones.
3. Crea un archivo `app/auth/services/auth_service.py` con una clase `AuthService` que contenga el método común de autenticación.
4. Modifica `routes.py` para usar esta nueva clase y reducir la duplicación.

## Criterios de evaluación

1. Correcta identificación de los principios SOLID violados (30%)
2. Claridad y simplicidad de la solución propuesta (40%)
3. Implementación funcional de los cambios (20%)
4. Explicación del enfoque y aprendizajes (10%)

## Fecha de entrega

La tarea debe ser entregada a más tardar el domingo 20 de abril de 2025 a las 11:00 AM.

## Recursos adicionales

- [Tutorial sobre principios SOLID en Python](https://realpython.com/solid-principles-python/)
- [Ejemplos de refactorización en Python](https://refactoring.guru/refactoring/examples/python)