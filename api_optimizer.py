#!/usr/bin/env python3
"""
API optimization utilities to handle rate limits and quotas.
"""
import os
import time
import json
from pathlib import Path
import hashlib

class APIOptimizer:
    """Handles API optimization and caching to reduce API calls."""
    
    def __init__(self):
        self.cache_dir = Path("cache/api_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.quota_file = self.cache_dir / "quota_usage.json"
        self.load_quota_usage()
    
    def load_quota_usage(self):
        """Load current quota usage from file."""
        if self.quota_file.exists():
            try:
                with open(self.quota_file, 'r') as f:
                    self.quota_usage = json.load(f)
            except:
                self.quota_usage = {"daily_requests": 0, "last_reset": time.time()}
        else:
            self.quota_usage = {"daily_requests": 0, "last_reset": time.time()}
    
    def save_quota_usage(self):
        """Save quota usage to file."""
        with open(self.quota_file, 'w') as f:
            json.dump(self.quota_usage, f)
    
    def reset_daily_quota_if_needed(self):
        """Reset daily quota if 24 hours have passed."""
        current_time = time.time()
        if current_time - self.quota_usage["last_reset"] > 24 * 3600:  # 24 hours
            self.quota_usage["daily_requests"] = 0
            self.quota_usage["last_reset"] = current_time
            self.save_quota_usage()
    
    def can_make_request(self, provider="gemini", daily_limit=20):
        """Check if we can make an API request."""
        self.reset_daily_quota_if_needed()
        
        if provider == "gemini":
            return self.quota_usage["daily_requests"] < daily_limit
        
        return True  # For other providers, assume no limit
    
    def record_request(self):
        """Record an API request."""
        self.quota_usage["daily_requests"] += 1
        self.save_quota_usage()
    
    def get_cache_key(self, text_content):
        """Generate a cache key for the given content."""
        return hashlib.md5(text_content.encode()).hexdigest()
    
    def get_cached_result(self, cache_key, operation_type="evaluation"):
        """Get cached result if available."""
        cache_file = self.cache_dir / f"{operation_type}_{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return None
    
    def cache_result(self, cache_key, result, operation_type="evaluation"):
        """Cache the result."""
        cache_file = self.cache_dir / f"{operation_type}_{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(result, f)
        except:
            pass
    
    def get_remaining_requests(self, daily_limit=20):
        """Get remaining requests for today."""
        self.reset_daily_quota_if_needed()
        return daily_limit - self.quota_usage["daily_requests"]

# Global optimizer instance
api_optimizer = APIOptimizer()