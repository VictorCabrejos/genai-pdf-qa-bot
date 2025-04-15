# services\text\extractor.py

class TextExtractor:
    """Clase responsable de extraer texto de archivos."""

    def extract_text_from_file(file_content: bytes) -> str:
        """Extrae el texto de un archivo."""
        try:
            return file_content.decode('utf-8')
        except UnicodeDecodeError:
            # Intentar con otra codificación si utf-8 falla
            return file_content.decode('latin-1')