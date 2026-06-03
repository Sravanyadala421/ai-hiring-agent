#!/usr/bin/env python3
"""
Advanced API management with key rotation, rate limiting, and caching.
"""
import os
import time
import json
import random
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class APIKeyRotator:
    """Manages multiple API keys with intelligent rotation and rate limiting."""
    
    def __init__(self):
        # Load environment variables first
        from dotenv import load_dotenv
        load_dotenv()
        
        self.cache_dir = Path("cache/api_management")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.usage_file = self.cache_dir / "api_usage.json"
        self.api_keys = self._load_api_keys()
        self.usage_data = self._load_usage_data()
        
        # Rate limits for different models (requests per minute)
        self.rate_limits = {
            "gemini-2.0-flash": {"per_minute": 15, "per_day": 1500},
            "gemini-1.5-flash": {"per_minute": 15, "per_day": 1500}, 
            "gemini-1.5-pro": {"per_minute": 2, "per_day": 50},
            "gemini-2.0-experimental": {"per_minute": 2, "per_day": 50}
        }
    
    def _load_api_keys(self) -> List[str]:
        """Load API keys from environment variables."""
        keys = []
        
        # Primary key
        primary_key = os.getenv('GEMINI_API_KEY')
        if primary_key and primary_key != 'your_gemini_api_key_here':
            keys.append(primary_key)
        
        # Additional keys (GEMINI_API_KEY_2, GEMINI_API_KEY_3, etc.)
        i = 2
        while True:
            key = os.getenv(f'GEMINI_API_KEY_{i}')
            if key and key != 'your_gemini_api_key_here':
                keys.append(key)
                i += 1
            else:
                break
        
        logger.info(f"Loaded {len(keys)} API keys")
        return keys
    
    def _load_usage_data(self) -> Dict[str, Dict]:
        """Load API usage data from cache."""
        if self.usage_file.exists():
            try:
                with open(self.usage_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Initialize usage data for each key
        usage = {}
        for i, key in enumerate(self.api_keys):
            key_id = f"key_{i}"
            usage[key_id] = {
                "requests_today": 0,
                "requests_this_minute": 0,
                "last_request_time": 0,
                "last_reset_day": time.strftime("%Y-%m-%d"),
                "last_reset_minute": time.time() // 60,
                "failures": 0,
                "last_failure_time": 0
            }
        
        return usage
    
    def _save_usage_data(self):
        """Save usage data to cache."""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save usage data: {e}")
    
    def _reset_counters_if_needed(self, key_id: str):
        """Reset counters if time periods have passed."""
        current_day = time.strftime("%Y-%m-%d")
        current_minute = time.time() // 60
        
        usage = self.usage_data[key_id]
        
        # Reset daily counter
        if usage["last_reset_day"] != current_day:
            usage["requests_today"] = 0
            usage["last_reset_day"] = current_day
        
        # Reset minute counter
        if usage["last_reset_minute"] != current_minute:
            usage["requests_this_minute"] = 0
            usage["last_reset_minute"] = current_minute
    
    def get_best_api_key(self, model_name: str = "gemini-2.0-flash") -> Optional[tuple]:
        """Get the best available API key for the given model."""
        if not self.api_keys:
            logger.error("No API keys available")
            return None
        
        # Get rate limits for the model
        limits = self.rate_limits.get(model_name, self.rate_limits["gemini-2.0-flash"])
        
        available_keys = []
        
        for i, key in enumerate(self.api_keys):
            key_id = f"key_{i}"
            
            if key_id not in self.usage_data:
                continue
            
            self._reset_counters_if_needed(key_id)
            usage = self.usage_data[key_id]
            
            # Skip if recently failed (wait 5 minutes)
            if (usage["failures"] > 0 and 
                time.time() - usage["last_failure_time"] < 300):
                continue
            
            # Check rate limits
            if (usage["requests_today"] < limits["per_day"] and 
                usage["requests_this_minute"] < limits["per_minute"]):
                
                # Calculate priority (lower is better)
                priority = (
                    usage["requests_today"] * 1000 +  # Prefer less used keys
                    usage["failures"] * 10000 +       # Avoid failed keys
                    random.randint(0, 100)            # Add randomness
                )
                
                available_keys.append((key, key_id, priority))
        
        if not available_keys:
            logger.warning("No API keys available within rate limits")
            return None
        
        # Sort by priority and return the best key
        available_keys.sort(key=lambda x: x[2])
        return available_keys[0][:2]  # Return (key, key_id)
    
    def record_request(self, key_id: str, success: bool = True):
        """Record an API request."""
        if key_id not in self.usage_data:
            return
        
        usage = self.usage_data[key_id]
        usage["requests_today"] += 1
        usage["requests_this_minute"] += 1
        usage["last_request_time"] = time.time()
        
        if not success:
            usage["failures"] += 1
            usage["last_failure_time"] = time.time()
        else:
            # Reset failure count on success
            usage["failures"] = max(0, usage["failures"] - 1)
        
        self._save_usage_data()
    
    def get_usage_stats(self) -> Dict:
        """Get current usage statistics."""
        stats = {
            "total_keys": len(self.api_keys),
            "keys_status": []
        }
        
        for i, key in enumerate(self.api_keys):
            key_id = f"key_{i}"
            if key_id in self.usage_data:
                self._reset_counters_if_needed(key_id)
                usage = self.usage_data[key_id]
                
                stats["keys_status"].append({
                    "key_id": key_id,
                    "requests_today": usage["requests_today"],
                    "requests_this_minute": usage["requests_this_minute"],
                    "failures": usage["failures"],
                    "available": usage["failures"] == 0 or 
                               time.time() - usage["last_failure_time"] > 300
                })
        
        return stats


class SmartCache:
    """Advanced caching system for API responses."""
    
    def __init__(self):
        self.cache_dir = Path("cache/smart_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, content: str, operation: str, model: str) -> str:
        """Generate a cache key for the content."""
        combined = f"{operation}:{model}:{content}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def get(self, content: str, operation: str, model: str) -> Optional[Any]:
        """Get cached result if available and valid."""
        cache_key = self._get_cache_key(content, operation, model)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            # Check if cache is still valid (24 hours for most operations)
            cache_age = time.time() - cached_data.get("timestamp", 0)
            max_age = 24 * 3600  # 24 hours
            
            if cache_age < max_age:
                logger.info(f"Cache hit for operation {operation}")
                return cached_data.get("result")
            else:
                # Remove expired cache
                cache_file.unlink()
                return None
                
        except Exception as e:
            logger.error(f"Error reading cache: {e}")
            return None
    
    def set(self, content: str, operation: str, model: str, result: Any):
        """Cache the result."""
        cache_key = self._get_cache_key(content, operation, model)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            cached_data = {
                "timestamp": time.time(),
                "operation": operation,
                "model": model,
                "result": result
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cached_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Cached result for operation {operation}")
            
        except Exception as e:
            logger.error(f"Error writing cache: {e}")

# Global instances
api_rotator = APIKeyRotator()
smart_cache = SmartCache()