"""
LLM Client Configuration
------------------------
Centralized class to initialize and return an OpenAI-compatible LLM client.

Automatically reads:
- MODEL_NAME (default: gpt-4o-mini)
- TEMPERATURE (default: 0.7)
from the .env file.
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()


class LLMClient:
    """Wrapper class for initializing the OpenAI LLM."""

    def __init__(self, model: str = None, temperature: float = None):
        """
        Initialize the LLM client with environment or provided values.

        Args:
            model (str): Model name (optional; reads from .env if not provided)
            temperature (float): Sampling temperature (optional; reads from .env if not provided)
        """
        # Load from .env with fallbacks
        self.model = model or os.getenv("MODEL_NAME", "gpt-4o-mini")
        self.temperature = temperature or float(os.getenv("TEMPERATURE", 0.7))

        # Initialize OpenAI client
        self.client = ChatOpenAI(model=self.model, temperature=self.temperature)

    def get_client(self):
        """Return the initialized LLM client."""
        return self.client
