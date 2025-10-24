"""
Groq API client for LLM interactions.
"""
from typing import List, Dict, Optional
from groq import Groq

from ..config import get_settings
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class GroqClient:
    """Wrapper for Groq API interactions."""
    
    def __init__(self, model: str = "llama-3.1-70b-versatile"):
        """
        Initialize the Groq client.
        
        Args:
            model: Model to use
        """
        settings = get_settings()
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = model
        logger.info(f"Groq client initialized with model: {self.model}")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        """
        Generate a chat completion.
        
        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        """
        Generate text from a prompt.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            
        Returns:
            Generated text
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        return self.chat_completion(messages, temperature, max_tokens)
    
    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate JSON-formatted response.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            JSON string
        """
        if not system_prompt:
            system_prompt = "You are a helpful assistant that responds in valid JSON format."
        
        return self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3  # Lower temperature for structured output
        )

