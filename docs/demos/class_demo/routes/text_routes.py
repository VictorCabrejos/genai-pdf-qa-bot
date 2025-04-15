# \routes\text_routes.py
from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import re
import uuid
from services.text.extractor import TextExtractor
from services.text.extractor import SentenceSplitter

router = APIRouter()

textextractor = TextExtractor()
sentencesplitter = SentenceSplitter()

@router.post("/upload-text")
async def upload_text_file(file: UploadFile = File(...)):
    """Sube un archivo de texto, extrae y divide en frases."""
    try:
        # Leer el contenido del archivo
        file_content = await file.read()

        # Extraer texto del archivo
        text = textextractor.extract_text_from_file(file_content)

        # Generar un ID único para este archivo
        file_id = str(uuid.uuid4())

        # Dividir el texto en frases
        sentences = sentencesplitter.split_into_sentences(text)

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

