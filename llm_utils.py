"""
Utility functions for LLM providers with advanced API management.
"""

import logging
import time
from typing import Any, Dict, Optional
from models import ModelProvider, OllamaProvider, GeminiProvider
from prompt import MODEL_PROVIDER_MAPPING, GEMINI_API_KEY
from api_manager import api_rotator, smart_cache

logger = logging.getLogger(__name__)

# Higher-limit models for better performance
OPTIMIZED_MODELS = {
    "gemini": {
        "primary": "gemini-2.0-flash",      # Higher limits, faster
        "fallback": "gemini-1.5-flash",     # Backup option
        "premium": "gemini-1.5-pro"         # Lower limits but better quality
    }
}

def extract_json_from_response(response_text: str) -> str:
    """
    Extract JSON content from markdown code blocks.

    Args:
        response_text: Text that may contain JSON wrapped in markdown code blocks

    Returns:
        Text with markdown code block syntax removed
    """

    response_text = response_text.strip()
    if "<think>" in response_text:
        think_start = response_text.find("<think>")
        think_end = response_text.find("</think>")
        if think_start != -1 and think_end != -1:
            response_text = response_text[:think_start] + response_text[think_end + 8 :]

    # Remove leading ```json if present
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    # Remove trailing ``` if present
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    return response_text


def get_optimized_model(provider: str = "gemini", quality_level: str = "primary") -> str:
    """Get the best model for the provider based on current API status."""
    if provider == "gemini":
        # Check API key availability and return appropriate model
        models_to_try = [
            OPTIMIZED_MODELS["gemini"]["primary"],
            OPTIMIZED_MODELS["gemini"]["fallback"]
        ]
        
        for model in models_to_try:
            key_info = api_rotator.get_best_api_key(model)
            if key_info:
                logger.info(f"Selected model {model} with available API key")
                return model
        
        # Fallback to original if no keys available
        return "gemini-2.5-flash"
    
    return "gemma3:4b"  # Ollama default


def initialize_llm_provider_with_rotation(model_name: str) -> tuple:
    """
    Initialize LLM provider with API key rotation support.
    Returns (provider, key_id, actual_model)
    """
    model_provider = MODEL_PROVIDER_MAPPING.get(model_name, ModelProvider.OLLAMA)
    
    if model_provider == ModelProvider.GEMINI:
        # Get the best available API key
        key_info = api_rotator.get_best_api_key(model_name)
        
        if not key_info:
            logger.warning("⚠️ No Gemini API keys available. Falling back to Ollama.")
            return OllamaProvider(), None, "gemma3:4b"
        
        api_key, key_id = key_info
        logger.info(f"🔄 Using Gemini API with key {key_id} and model {model_name}")
        
        try:
            provider = GeminiProvider(api_key=api_key)
            return provider, key_id, model_name
        except Exception as e:
            logger.error(f"Failed to initialize Gemini provider: {e}")
            # Mark this key as failed
            api_rotator.record_request(key_id, success=False)
            return OllamaProvider(), None, "gemma3:4b"
    else:
        logger.info(f"🔄 Using Ollama provider with model {model_name}")
        return OllamaProvider(), None, model_name


def make_cached_api_call(content: str, messages: list, operation: str, model_name: str = None) -> Optional[str]:
    """
    Make an API call with smart caching and rotation.
    
    Args:
        content: The content being processed (for cache key)
        messages: The messages to send to the API
        operation: The operation type (for caching)
        model_name: The model to use
    
    Returns:
        The API response content or None if failed
    """
    # Try to get from cache first
    cached_result = smart_cache.get(content, operation, model_name or "default")
    if cached_result:
        return cached_result
    
    # Determine best model if not specified
    if not model_name:
        model_name = get_optimized_model("gemini", "primary")
    
    # Initialize provider with rotation
    provider, key_id, actual_model = initialize_llm_provider_with_rotation(model_name)
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Make the API call
            response = provider.chat(
                model=actual_model,
                messages=messages,
                options={"temperature": 0.1, "top_p": 0.9}
            )
            
            if response and 'message' in response:
                content_result = response['message']['content']
                
                # Record successful request
                if key_id:
                    api_rotator.record_request(key_id, success=True)
                
                # Cache the result
                smart_cache.set(content, operation, actual_model, content_result)
                
                logger.info(f"✅ Successful API call for operation {operation}")
                return content_result
            else:
                raise Exception("Invalid response format")
        
        except Exception as e:
            retry_count += 1
            logger.warning(f"API call failed (attempt {retry_count}/{max_retries}): {e}")
            
            # Record failed request
            if key_id:
                api_rotator.record_request(key_id, success=False)
            
            # If quota exceeded or rate limited, try different key/model
            error_str = str(e).lower()
            if any(term in error_str for term in ["quota", "rate", "limit"]):
                logger.info("Rate limit detected, trying different key/model...")
                
                # Try a different model or key
                if retry_count < max_retries:
                    # Get next best option
                    provider, key_id, actual_model = initialize_llm_provider_with_rotation(model_name)
                    time.sleep(2)  # Brief pause before retry
            else:
                # For other errors, wait before retry
                time.sleep(1)
    
    logger.error(f"❌ All API call attempts failed for operation {operation}")
    return None


def initialize_llm_provider(model_name: str) -> Any:
    """
    Legacy function for backward compatibility.
    """
    provider, _, _ = initialize_llm_provider_with_rotation(model_name)
    return provider
