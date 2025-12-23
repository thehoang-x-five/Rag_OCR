"""
DeepSeek AI Provider Implementation
Cost-effective AI with specialized coder model
"""
import logging
import httpx
from typing import List, Dict, Optional
from app.core.ai_providers.base_provider import (
    BaseAIProvider,
    ProviderException,
    QuotaExceededException,
    RateLimitException
)

logger = logging.getLogger(__name__)


class DeepSeekProvider(BaseAIProvider):
    """
    DeepSeek AI provider implementation
    Uses OpenAI-compatible API format with specialized models
    """
    
    def __init__(self, api_key: str, base_url: str, model: str, vision_model: Optional[str] = None):
        """
        Initialize DeepSeek provider
        
        Args:
            api_key: DeepSeek API key
            base_url: DeepSeek API base URL
            model: Default model (e.g., deepseek-chat)
            vision_model: Vision model (DeepSeek doesn't have vision yet)
        """
        super().__init__(api_key, base_url, model, vision_model)
        self.coder_model = "deepseek-coder"  # Specialized model for code
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
        logger.info(f"Initialized DeepSeek provider with model {self.model}")
    
    def _detect_code_document(self, messages: List[Dict[str, str]]) -> bool:
        """
        Detect if the content appears to be code-related
        
        Args:
            messages: List of messages to analyze
            
        Returns:
            True if content appears to be code-related
        """
        code_indicators = [
            'function', 'class', 'import', 'def ', 'var ', 'let ', 'const ',
            'public ', 'private ', 'static ', 'void ', 'int ', 'string ',
            '#!/', '<?php', '<html>', '<script>', 'SELECT ', 'INSERT ',
            'CREATE TABLE', 'git ', 'npm ', 'pip ', 'docker ', 'kubernetes',
            '```', 'console.log', 'print(', 'System.out', 'printf(',
            'malloc', 'free', 'struct ', 'typedef ', '#include', '#define'
        ]
        
        # Check all message content
        full_text = ' '.join([msg.get('content', '') for msg in messages]).lower()
        
        # Count code indicators
        code_count = sum(1 for indicator in code_indicators if indicator.lower() in full_text)
        
        # If we find multiple code indicators, likely a code document
        return code_count >= 2
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Send chat completion request to DeepSeek
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to self.model or coder model for code)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
            
        Raises:
            QuotaExceededException: If quota/credits exhausted
            RateLimitException: If rate limit exceeded
            ProviderException: For other errors
        """
        # Auto-select model based on content if not specified
        if model is None:
            if self._detect_code_document(messages):
                model = self.coder_model
                logger.debug("Detected code content, using DeepSeek-Coder model")
            else:
                model = self.model
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        try:
            logger.debug(f"Sending chat completion request to DeepSeek with model {model}")
            
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            
            # Check for errors
            if response.status_code == 429:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", "Rate limit exceeded")
                logger.warning(f"DeepSeek rate limit exceeded: {error_msg}")
                raise RateLimitException(f"DeepSeek rate limit: {error_msg}")
            
            if response.status_code == 403:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", "Quota exceeded")
                logger.warning(f"DeepSeek quota exceeded: {error_msg}")
                raise QuotaExceededException(f"DeepSeek quota exceeded: {error_msg}")
            
            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                logger.error(f"DeepSeek API error: {error_msg}")
                raise ProviderException(f"DeepSeek API error: {error_msg}")
            
            # Parse response
            data = response.json()
            
            if "choices" not in data or len(data["choices"]) == 0:
                raise ProviderException("DeepSeek returned empty response")
            
            content = data["choices"][0]["message"]["content"]
            
            logger.debug(f"DeepSeek chat completion successful, generated {len(content)} characters")
            return content
            
        except (QuotaExceededException, RateLimitException):
            raise
        except httpx.TimeoutException:
            logger.error("DeepSeek request timeout")
            raise ProviderException("DeepSeek request timeout")
        except httpx.RequestError as e:
            logger.error(f"DeepSeek request error: {e}")
            raise ProviderException(f"DeepSeek request error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected DeepSeek error: {e}")
            raise ProviderException(f"Unexpected DeepSeek error: {str(e)}")
    
    async def vision_completion(
        self,
        prompt: str,
        image_data: bytes,
        model: Optional[str] = None
    ) -> str:
        """
        Send vision-based completion request to DeepSeek
        
        Args:
            prompt: Text prompt for image analysis
            image_data: Image bytes
            model: Vision model to use
            
        Returns:
            Generated text response from image analysis
            
        Raises:
            NotImplementedError: DeepSeek doesn't support vision yet
        """
        raise NotImplementedError("DeepSeek does not support vision models yet")
    
    async def check_health(self) -> bool:
        """
        Check if DeepSeek is available and healthy
        
        Returns:
            True if available, False otherwise
        """
        try:
            # Send a minimal test request
            test_messages = [{"role": "user", "content": "test"}]
            
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": test_messages,
                    "max_tokens": 5
                }
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.debug(f"DeepSeek health check failed: {e}")
            return False
    
    def supports_vision(self) -> bool:
        """
        Check if DeepSeek supports vision models
        
        Returns:
            False (DeepSeek doesn't support vision yet)
        """
        return False
    
    def get_name(self) -> str:
        """
        Get provider name
        
        Returns:
            "deepseek"
        """
        return "deepseek"
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()