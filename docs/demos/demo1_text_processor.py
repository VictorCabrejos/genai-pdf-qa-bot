from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import re
import uuid
from typing import List, Dict, Any

router = APIRouter()

def extract_text_from_file(file_content: bytes) -> str:
    """Extrae el texto de un archivo."""
    try:
        return file_content.decode('utf-8')
    except UnicodeDecodeError:
        # Intentar con otra codificación si utf-8 falla
        return file_content.decode('latin-1')

def split_into_sentences(text: str, min_length: int = 20) -> List[Dict[str, Any]]:
    """Divide el texto en frases."""
    # Patrón simple para dividir por puntos, exclamaciones o interrogaciones
    sentence_endings = r'[.!?]'
    raw_sentences = re.split(sentence_endings, text)

    sentences = []
    for i, sentence in enumerate(raw_sentences):
        sentence = sentence.strip()
        # Omitir frases muy cortas
        if len(sentence) >= min_length:
            sentence_obj = {
                "id": i,
                "text": sentence,
                "length": len(sentence)
            }
            sentences.append(sentence_obj)

    return sentences

@router.post("/upload-text")
async def upload_text_file(file: UploadFile = File(...)):
    """Sube un archivo de texto, extrae y divide en frases."""
    try:
        # Leer el contenido del archivo
        file_content = await file.read()

        # Extraer texto del archivo
        text = extract_text_from_file(file_content)

        # Generar un ID único para este archivo
        file_id = str(uuid.uuid4())

        # Dividir el texto en frases
        sentences = split_into_sentences(text)

        # Crear metadata
        file_metadata = {
            "file_id": file_id,
            "filename": file.filename,
            "total_sentences": len(sentences)
        }

        # Guardar el resultado (simulado)
        output_dir = f"./processed/{file_id}"
        os.makedirs(output_dir, exist_ok=True)

        # Simular guardado del resultado
        print(f"Guardando {len(sentences)} frases en {output_dir}")

        return {
            "file_id": file_id,
            "filename": file.filename,
            "num_sentences": len(sentences),
            "first_sentence": sentences[0]["text"] if sentences else ""
        }

    except Exception as e:
        print(f"Error procesando archivo de texto: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando archivo: {str(e)}")