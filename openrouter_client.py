import os
from dotenv import load_dotenv
import logging
import asyncio
import aiohttp

logger = logging.getLogger(__name__)
load_dotenv()

class OpenRouterClient:
    """
    Client for interacting with the OpenRouter API (LLM provider)
    Handles both synchronous and asynchronous chat completions
    """
    def __init__(self, api_key: str, base_url: str = "https://openrouter.ai/api/v1"):
        """Initializes the OpenRouter client with API key and base URL"""
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        logger.info("Initialized OpenRouterClient")

    def chat(self, model: str, messages: list, **kwargs):
        """
        Synchronous chat completion using the OpenRouter API
        Internally runs the async version using asyncio.run
        """
        return asyncio.run(self.async_chat(model, messages, **kwargs))
    
    async def async_chat(self, model: str, messages: list, **kwargs):
        """
        Asynchronous chat completion using the OpenRouter API
        Sends a POST request to the /chat/completions endpoint
        """
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            **kwargs
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"Error: {response.status} - {await response.text()}")
                data = await response.json()
                return data["choices"][0]["message"]["content"]
