"""
Google Gemini AI Provider Implementation
Multimodal AI with native vision support
"""
import logging
import httpx
import base64
from typing import List, Dict, Optional
from app.core.ai_providers.base_provider import (
    BaseAIProvider,
    ProviderException,
    QuotaExceededException,
    RateLimitException
)

logger = logging.getLogger(__name__)


class GeminiProvider(BaseAIProvider):
    """
    Google Gemini AI provider implementation
    Uses Google AI API format with native multimodal support
    """
    
    def __init__(self, api_key: str, base_url: str, model: str, vision_model: Optional[str] = None):
        """
        Initialize Gemini provider
        
        Args:
            api_key: Google AI API key
            base_url: Gemini API base URL
            model: Default model (e.g., gemini-1.5-flash)
            vision_model: Vision model (Gemini models support vision natively)
        """
        super().__init__(api_key, base_url, model, vision_model or model)
        self.client = httpx.AsyncClient(
            params={"key": self.api_key},  # Gemini uses query param for API key
            timeout=30.0
        )
        logger.info(f"Initialized Gemini provider with model {self.model}")
    
    def _convert_messages_to_gemini_format(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Convert OpenAI-style messages to Gemini format
        
        Args:
            messages: OpenAI-style messages
            
        Returns:
            Gemini-formatted messages
        """
        gemini_messages = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Convert role mapping
            if role == "system":
                # Gemini doesn't have system role, prepend to first user message
                if gemini_messages and gemini_messages[-1]["role"] == "user":
                    gemini_messages[-1]["parts"][0]["text"] = f"{content}\n\n{gemini_messages[-1]['parts'][0]['text']}"
                else:
                    gemini_messages.append({
                        "role": "user",
                        "parts": [{"text": content}]
                    })
            elif role == "assistant":
                gemini_messages.append({
                    "role": "model",
                    "parts": [{"text": content}]
                })
            else:  # user
                gemini_messages.append({
                    "role": "user",
                    "parts": [{"text": content}]
                })
        
        return gemini_messages
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Send chat completion request to Gemini
        
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
        
        # Convert messages to Gemini format
        gemini_messages = self._convert_messages_to_gemini_format(messages)
        
        payload = {
            "contents": gemini_messages,
            "generationConfig": {
                "temperature": temperature
            }
        }
        
        if max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens
        
        try:
            logger.debug(f"Sending chat completion request to Gemini with model {model}")
            
            response = await self.client.post(
                f"{self.base_url}/models/{model}:generateContent",
                json=payload
            )
            
            # Check for errors
            if response.status_code == 429:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", "Rate limit exceeded")
                logger.warning(f"Gemini rate limit exceeded: {error_msg}")
                raise RateLimitException(f"Gemini rate limit: {error_msg}")
            
            if response.status_code == 403:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", "Quota exceeded")
                logger.warning(f"Gemini quota exceeded: {error_msg}")
                raise QuotaExceededException(f"Gemini quota exceeded: {error_msg}")
            
            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                logger.error(f"Gemini API error: {error_msg}")
                raise ProviderException(f"Gemini API error: {error_msg}")
            
            # Parse Gemini response format
            data = response.json()
            
            if "candidates" not in data or len(data["candidates"]) == 0:
                raise ProviderException("Gemini returned empty response")
            
            candidate = data["candidates"][0]
            
            if "content" not in candidate or "parts" not in candidate["content"]:
                raise ProviderException("Gemini response missing content")
            
            parts = candidate["content"]["parts"]
            if len(parts) == 0 or "text" not in parts[0]:
                raise ProviderException("Gemini response missing text")
            
            content = parts[0]["text"]
            
            logger.debug(f"Gemini chat completion successful, generated {len(content)} characters")
            return content
            
        except (QuotaExceededException, RateLimitException):
            raise
        except httpx.TimeoutException:
            logger.error("Gemini request timeout")
            raise ProviderException("Gemini request timeout")
        except httpx.RequestError as e:
            logger.error(f"Gemini request error: {e}")
            raise ProviderException(f"Gemini request error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected Gemini error: {e}")
            raise ProviderException(f"Unexpected Gemini error: {str(e)}")
    
    async def vision_completion(
        self,
        prompt: str,
        image_data: bytes,
        model: Optional[str] = None
    ) -> str:
        """
        Send vision-based completion request to Gemini
        
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
        model = model or self.vision_model
        
        # Encode image to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Detect image format
        image_format = "image/jpeg"  # Default
        if image_data.startswith(b'\x89PNG'):
            image_format = "image/png"
        elif image_data.startswith(b'GIF'):
            image_format = "image/gif"
        elif image_data.startswith(b'\xff\xd8'):
            image_format = "image/jpeg"
        
        # Gemini multimodal format
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": image_format,
                                "data": image_base64
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1
            }
        }
        
        try:
            logger.debug(f"Sending vision completion request to Gemini with model {model}")
            
            response = await self.client.post(
                f"{self.base_url}/models/{model}:generateContent",
                json=payload
            )
            
            # Check for errors (same as chat_completion)
            if response.status_code == 429:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", "Rate limit exceeded")
                raise RateLimitException(f"Gemini rate limit: {error_msg}")
            
            if response.status_code == 403:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", "Quota exceeded")
                raise QuotaExceededException(f"Gemini quota exceeded: {error_msg}")
            
            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                raise ProviderException(f"Gemini vision API error: {error_msg}")
            
            # Parse response
            data = response.json()
            
            if "candidates" not in data or len(data["candidates"]) == 0:
                raise ProviderException("Gemini vision returned empty response")
            
            candidate = data["candidates"][0]
            
            if "content" not in candidate or "parts" not in candidate["content"]:
                raise ProviderException("Gemini vision response missing content")
            
            parts = candidate["content"]["parts"]
            if len(parts) == 0 or "text" not in parts[0]:
                raise ProviderException("Gemini vision response missing text")
            
            content = parts[0]["text"]
            
            logger.debug(f"Gemini vision completion successful")
            return content
            
        except (QuotaExceededException, RateLimitException):
            raise
        except Exception as e:
            logger.error(f"Gemini vision error: {e}")
            raise ProviderException(f"Gemini vision error: {str(e)}")
    
    async def check_health(self) -> bool:
        """
        Check if Gemini is available and healthy
        
        Returns:
            True if available, False otherwise
        """
        try:
            # Send a minimal test request
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": "test"}]
                    }
                ],
                "generationConfig": {
                    "maxOutputTokens": 5
                }
            }
            
            response = await self.client.post(
                f"{self.base_url}/models/{self.model}:generateContent",
                json=payload
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.debug(f"Gemini health check failed: {e}")
            return False
    
    def supports_vision(self) -> bool:
        """
        Check if Gemini supports vision models
        
        Returns:
            True (Gemini models support vision natively)
        """
        return True
    
    def get_name(self) -> str:
        """
        Get provider name
        
        Returns:
            "gemini"
        """
        return "gemini"
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()