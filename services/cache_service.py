"""Simple in-memory cache service with timestamp-based expiration."""

import time
from config import Config


class CacheService:
    """
    Simple in-memory cache with timestamp-based expiration.

    For a single-user application, this is sufficient. Can be upgraded
    to Redis or similar if needed for multi-worker deployments.
    """

    def __init__(self):
        """Initialize cache storage."""
        self._cache = {}

    def get(self, key):
        """
        Get a cached value if it exists and hasn't expired.

        Args:
            key: Cache key (string)

        Returns:
            Cached value or None if not found or expired
        """
        if key not in self._cache:
            return None

        value, timestamp, duration = self._cache[key]

        # Check if cache entry has expired
        if time.time() - timestamp > duration:
            # Cache expired, remove it
            del self._cache[key]
            return None

        return value

    def set(self, key, value, duration=None):
        """
        Set a cache value with expiration.

        Args:
            key: Cache key (string)
            value: Value to cache (any type)
            duration: Expiration duration in seconds (default: from config)
        """
        if duration is None:
            duration = Config.CACHE_DURATION

        self._cache[key] = (value, time.time(), duration)

    def invalidate(self, key):
        """
        Invalidate (delete) a specific cache entry.

        Args:
            key: Cache key to invalidate
        """
        if key in self._cache:
            del self._cache[key]

    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()

    def has(self, key):
        """
        Check if a key exists in cache and hasn't expired.

        Args:
            key: Cache key to check

        Returns:
            True if key exists and is valid, False otherwise
        """
        return self.get(key) is not None

    def get_stats(self):
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats:
            {
                'total_entries': int,
                'active_entries': int,
                'expired_entries': int
            }
        """
        total_entries = len(self._cache)
        active_entries = 0
        expired_entries = 0

        current_time = time.time()

        for key in list(self._cache.keys()):
            value, timestamp, duration = self._cache[key]
            if current_time - timestamp > duration:
                expired_entries += 1
            else:
                active_entries += 1

        return {
            'total_entries': total_entries,
            'active_entries': active_entries,
            'expired_entries': expired_entries
        }

    def cleanup_expired(self):
        """
        Remove all expired cache entries.

        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = []

        for key, (value, timestamp, duration) in self._cache.items():
            if current_time - timestamp > duration:
                expired_keys.append(key)

        for key in expired_keys:
            del self._cache[key]

        return len(expired_keys)


# Global cache instance
cache = CacheService()


# Convenience functions for common cache operations

def get_cached(key):
    """Get a cached value."""
    return cache.get(key)


def set_cached(key, value, duration=None):
    """Set a cache value."""
    cache.set(key, value, duration)


def invalidate_cache(key):
    """Invalidate a cache entry."""
    cache.invalidate(key)


def clear_all_cache():
    """Clear all cache entries."""
    cache.clear()


def invalidate_dashboard_cache():
    """
    Invalidate all dashboard-related cache entries.
    Should be called whenever habit or log data is modified.
    """
    cache.invalidate('public_dashboard_data')
    cache.invalidate('public_dashboard_json')
