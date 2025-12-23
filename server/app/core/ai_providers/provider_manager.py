"""
AI Provider Manager
Manages multiple AI providers with automatic fallback and quota detection
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from app.core.ai_providers.base_provider import (
    BaseAIProvider,
    ProviderException,
    QuotaExceededException,
    RateLimitException
)
from app.core.ai_providers.config_loader import AIProviderConfigLoader
from app.core.ai_providers.groq_provider import GroqProvider
from app.core.ai_providers.deepseek_provider import DeepSeekProvider
from app.core.ai_providers.gemini_provider import GeminiProvider
from app.core.ai_providers.ollama_provider import OllamaProvider
from app.models.ai_models import ProviderConfig, ProviderStatus, EnhancementResult, ProviderName

logger = logging.getLogger(__name__)


class AIProviderManager:
    """
    Manages multiple AI providers with automatic fallback and quota detection
    """
    
    def __init__(self):
        """Initialize provider manager"""
        self.providers: Dict[str, BaseAIProvider] = {}
        self.provider_configs: List[ProviderConfig] = []
        self.provider_statuses: Dict[str, ProviderStatus] = {}
        self.cached_provider: Optional[str] = None
        self.last_health_check = datetime.now() - timedelta(minutes=10)  # Force initial check
        
        # Load configurations and initialize providers
        self._load_providers()
        logger.info(f"Initialized AI Provider Manager with {len(self.providers)} providers")
    
    def _load_providers(self):
        """Load and initialize all configured providers"""
        self.provider_configs = AIProviderConfigLoader.load_provider_configs()
        
        for config in self.provider_configs:
            if not AIProviderConfigLoader.validate_config(config):
                logger.warning(f"Skipping invalid config for {config.name}")
                continue
            
            try:
                provider = self._create_provider(config)
                if provider:
                    self.providers[config.name] = provider
                    self.provider_statuses[config.name] = ProviderStatus(
                        name=config.name,
                        available=True,  # Will be checked in health check
                        last_check=datetime.now(),
                        supports_vision=provider.supports_vision()
                    )
                    logger.info(f"Loaded provider: {config.name}")
            except Exception as e:
                logger.error(f"Failed to initialize provider {config.name}: {e}")
                self.provider_statuses[config.name] = ProviderStatus(
                    name=config.name,
                    available=False,
                    last_check=datetime.now(),
                    error_message=str(e),
                    supports_vision=False
                )
    
    def _create_provider(self, config: ProviderConfig) -> Optional[BaseAIProvider]:
        """
        Create provider instance from config
        
        Args:
            config: Provider configuration
            
        Returns:
            Provider instance or None if creation fails
        """
        try:
            if config.name == ProviderName.GROQ:
                return GroqProvider(
                    api_key=config.api_key,
                    base_url=config.base_url,
                    model=config.model,
                    vision_model=config.vision_model
                )
            elif config.name == ProviderName.DEEPSEEK:
                return DeepSeekProvider(
                    api_key=config.api_key,
                    base_url=config.base_url,
                    model=config.model,
                    vision_model=config.vision_model
                )
            elif config.name == ProviderName.GEMINI:
                return GeminiProvider(
                    api_key=config.api_key,
                    base_url=config.base_url,
                    model=config.model,
                    vision_model=config.vision_model
                )
            elif config.name == ProviderName.OLLAMA:
                return OllamaProvider(
                    api_key=config.api_key,
                    base_url=config.base_url,
                    model=config.model,
                    vision_model=config.vision_model
                )
            else:
                logger.error(f"Unknown provider type: {config.name}")
                return None
        except Exception as e:
            logger.error(f"Error creating provider {config.name}: {e}")
            return None
    
    async def enhance_text(
        self,
        text: str,
        document_type: str = "general",
        image_data: Optional[bytes] = None,
        target_language: str = "auto"
    ) -> EnhancementResult:
        """
        Enhance OCR text using available providers with automatic fallback
        
        Args:
            text: Original OCR text to enhance
            document_type: Type of document (general, code, invoice, etc.)
            image_data: Optional image data for vision-based enhancement
            target_language: Target language (auto, vi, en, etc.)
            
        Returns:
            EnhancementResult with original and enhanced text
        """
        start_time = time.time()
        
        # Check provider health periodically
        await self._periodic_health_check()
        
        # Get ordered list of available providers
        available_providers = self._get_available_providers()
        
        if not available_providers:
            logger.warning("No available providers for text enhancement")
            return EnhancementResult(
                original_text=text,
                enhanced_text=text,
                provider_used="none",
                model_used="none",
                processing_time_ms=int((time.time() - start_time) * 1000),
                error="No available providers"
            )
        
        # Try cached provider first if available
        if self.cached_provider and self.cached_provider in available_providers:
            available_providers.remove(self.cached_provider)
            available_providers.insert(0, self.cached_provider)
        
        last_error = None
        fallback_occurred = False
        
        for provider_name in available_providers:
            try:
                provider = self.providers[provider_name]
                logger.info(f"Attempting text enhancement with {provider_name}")
                
                # Create enhancement prompt with language support
                prompt = self._create_enhancement_prompt(text, document_type, target_language)
                messages = [{"role": "user", "content": prompt}]
                
                # Use vision if available and image provided
                if image_data and provider.supports_vision():
                    logger.debug(f"Using vision enhancement with {provider_name}")
                    vision_prompt = self._create_vision_prompt(target_language)
                    enhanced_text = await provider.vision_completion(
                        vision_prompt,
                        image_data
                    )
                else:
                    enhanced_text = await provider.chat_completion(messages)
                
                # Validate response
                if not enhanced_text or len(enhanced_text.strip()) == 0:
                    raise ProviderException("Empty response from provider")
                
                # For Vietnamese, validate that tone marks were added
                if target_language == "vi":
                    # Check if enhanced text has Vietnamese tone marks
                    vietnamese_chars = set('àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ')
                    has_tones = any(c in vietnamese_chars for c in enhanced_text.lower())
                    
                    if not has_tones and len(enhanced_text) > 20:
                        # Text is long enough but has no tones - might be a problem
                        logger.warning(f"Provider {provider_name} returned Vietnamese text without tone marks, trying next provider")
                        last_error = "No Vietnamese tone marks detected"
                        fallback_occurred = True
                        continue
                
                # Success - cache this provider
                self.cached_provider = provider_name
                processing_time = int((time.time() - start_time) * 1000)
                
                logger.info(f"Text enhancement successful with {provider_name} in {processing_time}ms")
                
                return EnhancementResult(
                    original_text=text,
                    enhanced_text=enhanced_text.strip(),
                    provider_used=provider_name,
                    model_used=provider.model,
                    processing_time_ms=processing_time,
                    improvements=self._detect_improvements(text, enhanced_text),
                    fallback_occurred=fallback_occurred
                )
                
            except QuotaExceededException as e:
                logger.warning(f"Provider {provider_name} quota exceeded: {e}")
                self._mark_provider_quota_exceeded(provider_name, str(e))
                last_error = str(e)
                fallback_occurred = True
                continue
                
            except RateLimitException as e:
                logger.warning(f"Provider {provider_name} rate limited: {e}")
                self._mark_provider_rate_limited(provider_name, str(e))
                last_error = str(e)
                fallback_occurred = True
                continue
                
            except Exception as e:
                logger.error(f"Provider {provider_name} failed: {e}")
                self._mark_provider_error(provider_name, str(e))
                last_error = str(e)
                fallback_occurred = True
                continue
        
        # All providers failed - return original text
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"All providers failed for text enhancement. Last error: {last_error}")
        
        return EnhancementResult(
            original_text=text,
            enhanced_text=text,  # Return original text as fallback
            provider_used="none",
            model_used="none",
            processing_time_ms=processing_time,
            fallback_occurred=True,
            error=f"All providers failed. Last error: {last_error}"
        )
    
    def _create_enhancement_prompt(self, text: str, document_type: str, target_language: str = "auto") -> str:
        """
        Create enhancement prompt based on document type and target language
        
        Args:
            text: Original OCR text
            document_type: Type of document
            target_language: Target language (auto, vi, en, etc.)
            
        Returns:
            Enhancement prompt
        """
        # Language-specific instructions
        language_instruction = ""
        if target_language == "vi":
            language_instruction = """
