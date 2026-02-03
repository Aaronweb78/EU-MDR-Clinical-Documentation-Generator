"""
Ollama LLM client for text generation
"""
import ollama
import logging
from typing import Generator, Optional, Dict
from config import OLLAMA_BASE_URL, OLLAMA_DEFAULT_MODEL, OLLAMA_TEMPERATURE, OLLAMA_MAX_TOKENS

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama LLM"""

    def __init__(self, base_url: str = OLLAMA_BASE_URL,
                 model: str = OLLAMA_DEFAULT_MODEL):
        """
        Initialize Ollama client

        Args:
            base_url: Ollama server URL
            model: Model name to use
        """
        self.base_url = base_url
        self.model = model
        self.client = ollama.Client(host=base_url)

    def test_connection(self) -> Dict:
        """
        Test connection to Ollama server

        Returns:
            Dictionary with connection status
        """
        try:
            # Try to list models
            models_response = self.client.list()

            # Handle different response formats
            model_list = []
            if isinstance(models_response, dict):
                models = models_response.get('models', [])
                for m in models:
                    if isinstance(m, dict):
                        model_list.append(m.get('name', m.get('model', 'unknown')))
                    else:
                        model_list.append(str(m))

            return {
                'success': True,
                'models': model_list,
                'message': 'Connected successfully'
            }
        except Exception as e:
            logger.error(f"Error connecting to Ollama: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to connect to Ollama server'
            }

    def generate(self, prompt: str,
                temperature: float = OLLAMA_TEMPERATURE,
                max_tokens: int = OLLAMA_MAX_TOKENS,
                system_prompt: Optional[str] = None) -> str:
        """
        Generate text from prompt (non-streaming)

        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt

        Returns:
            Generated text
        """
        try:
            messages = []

            if system_prompt:
                messages.append({
                    'role': 'system',
                    'content': system_prompt
                })

            messages.append({
                'role': 'user',
                'content': prompt
            })

            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    'temperature': temperature,
                    'num_predict': max_tokens
                }
            )

            return response['message']['content']

        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise

    def generate_stream(self, prompt: str,
                       temperature: float = OLLAMA_TEMPERATURE,
                       max_tokens: int = OLLAMA_MAX_TOKENS,
                       system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        """
        Generate text with streaming (for real-time UI updates)

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt

        Yields:
            Text chunks as they are generated
        """
        try:
            messages = []

            if system_prompt:
                messages.append({
                    'role': 'system',
                    'content': system_prompt
                })

            messages.append({
                'role': 'user',
                'content': prompt
            })

            stream = self.client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options={
                    'temperature': temperature,
                    'num_predict': max_tokens
                }
            )

            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']

        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            raise

    def generate_with_context(self, prompt: str, context: str,
                             temperature: float = OLLAMA_TEMPERATURE,
                             max_tokens: int = OLLAMA_MAX_TOKENS) -> str:
        """
        Generate text with provided context (for RAG)

        Args:
            prompt: User prompt/question
            context: Retrieved context from documents
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        system_prompt = """You are a medical device regulatory expert writing clinical documentation per EU MDR 2017/745.
Use the provided context from source documents to write accurate, thorough, and compliant regulatory content.
Always base your writing on the evidence provided in the context."""

        full_prompt = f"""Context from source documents:
{context}

Task:
{prompt}

Write your response based on the context provided above."""

        return self.generate(
            prompt=full_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt
        )

    def generate_stream_with_context(self, prompt: str, context: str,
                                    temperature: float = OLLAMA_TEMPERATURE,
                                    max_tokens: int = OLLAMA_MAX_TOKENS) -> Generator[str, None, None]:
        """
        Generate text with context (streaming)

        Args:
            prompt: User prompt/question
            context: Retrieved context
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Yields:
            Text chunks
        """
        system_prompt = """You are a medical device regulatory expert writing clinical documentation per EU MDR 2017/745.
Use the provided context from source documents to write accurate, thorough, and compliant regulatory content.
Always base your writing on the evidence provided in the context."""

        full_prompt = f"""Context from source documents:
{context}

Task:
{prompt}

Write your response based on the context provided above."""

        return self.generate_stream(
            prompt=full_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt
        )

    def list_models(self) -> list:
        """
        List available models on Ollama server

        Returns:
            List of model names
        """
        try:
            models_response = self.client.list()
            model_list = []
            if isinstance(models_response, dict):
                models = models_response.get('models', [])
                for m in models:
                    if isinstance(m, dict):
                        model_list.append(m.get('name', m.get('model', 'unknown')))
                    else:
                        model_list.append(str(m))
            return model_list
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []

    def pull_model(self, model_name: str) -> bool:
        """
        Pull/download a model from Ollama

        Args:
            model_name: Name of model to pull

        Returns:
            True if successful
        """
        try:
            self.client.pull(model_name)
            logger.info(f"Successfully pulled model: {model_name}")
            return True
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            return False

    def set_model(self, model_name: str):
        """
        Change the active model

        Args:
            model_name: New model name
        """
        self.model = model_name
        logger.info(f"Active model changed to: {model_name}")

    def get_model_info(self, model_name: Optional[str] = None) -> Dict:
        """
        Get information about a model

        Args:
            model_name: Model name (uses current model if not specified)

        Returns:
            Model information dictionary
        """
        target_model = model_name or self.model

        try:
            info = self.client.show(target_model)
            return info
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {}

    def validate_prompt_length(self, prompt: str, max_length: int = 6000) -> Dict:
        """
        Validate prompt length

        Args:
            prompt: Prompt text
            max_length: Maximum allowed length

        Returns:
            Validation result
        """
        # Rough token count (1 token ≈ 4 characters)
        estimated_tokens = len(prompt) / 4

        return {
            'valid': estimated_tokens < max_length,
            'estimated_tokens': int(estimated_tokens),
            'max_tokens': max_length,
            'char_count': len(prompt)
        }

    def generate_with_retry(self, prompt: str,
                          temperature: float = OLLAMA_TEMPERATURE,
                          max_tokens: int = OLLAMA_MAX_TOKENS,
                          max_retries: int = 3) -> Optional[str]:
        """
        Generate with automatic retry on failure

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            max_retries: Maximum retry attempts

        Returns:
            Generated text or None if all retries fail
        """
        for attempt in range(max_retries):
            try:
                return self.generate(prompt, temperature, max_tokens)
            except Exception as e:
                logger.warning(f"Generation attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error("All retry attempts failed")
                    return None

        return None
