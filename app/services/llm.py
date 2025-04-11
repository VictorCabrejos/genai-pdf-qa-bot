import os
import json
import logging
import sys
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
import traceback
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("llm_service.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("llm_service")

# Get the absolute path to the root directory
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables with explicit path to .env file
load_dotenv(ROOT_DIR / '.env')

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Print a debug message to check if the API key is loaded
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    logger.info(f"API key loaded successfully: {api_key[:5]}...{api_key[-4:]}")
else:
    logger.warning("WARNING: API key not found in environment variables")

class LLMService:
    """Service for interacting with OpenAI's language models."""

    def __init__(self, model: str = None):
        """
        Initialize the LLM service.

        Args:
            model: The OpenAI model to use
        """
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        logger.info(f"Initialized LLMService with model: {self.model}")
        if not client.api_key:
            logger.error("OpenAI API key is not set. Please check your .env file.")
            raise ValueError("OpenAI API key is not set. Please check your .env file.")

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

    def _create_prompt(self, question: str, context_chunks: List[Dict[str, Any]], allow_interpretation: bool = False) -> str:
        """
        Create a prompt for the language model.

        Args:
            question: The user's question
            context_chunks: List of relevant context chunks
            allow_interpretation: Whether to allow some interpretation beyond the exact text

        Returns:
            Formatted prompt string
        """
        formatted_context = self._format_context(context_chunks)

        if allow_interpretation:
            prompt = f"""You are a helpful AI assistant tasked with answering questions about a PDF document.
Answer the question primarily based on the provided document chunks below. You may provide reasonable interpretations,
summaries, or inferences based on the content, but make it clear when you're going beyond what's explicitly stated.
Be concise and provide useful insights when possible.

If the document doesn't contain ANY information even remotely related to the question, respond with
"I cannot answer this question based on the provided document."

Document chunks for context:
{formatted_context}

Question: {question}

Answer:"""
        else:
            prompt = f"""You are a helpful AI assistant tasked with answering questions about a PDF document.
Answer the question based ONLY on the provided document chunks below. Be concise and accurate.
If the information to answer the question is not contained in the document chunks, respond with
"I cannot answer this question based on the provided document."

Document chunks for context:
{formatted_context}

Question: {question}

Answer:"""

        return prompt

    def _detect_interpretation_question(self, question: str) -> bool:
        """
        Detect if a question likely requires interpretation beyond the document.

        Args:
            question: The user's question

        Returns:
            True if the question likely needs interpretation
        """
        interpretation_indicators = [
            "do you think",
            "would you say",
            "in your opinion",
            "summarize",
            "summarise",
            "overview",
            "what's the main",
            "what is the main",
            "conclusion",
            "interpret",
            "analyze",
            "analyse",
            "evaluate",
            "assessment",
            "compare",
            "contrast",
            "relationship between",
            "significance of",
            "implications",
            "relate to",
            "align with",
            "how does this",
            "what does this mean"
        ]

        question_lower = question.lower()
        for indicator in interpretation_indicators:
            if indicator in question_lower:
                return True

        return False

    async def generate_answer(self, question: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Generate an answer using the OpenAI API.

        Args:
            question: The user's question
            context_chunks: Relevant document chunks for context

        Returns:
            Generated answer
        """
        # Detect if question likely needs interpretation
        allow_interpretation = self._detect_interpretation_question(question)

        prompt = self._create_prompt(question, context_chunks, allow_interpretation)

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

    async def generate_structured_response(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Generate a structured JSON response using the OpenAI API.

        Args:
            system_prompt: The system prompt for the LLM
            user_prompt: The user prompt for the LLM

        Returns:
            Parsed JSON response
        """
        response_text = "No response received"
        try:
            logger.info(f"Generating structured response with model: {self.model}")
            start_time = time.time()

            # Breaking up prompts if they're too long
            max_system_prompt_length = 3000
            max_user_prompt_length = 12000

            if len(system_prompt) > max_system_prompt_length:
                logger.warning(f"Truncating system prompt from {len(system_prompt)} chars to {max_system_prompt_length}")
                system_prompt = system_prompt[:max_system_prompt_length]

            if len(user_prompt) > max_user_prompt_length:
                logger.warning(f"Truncating user prompt from {len(user_prompt)} chars to {max_user_prompt_length}")
                # Keep the beginning and ending parts of the prompt
                # This is important for quiz generation where the JSON format instructions are at the end
                beginning = user_prompt[:max_user_prompt_length // 2]
                ending = user_prompt[-max_user_prompt_length // 2:]
                user_prompt = beginning + "\n\n[Content truncated due to length]\n\n" + ending

            logger.info(f"Prompt sizes - System: {len(system_prompt)}, User: {len(user_prompt)}")

            # Try with JSON format first
            try:
                logger.info("Attempting with response_format=json_object")
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.5,
                    max_tokens=4000,
                    response_format={"type": "json_object"}
                )
                logger.info("Successfully received response with json_object format")
            except Exception as e:
                logger.error(f"Failed with json_object format: {e}")
                logger.info("Falling back to standard completion without response_format")
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt + "\nRESPOND WITH VALID JSON ONLY."},
                        {"role": "user", "content": user_prompt + "\n\nRemember to respond with valid JSON only."}
                    ],
                    temperature=0.5,
                    max_tokens=4000
                )
                logger.info("Successfully received response with standard completion")

            response_text = response.choices[0].message.content
            request_time = time.time() - start_time
            logger.info(f"Response received in {request_time:.2f}s, length: {len(response_text)} characters")

            # Log a sample of the response for debugging
            sample_length = min(300, len(response_text))
            logger.info(f"Response preview: {response_text[:sample_length]}...")

            # Parse the response as JSON
            json_response = self._extract_and_validate_json(response_text)

            # If it's for a quiz, validate and fix the structure
            if "questions" in json_response:
                logger.info("Detected quiz structure, validating and fixing if needed")
                json_response = self._validate_and_fix_quiz(json_response)

            return json_response

        except Exception as e:
            logger.error(f"Unexpected error in generate_structured_response: {str(e)}")
            logger.error(traceback.format_exc())

            # Create a minimal valid response structure as fallback
            error_response = {
                "error": f"Error: {str(e)}",
                "raw_response": response_text[:500] + "...(truncated)" if len(response_text) > 500 else response_text
            }

            logger.error(f"Returning error response: {error_response['error']}")
            return error_response

    def _extract_and_validate_json(self, text: str) -> Dict[str, Any]:
        """Extract and validate JSON from model response text."""
        try:
            # First try direct parsing
            logger.info("Attempting to parse response as JSON directly")
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse response as JSON directly")

            # Try to extract JSON from markdown code blocks
            import re
            logger.info("Attempting to extract JSON from code blocks")
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
            if json_match:
                try:
                    extracted_json = json_match.group(1).strip()
                    logger.info("Found JSON in code block, attempting to parse")
                    return json.loads(extracted_json)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON from code block")

            # Try to find anything between { and } as a last resort
            try:
                if text.strip().startswith('{') and text.strip().endswith('}'):
                    logger.info("Text looks like JSON, trying to fix and parse")
                    # Try to clean up common JSON issues
                    cleaned_text = text.replace("'", '"')  # Replace single quotes with double quotes
                    return json.loads(cleaned_text)
            except Exception as e:
                logger.warning(f"Failed to clean and parse JSON-like text: {e}")

            logger.error("All JSON parsing attempts failed, returning error")
            logger.error(f"Problem text: {text[:500]}...")
            return {
                "error": "Failed to parse response as JSON",
                "raw_response": text
            }

    def _validate_and_fix_quiz(self, quiz_json: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix quiz structure if needed."""
        if "questions" not in quiz_json or not isinstance(quiz_json["questions"], list):
            logger.error("Invalid quiz structure: 'questions' key missing or not a list")
            return {
                "error": "Invalid quiz structure",
                "questions": [],
                "raw_response": str(quiz_json)
            }

        logger.info(f"Validating {len(quiz_json['questions'])} quiz questions")

        # Fix any malformed questions
        for i, question in enumerate(quiz_json['questions']):
            logger.info(f"Checking question {i+1}")

            # Ensure question has the required fields
            if not isinstance(question, dict):
                logger.warning(f"Question {i+1} is not a dictionary: {question}")
                quiz_json['questions'][i] = {
                    "question": f"Question {i+1} (malformed)",
                    "answers": [
                        {"text": "Option A", "is_correct": True},
                        {"text": "Option B", "is_correct": False},
                        {"text": "Option C", "is_correct": False},
                        {"text": "Option D", "is_correct": False}
                    ],
                    "explanation": "This is a placeholder for a malformed question."
                }
                continue

            # Fix missing fields
            if "question" not in question or not question["question"]:
                logger.warning(f"Question {i+1} missing question field")
                question["question"] = f"Question {i+1}"

            if "explanation" not in question or not question["explanation"]:
                logger.warning(f"Question {i+1} missing explanation field")
                question["explanation"] = "No explanation provided."

            # Fix answers structure
            if "answers" not in question or not isinstance(question["answers"], list) or len(question["answers"]) < 2:
                logger.warning(f"Question {i+1} has invalid answers: {question.get('answers', 'missing')}")
                question["answers"] = [
                    {"text": "Option A", "is_correct": True},
                    {"text": "Option B", "is_correct": False},
                    {"text": "Option C", "is_correct": False},
                    {"text": "Option D", "is_correct": False}
                ]
            else:
                # Make sure each answer has text and is_correct fields
                has_correct = False
                for j, answer in enumerate(question["answers"]):
                    if not isinstance(answer, dict):
                        logger.warning(f"Question {i+1}, Answer {j+1} is not a dictionary")
                        question["answers"][j] = {"text": f"Option {j+1}", "is_correct": j == 0}
                        continue

                    if "text" not in answer or not answer["text"]:
                        logger.warning(f"Question {i+1}, Answer {j+1} missing text field")
                        answer["text"] = f"Option {j+1}"

                    if "is_correct" not in answer:
                        logger.warning(f"Question {i+1}, Answer {j+1} missing is_correct field")
                        answer["is_correct"] = False

                    if answer["is_correct"]:
                        has_correct = True

                # Ensure at least one correct answer
                if not has_correct and question["answers"]:
                    logger.warning(f"Question {i+1} has no correct answer, fixing")
                    question["answers"][0]["is_correct"] = True

        return quiz_json

# Function to get a singleton OpenAI client instance
def get_llm_client():
    """
    Returns the initialized OpenAI client instance.

    Returns:
        OpenAI: The initialized OpenAI client
    """
    return client