5. CRITICAL: If the text is in Vietnamese, you MUST add proper tone marks (dấu thanh):
   - à, á, ả, ã, ạ for 'a'
   - è, é, ẻ, ẽ, ẹ for 'e'
   - ì, í, ỉ, ĩ, ị for 'i'
   - ò, ó, ỏ, õ, ọ for 'o'
   - ù, ú, ủ, ũ, ụ for 'u'
   - ỳ, ý, ỷ, ỹ, ỵ for 'y'
   - đ for 'd'
   - And all compound vowels: ă, â, ê, ô, ơ, ư with their tones
6. If the text is in another language, translate it to Vietnamese with proper tone marks
7. Examples:
   - "Truong Dai hoc" → "Trường Đại học"
   - "Ha Noi" → "Hà Nội"
   - "Viet Nam" → "Việt Nam"
"""
        elif target_language == "en":
            language_instruction = "\n5. Translate to English if the text is in another language"
        
        base_prompt = f"""Please improve the following OCR text by:
1. Correcting spelling and OCR errors
2. Fixing formatting and spacing issues
3. Preserving the original structure and meaning
4. Maintaining all important information{language_instruction}

IMPORTANT: Return ONLY the corrected text, without any explanations or comments.

Original OCR text:
"""
        
        if document_type == "code":
            base_prompt += "\nThis appears to be code or technical documentation. Please preserve code syntax and technical terms.\n"
        elif document_type == "invoice":
            base_prompt += "\nThis appears to be an invoice or receipt. Please preserve numbers, dates, and financial information accurately.\n"
        elif document_type == "form":
            base_prompt += "\nThis appears to be a form. Please preserve field labels and structure.\n"
        
        return base_prompt + f"\n{text}\n\nCorrected text:"
    
    def _create_vision_prompt(self, target_language: str = "auto") -> str:
        """
        Create vision prompt for image-based OCR
        
        Args:
            target_language: Target language
            
        Returns:
            Vision prompt
        """
        base_prompt = "Please extract and correct the text from this image, fixing any OCR errors."
        
        if target_language == "vi":
            base_prompt += """ 
