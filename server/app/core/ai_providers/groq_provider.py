"""
Groq AI Provider Implementation
Ultra-fast inference with OpenAI-compatible API
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


class GroqProvider(BaseAIProvider):
    """
    Groq AI provider implementation
    Uses OpenAI-compatible API format for fast inference
    """
    
    def __init__(self, api_key: str, base_url: str, model: str, vision_model: Optional[str] = None):
        """
        Initialize Groq provider
        
        Args:
            api_key: Groq API key
            base_url: Groq API base URL
            model: Default model (e.g., llama-3.3-70b-versatile)
            vision_model: Vision model (e.g., llama-3.2-90b-vision-preview)
        """
        super().__init__(api_key, base_url, model, vision_model)
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
        logger.info(f"Initialized Groq provider with model {self.model}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Send chat completion request to Groq
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to self.model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
            
        Raises:
            QuotaExceededException: If quota/credits exhausted
            RateLimitException: If rate limit exceeded
            ProviderException: For other errors
        """
        model = model or self.model
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        try:
            logger.debug(f"Sending chat completion request to Groq with model {model}")
            
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            
            # Check for errors
            if response.status_code == 429:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", "Rate limit exceeded")
                logger.warning(f"Groq rate limit exceeded: {error_msg}")
                raise RateLimitException(f"Groq rate limit: {error_msg}")
            
            if response.status_code == 403:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", "Quota exceeded")
                logger.warning(f"Groq quota exceeded: {error_msg}")
                raise QuotaExceededException(f"Groq quota exceeded: {error_msg}")
            
            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                logger.error(f"Groq API error: {error_msg}")
                raise ProviderException(f"Groq API error: {error_msg}")
            
            # Parse response
            data = response.json()
            
            if "choices" not in data or len(data["choices"]) == 0:
                raise ProviderException("Groq returned empty response")
            
            content = data["choices"][0]["message"]["content"]
            
            logger.debug(f"Groq chat completion successful, generated {len(content)} characters")
            return content
            
        except (QuotaExceededException, RateLimitException):
            raise
        except httpx.TimeoutException:
            logger.error("Groq request timeout")
            raise ProviderException("Groq request timeout")
        except httpx.RequestError as e:
            logger.error(f"Groq request error: {e}")
            raise ProviderException(f"Groq request error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected Groq error: {e}")
            raise ProviderException(f"Unexpected Groq error: {str(e)}")
    
    async def vision_completion(
        self,
        prompt: str,
        image_data: bytes,
        model: Optional[str] = None
    ) -> str:
        """
        Send vision-based completion request to Groq
        
        Args:
            prompt: Text prompt for image analysis
            image_data: Image bytes
            model: Vision model to use
            
        Returns:
            Generated text response from image analysis
            
        Raises:
            QuotaExceededException: If quota/credits exhausted
            RateLimitException: If rate limit exceeded
            ProviderException: For other errors
        """
        if not self.vision_model:
            raise ProviderException("Groq vision model not configured")
        
        model = model or self.vision_model
        
        # Encode image to base64
        import base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Groq uses OpenAI format for vision
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
        
        try:
            logger.debug(f"Sending vision completion request to Groq with model {model}")
            
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.1
                }
            )
            
            # Check for errors (same as chat_completion)
            if response.status_code == 429:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", "Rate limit exceeded")
                raise RateLimitException(f"Groq rate limit: {error_msg}")
            
            if response.status_code == 403:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", "Quota exceeded")
                raise QuotaExceededException(f"Groq quota exceeded: {error_msg}")
            
            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                raise ProviderException(f"Groq vision API error: {error_msg}")
            
            # Parse response
            data = response.json()
            
            if "choices" not in data or len(data["choices"]) == 0:
                raise ProviderException("Groq vision returned empty response")
            
            content = data["choices"][0]["message"]["content"]
            
            logger.debug(f"Groq vision completion successful")
            return content
            
        except (QuotaExceededException, RateLimitException):
            raise
        except Exception as e:
            logger.error(f"Groq vision error: {e}")
            raise ProviderException(f"Groq vision error: {str(e)}")
    
    async def check_health(self) -> bool:
        """
        Check if Groq is available and healthy
        
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
            logger.debug(f"Groq health check failed: {e}")
            return False
    
    def supports_vision(self) -> bool:
        """
        Check if Groq supports vision models
        
        Returns:
            True if vision is supported
        """
        return self.vision_model is not None
    
    def get_name(self) -> str:
        """
        Get provider name
        
        Returns:
            "groq"
        """
        return "groq"
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
