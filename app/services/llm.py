import os
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class LLMService:
    """Service for interacting with OpenAI's language models."""

    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize the LLM service.

        Args:
            model: The OpenAI model to use
        """
        self.model = model
        if not client.api_key:
            raise ValueError("OpenAI API key is not set")

    def _format_context(self, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Format the context chunks into a string for the prompt.

        Args:
            context_chunks: List of context chunks with metadata

        Returns:
            Formatted context string
        """
        formatted_contexts = []

        for i, chunk in enumerate(context_chunks):
            formatted_chunk = (
                f"[DOCUMENT CHUNK {i+1}] Page {chunk.get('page_number', 'unknown')}\n"
                f"{chunk.get('text', '')}\n"
            )
            formatted_contexts.append(formatted_chunk)

        return "\n".join(formatted_contexts)

    def _create_prompt(self, question: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Create a prompt for the language model.

        Args:
            question: The user's question
            context_chunks: List of relevant context chunks

        Returns:
            Formatted prompt string
        """
        formatted_context = self._format_context(context_chunks)

        prompt = f"""You are a helpful AI assistant tasked with answering questions about a PDF document.
Answer the question based ONLY on the provided document chunks below. Be concise and accurate.
If the information to answer the question is not contained in the document chunks, respond with
"I cannot answer this question based on the provided document."

Document chunks for context:
{formatted_context}

Question: {question}

Answer:"""

        return prompt

    async def generate_answer(self, question: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Generate an answer using the OpenAI API.

        Args:
            question: The user's question
            context_chunks: Relevant document chunks for context

        Returns:
            Generated answer
        """
        prompt = self._create_prompt(question, context_chunks)

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant answering questions about PDF documents."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )

        return response.choices[0].message.content