CRITICAL: Ensure Vietnamese text has proper tone marks (dấu thanh):
- Use à, á, ả, ã, ạ, ă, ằ, ắ, ẳ, ẵ, ặ, â, ầ, ấ, ẩ, ẫ, ậ for 'a'
- Use è, é, ẻ, ẽ, ẹ, ê, ề, ế, ể, ễ, ệ for 'e'
- Use ò, ó, ỏ, õ, ọ, ô, ồ, ố, ổ, ỗ, ộ, ơ, ờ, ớ, ở, ỡ, ợ for 'o'
- Use ù, ú, ủ, ũ, ụ, ư, ừ, ứ, ử, ữ, ự for 'u'
- Use đ for 'd'

If text is in another language, translate to Vietnamese with proper tone marks.
Return ONLY the corrected text."""
        elif target_language == "en":
            base_prompt += " If text is in another language, translate to English. Return ONLY the corrected text."
        else:
            base_prompt += " Return ONLY the corrected text."
        
        return base_prompt
    
    def _detect_improvements(self, original: str, enhanced: str) -> List[str]:
        """
        Detect what improvements were made
        
        Args:
            original: Original text
            enhanced: Enhanced text
            
        Returns:
            List of improvement descriptions
        """
        improvements = []
        
        # Simple heuristics for detecting improvements
        if len(enhanced) > len(original) * 1.1:
            improvements.append("Added missing content")
        elif len(enhanced) < len(original) * 0.9:
            improvements.append("Removed redundant content")
        
        if original.count('\n') != enhanced.count('\n'):
            improvements.append("Improved formatting")
        
        if original.lower() != enhanced.lower():
            improvements.append("Corrected spelling/grammar")
        
        return improvements
    
    def _get_available_providers(self) -> List[str]:
        """
        Get list of available providers in priority order
        
        Returns:
            List of available provider names
        """
        available = []
        
        for config in self.provider_configs:
            if config.name in self.provider_statuses:
                status = self.provider_statuses[config.name]
                if status.available and not status.quota_exceeded:
                    available.append(config.name)
        
        return available
    
    def _mark_provider_quota_exceeded(self, provider_name: str, error_msg: str):
        """Mark provider as quota exceeded"""
        if provider_name in self.provider_statuses:
            status = self.provider_statuses[provider_name]
            status.available = False
            status.quota_exceeded = True
            status.unavailable_reason = "quota_exceeded"
            status.error_message = error_msg
            status.last_check = datetime.now()
            # Set quota reset time (estimate 24 hours for most providers)
            status.quota_reset_time = datetime.now() + timedelta(hours=24)
            
            logger.warning(f"Provider {provider_name} marked as quota exceeded")
    
    def _mark_provider_rate_limited(self, provider_name: str, error_msg: str):
        """Mark provider as rate limited"""
        if provider_name in self.provider_statuses:
            status = self.provider_statuses[provider_name]
            status.available = False
            status.unavailable_reason = "rate_limit"
            status.error_message = error_msg
            status.last_check = datetime.now()
            # Set shorter cooldown for rate limits (1 hour)
            status.quota_reset_time = datetime.now() + timedelta(hours=1)
            
            logger.warning(f"Provider {provider_name} marked as rate limited")
    
    def _mark_provider_error(self, provider_name: str, error_msg: str):
        """Mark provider as having an error"""
        if provider_name in self.provider_statuses:
            status = self.provider_statuses[provider_name]
            status.available = False
            status.unavailable_reason = "api_error"
            status.error_message = error_msg
            status.last_check = datetime.now()
            
            logger.error(f"Provider {provider_name} marked as error: {error_msg}")
    
    async def _periodic_health_check(self):
        """Perform periodic health checks on providers"""
        now = datetime.now()
        
        # Check every 5 minutes
        if now - self.last_health_check < timedelta(minutes=5):
            return
        
        logger.debug("Performing periodic provider health check")
        
        for provider_name, provider in self.providers.items():
            try:
                # Check if provider should be retried (quota reset time passed)
                status = self.provider_statuses.get(provider_name)
                if status and not status.available and status.quota_reset_time:
                    if now >= status.quota_reset_time:
                        logger.info(f"Retrying provider {provider_name} after cooldown")
                        status.available = True
                        status.quota_exceeded = False
                        status.unavailable_reason = None
                        status.quota_reset_time = None
                
                # Perform health check
                if status and status.available:
                    start_time = time.time()
                    is_healthy = await provider.check_health()
                    response_time = int((time.time() - start_time) * 1000)
                    
                    status.last_check = now
                    status.response_time_ms = response_time
                    
                    if not is_healthy and status.available:
                        logger.warning(f"Provider {provider_name} failed health check")
                        status.available = False
                        status.unavailable_reason = "health_check_failed"
                    elif is_healthy and not status.available and not status.quota_exceeded:
                        logger.info(f"Provider {provider_name} recovered")
                        status.available = True
                        status.unavailable_reason = None
                        status.error_message = None
                        
            except Exception as e:
                logger.error(f"Health check failed for {provider_name}: {e}")
        
        self.last_health_check = now
    
    async def get_provider_status(self) -> Dict[str, ProviderStatus]:
        """
        Get health status of all providers
        
        Returns:
            Dict mapping provider name to status
        """
        await self._periodic_health_check()
        return self.provider_statuses.copy()
    
    def get_active_provider(self) -> Optional[str]:
        """
        Get currently active/cached provider name
        
        Returns:
            Active provider name or None
        """
        return self.cached_provider
    
    async def close(self):
        """Close all provider connections"""
        for provider in self.providers.values():
            if hasattr(provider, 'close'):
                await provider.close()
        logger.info("Closed all provider connections")


# Global provider manager instance
provider_manager = AIProviderManager()