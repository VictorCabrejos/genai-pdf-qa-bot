# services\text\splitter.py

class SentenceSplitter:
    """Clase responsable de dividir texto en frases"""

    def __init__(self, min_length: int = 20):
        self.min_length = min_length


    def split_into_sentences(text: str) -> List[Dict[str, Any]]:
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