"""Cache management for API responses."""

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional


class CacheManager:
    """Manages caching of API responses."""
    
    def __init__(self, cache_path: str, ttl: int = 86400):
        """
        Initialize cache manager.
        
        Args:
            cache_path: Path to cache file
            ttl: Time to live in seconds (default 24 hours)
        """
        self.cache_path = Path(cache_path).expanduser()
        self.ttl = ttl
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self) -> None:
        """Ensure cache directory exists."""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
    
    def is_valid(self) -> bool:
        """Check if cache exists and is valid."""
        if not self.cache_path.exists():
            return False
        
        cache_age = time.time() - self.cache_path.stat().st_mtime
        return cache_age < self.ttl
    
    def get(self, key: Optional[str] = None) -> Optional[Any]:
        """
        Get cached data.
        
        Args:
            key: Optional key to get specific data
            
        Returns:
            Cached data or None if not found/invalid
        """
        if not self.is_valid():
            return None
        
        try:
            with open(self.cache_path) as f:
                data = json.load(f)
            
            if key:
                return data.get(key)
            return data
        except (json.JSONDecodeError, IOError):
            return None
    
    def set(self, data: Any, key: Optional[str] = None) -> None:
        """
        Set cache data.
        
        Args:
            data: Data to cache
            key: Optional key to set specific data
        """
        if key:
            existing = self.get() or {}
            existing[key] = data
            data = existing
        
        with open(self.cache_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def clear(self) -> None:
        """Clear cache."""
        if self.cache_path.exists():
            self.cache_path.unlink()
    
    def refresh(self, fetch_func, *args, **kwargs) -> Any:
        """
        Refresh cache with new data.
        
        Args:
            fetch_func: Function to fetch new data
            *args, **kwargs: Arguments for fetch function
            
        Returns:
            Fetched data
        """
        data = fetch_func(*args, **kwargs)
        self.set(data)
        return data
    
    def get_or_fetch(self, fetch_func, *args, **kwargs) -> Any:
        """
        Get cached data or fetch if not available/invalid.
        
        Args:
            fetch_func: Function to fetch new data
            *args, **kwargs: Arguments for fetch function
            
        Returns:
            Cached or fetched data
        """
        data = self.get()
        if data is None:
            data = self.refresh(fetch_func, *args, **kwargs)
        return data