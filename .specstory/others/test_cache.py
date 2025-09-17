#!/usr/bin/env python3
"""
Simple test script to verify cache functionality
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from tardis_data_downloader.data.data_manager import TardisApi, SimpleCache
import time


def test_simple_cache():
    print("Testing SimpleCache...")

    # Test basic cache operations
    cache = SimpleCache(default_ttl_seconds=2)  # 2 second TTL

    # Test cache miss
    result = cache.get("http://test.com")
    assert result is None, "Should return None for cache miss"
    print("✓ Cache miss works correctly")

    # Test cache set and get
    test_data = {"test": "data"}
    cache.set("http://test.com", test_data)
    result = cache.get("http://test.com")
    assert result == test_data, "Should return cached data"
    print("✓ Cache set and get works correctly")

    # Test TTL expiration
    time.sleep(3)  # Wait for TTL to expire
    result = cache.get("http://test.com")
    assert result is None, "Should return None after TTL expires"
    print("✓ TTL expiration works correctly")

    # Test cache stats
    cache.set("http://test1.com", {"data": 1})
    cache.set("http://test2.com", {"data": 2})
    stats = cache.get_stats()
    assert stats["total_entries"] == 2, "Should have 2 entries"
    print("✓ Cache stats work correctly")

    # Test cache clear
    cache.clear()
    stats = cache.get_stats()
    assert stats["total_entries"] == 0, "Should have 0 entries after clear"
    print("✓ Cache clear works correctly")

    print("All SimpleCache tests passed! ✓")


def test_tardis_api_cache():
    print("\nTesting TardisApi cache functionality...")

    # Test API without cache
    api_no_cache = TardisApi(enable_cache=False)
    assert not api_no_cache.is_cache_enabled(), "Should report cache as disabled"
    assert api_no_cache.cache is None, "Should not have cache instance"
    print("✓ API without cache works correctly")

    # Test API with cache
    api_with_cache = TardisApi(enable_cache=True, cache_ttl_seconds=5)
    assert api_with_cache.is_cache_enabled(), "Should report cache as enabled"
    assert api_with_cache.cache is not None, "Should have cache instance"
    print("✓ API with cache works correctly")

    # Test cache management methods
    api_with_cache.clear_cache()
    stats = api_with_cache.get_cache_stats()
    assert "total_entries" in stats, "Should return valid stats"
    print("✓ Cache management methods work correctly")

    print("All TardisApi cache tests passed! ✓")


if __name__ == "__main__":
    test_simple_cache()
    test_tardis_api_cache()
    print("\n🎉 All cache functionality tests passed!")
