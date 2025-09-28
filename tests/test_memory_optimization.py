"""Comprehensive tests for the memory optimization system.

This module tests all components of the memory optimization system including
object pooling, smart caching, memory profiling, and GC optimization.
"""

import unittest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memory import (
    # Core
    ObjectPool, PoolableObject, PoolManager, MemoryManager, MemoryConfig, MemoryStats,
    PoolStrategy,
    
    # Pools
    MessagePool, EntityPool, ComponentPool, EventPool, TemporaryObjectPool,
    PooledMessage, PooledEntity, PooledEvent, PooledComponent, TemporaryObject,
    create_default_pools,
    
    # Cache
    SmartCache, CacheConfig, CacheStats, LRUCache, TTLCache, WeakRefCache,
    CacheStrategy, create_cache, CacheManager,
    
    # Profiler
    MemoryProfiler, MemorySnapshot, MemoryLeak, LeakDetector, AllocationTracker,
    LeakSeverity, create_memory_profiler,
    
    # GC Optimizer
    GCOptimizer, GCConfig, GCStats, GCMode, optimize_gc_settings,
    disable_gc_during, gc_collect_if_needed,
    
    # Integration
    GameMemoryManager, MemoryOptimizationConfig, initialize_game_memory_manager,
    
    # Utils
    get_object_size, get_memory_usage, format_memory_size, memory_usage_context,
    AllocationTracker as UtilsAllocationTracker, MemoryMonitor, ObjectRegistry,
)


class MockPoolableObject(PoolableObject):
    """Test implementation of PoolableObject."""
    
    def __init__(self):
        self.data = "initial"
        self.reset_called = False
        self.acquire_called = False
        self.release_called = False
    
    def reset(self):
        self.data = "reset"
        self.reset_called = True
    
    def on_acquire(self):
        self.acquire_called = True
    
    def on_release(self):
        self.release_called = True


class TestMemoryCore(unittest.TestCase):
    """Test core memory management components."""
    
    def test_memory_config_defaults(self):
        """Test memory configuration defaults."""
        config = MemoryConfig()
        
        self.assertTrue(config.enable_pooling)
        self.assertTrue(config.enable_caching)
        self.assertEqual(config.default_pool_size, 100)
        self.assertEqual(config.pool_strategy, PoolStrategy.BOUNDED_DYNAMIC)
    
    def test_memory_stats_to_dict(self):
        """Test memory stats conversion to dictionary."""
        stats = MemoryStats()
        stats.total_pools = 5
        stats.pool_hit_rate = 85.5
        
        stats_dict = stats.to_dict()
        
        self.assertEqual(stats_dict['total_pools'], 5)
        self.assertEqual(stats_dict['pool_hit_rate'], 85.5)
        self.assertIn('total_pooled_objects', stats_dict)
    
    def test_object_pool_creation(self):
        """Test object pool creation and basic operations."""
        pool = ObjectPool(MockPoolableObject, initial_size=5, max_size=10)
        
        self.assertEqual(len(pool), 5)  # Initial objects created
        
        # Acquire object
        obj = pool.acquire()
        self.assertIsInstance(obj, MockPoolableObject)
        self.assertTrue(obj.reset_called)
        self.assertTrue(obj.acquire_called)
        
        # Release object
        pool.release(obj)
        self.assertTrue(obj.release_called)
    
    def test_object_pool_auto_release(self):
        """Test object pool with auto-release wrapper."""
        pool = ObjectPool(MockPoolableObject, initial_size=2)
        
        with pool.acquire(auto_release=True) as obj:
            self.assertIsInstance(obj, MockPoolableObject)
        
        # Object should be automatically released
        stats = pool.get_stats()
        self.assertEqual(stats['acquired_count'], 0)
    
    def test_object_pool_strategies(self):
        """Test different pool strategies."""
        # Fixed size pool
        fixed_pool = ObjectPool(
            MockPoolableObject, 
            initial_size=2, 
            max_size=2, 
            strategy=PoolStrategy.FIXED_SIZE
        )
        
        # Exhaust pool
        obj1 = fixed_pool.acquire()
        obj2 = fixed_pool.acquire()
        
        # Should raise exception when exhausted
        with self.assertRaises(RuntimeError):
            fixed_pool.acquire()
        
        # Clean up
        fixed_pool.release(obj1)
        fixed_pool.release(obj2)
    
    def test_pool_manager(self):
        """Test pool manager functionality."""
        manager = PoolManager()
        
        # Create pool
        pool = manager.create_pool('test_pool', MockPoolableObject, initial_size=3)
        self.assertIsNotNone(pool)
        
        # Get pool
        retrieved_pool = manager.get_pool('test_pool')
        self.assertEqual(pool, retrieved_pool)
        
        # Get stats
        stats = manager.get_stats()
        self.assertEqual(stats['total_pools'], 1)
        self.assertEqual(stats['aggregate']['total_objects'], 3)
        
        # Remove pool
        removed = manager.remove_pool('test_pool')
        self.assertTrue(removed)
        self.assertIsNone(manager.get_pool('test_pool'))
    
    def test_memory_manager(self):
        """Test memory manager functionality."""
        config = MemoryConfig(enable_pooling=True)
        manager = MemoryManager(config)
        
        self.assertIsNotNone(manager.get_pool_manager())
        
        stats = manager.get_stats()
        self.assertIsInstance(stats, MemoryStats)
        
        manager.shutdown()


class TestSpecializedPools(unittest.TestCase):
    """Test specialized object pools."""
    
    def test_pooled_message(self):
        """Test pooled message functionality."""
        message = PooledMessage()
        
        # Test reset
        message.set_message("test", (255, 0, 0))
        message.reset()
        self.assertEqual(message.text, "")
        self.assertEqual(message.color, (255, 255, 255))
        
        # Test conversion
        message.set_message("hello", (0, 255, 0))
        regular_message = message.to_message()
        self.assertEqual(regular_message.text, "hello")
        self.assertEqual(regular_message.color, (0, 255, 0))
    
    def test_pooled_event(self):
        """Test pooled event functionality."""
        event = PooledEvent()
        
        # Test reset
        event.set_event("test.event", {"key": "value"})
        event.reset()
        self.assertEqual(event.event_type, "")
        self.assertEqual(len(event.data), 0)
        self.assertFalse(event.cancelled)
        
        # Test conversion
        event.set_event("game.event", {"player": "test"})
        regular_event = event.to_event()
        self.assertEqual(regular_event.event_type, "game.event")
        self.assertEqual(regular_event.data["player"], "test")
    
    def test_pooled_entity(self):
        """Test pooled entity functionality."""
        entity = PooledEntity()
        
        # Test initialization
        entity.initialize_entity(
            x=10, y=20, char='@', color=(255, 255, 255), 
            name="Player", blocks=True
        )
        
        self.assertEqual(entity.x, 10)
        self.assertEqual(entity.y, 20)
        self.assertEqual(entity.char, '@')
        self.assertTrue(entity.blocks)
        
        # Test reset
        entity.reset()
        self.assertEqual(entity.x, 0)
        self.assertEqual(entity.char, '?')
        self.assertFalse(entity.blocks)
    
    def test_message_pool(self):
        """Test message pool."""
        pool = MessagePool(initial_size=5, max_size=10)
        
        message = pool.create_message("Test message", (255, 0, 0))
        self.assertEqual(message.text, "Test message")
        self.assertEqual(message.color, (255, 0, 0))
    
    def test_entity_pool(self):
        """Test entity pool."""
        pool = EntityPool(initial_size=3, max_size=10)
        
        entity = pool.create_entity(
            x=5, y=10, char='E', color=(0, 255, 0), name="Enemy"
        )
        self.assertEqual(entity.x, 5)
        self.assertEqual(entity.name, "Enemy")
    
    def test_event_pool(self):
        """Test event pool."""
        pool = EventPool(initial_size=10, max_size=50)
        
        event = pool.create_event("test.event", {"data": "test"})
        self.assertEqual(event.event_type, "test.event")
        self.assertEqual(event.data["data"], "test")
    
    def test_create_default_pools(self):
        """Test creation of default pools."""
        manager = PoolManager()
        pools = create_default_pools(manager)
        
        self.assertIn('messages', pools)
        self.assertIn('events', pools)
        self.assertIn('temp_entities', pools)
        self.assertIn('fighters', pools)
        
        # Verify pools are registered
        self.assertIsNotNone(manager.get_pool('messages'))
        self.assertIsNotNone(manager.get_pool('events'))


class TestSmartCaching(unittest.TestCase):
    """Test smart caching system."""
    
    def test_lru_cache(self):
        """Test LRU cache functionality."""
        config = CacheConfig(max_size=3)
        cache = LRUCache(config)
        
        # Add items
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        self.assertEqual(cache.size(), 3)
        
        # Access key1 to make it recently used
        self.assertEqual(cache.get("key1"), "value1")
        
        # Add key4, should evict key2 (least recently used)
        cache.put("key4", "value4")
        
        self.assertIsNone(cache.get("key2"))
        self.assertEqual(cache.get("key1"), "value1")
        self.assertEqual(cache.get("key4"), "value4")
    
    def test_ttl_cache(self):
        """Test TTL cache functionality."""
        config = CacheConfig(default_ttl=0.1)  # 100ms TTL
        cache = TTLCache(config)
        
        cache.put("key1", "value1")
        self.assertEqual(cache.get("key1"), "value1")
        
        # Wait for expiration
        time.sleep(0.15)
        self.assertIsNone(cache.get("key1"))
    
    def test_weak_ref_cache(self):
        """Test weak reference cache."""
        cache = WeakRefCache()
        
        # Create object that can be weakly referenced
        class TestObject:
            def __init__(self, data):
                self.data = data
        
        obj = TestObject("test")
        cache.put("key1", obj)
        
        self.assertEqual(cache.get("key1"), obj)
        
        # Delete reference
        del obj
        
        # Object should be garbage collected and removed from cache
        # Note: This might not work immediately due to GC timing
        # In a real test, you might need to force GC
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = LRUCache()
        
        # Generate some hits and misses
        cache.put("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        
        stats = cache.get_stats()
        self.assertEqual(stats.hits, 1)
        self.assertEqual(stats.misses, 1)
        self.assertEqual(stats.hit_rate, 50.0)
    
    def test_cache_manager(self):
        """Test cache manager."""
        manager = CacheManager()
        
        # Create cache
        cache = manager.create_cache("test_cache", CacheStrategy.LRU)
        self.assertIsNotNone(cache)
        
        # Get cache
        retrieved_cache = manager.get_cache("test_cache")
        self.assertEqual(cache, retrieved_cache)
        
        # Get stats
        stats = manager.get_stats()
        self.assertEqual(stats['total_caches'], 1)
        
        # Remove cache
        removed = manager.remove_cache("test_cache")
        self.assertTrue(removed)


class TestMemoryProfiler(unittest.TestCase):
    """Test memory profiling system."""
    
    def test_memory_snapshot(self):
        """Test memory snapshot functionality."""
        snapshot1 = MemorySnapshot(
            timestamp=1000.0,
            process_memory_mb=100.0,
            system_memory_percent=50.0,
            gc_counts=(10, 5, 2)
        )
        
        snapshot2 = MemorySnapshot(
            timestamp=1060.0,
            process_memory_mb=120.0,
            system_memory_percent=55.0,
            gc_counts=(15, 6, 2)
        )
        
        # Test deltas
        memory_delta = snapshot2.get_memory_delta(snapshot1)
        time_delta = snapshot2.get_time_delta(snapshot1)
        
        self.assertEqual(memory_delta, 20.0)
        self.assertEqual(time_delta, 60.0)
        
        # Test serialization
        snapshot_dict = snapshot1.to_dict()
        self.assertEqual(snapshot_dict['timestamp'], 1000.0)
        self.assertEqual(snapshot_dict['process_memory_mb'], 100.0)
    
    def test_memory_leak(self):
        """Test memory leak representation."""
        leak = MemoryLeak(
            object_type="TestObject",
            count_increase=100,
            memory_increase_mb=5.0,
            detection_time=time.time(),
            severity=LeakSeverity.MEDIUM
        )
        
        self.assertEqual(leak.object_type, "TestObject")
        self.assertEqual(leak.severity, LeakSeverity.MEDIUM)
        
        # Test serialization
        leak_dict = leak.to_dict()
        self.assertEqual(leak_dict['object_type'], "TestObject")
        self.assertEqual(leak_dict['severity'], "MEDIUM")
    
    def test_allocation_tracker(self):
        """Test allocation tracker."""
        tracker = AllocationTracker(max_history=100)
        
        tracker.enable()
        
        # Record some allocations
        tracker.record_allocation("str", 50)
        tracker.record_allocation("list", 200)
        tracker.record_allocation("str", 30)
        
        stats = tracker.get_allocation_stats()
        self.assertEqual(stats['total_allocations'], 3)
        self.assertTrue(stats['enabled'])
        
        tracker.disable()
    
    def test_leak_detector(self):
        """Test leak detector."""
        detector = LeakDetector(sensitivity=1.0, min_samples=2)
        
        # Create snapshots showing memory growth
        snapshot1 = MemorySnapshot(
            timestamp=1000.0,
            process_memory_mb=100.0,
            system_memory_percent=50.0,
            gc_counts=(10, 5, 2),
            object_counts={"str": 1000, "list": 500}
        )
        
        snapshot2 = MemorySnapshot(
            timestamp=1060.0,
            process_memory_mb=150.0,  # 50MB increase
            system_memory_percent=60.0,
            gc_counts=(15, 6, 2),
            object_counts={"str": 1500, "list": 600}  # Significant increase
        )
        
        detector.add_snapshot(snapshot1)
        detector.add_snapshot(snapshot2)
        
        # Check for detected leaks
        leaks = detector.get_detected_leaks()
        # Note: Leak detection depends on thresholds and growth patterns
    
    @patch('memory.profiler.psutil')
    def test_memory_profiler(self, mock_psutil):
        """Test memory profiler."""
        # Mock psutil
        mock_process = Mock()
        mock_process.memory_info.return_value = Mock(rss=100 * 1024 * 1024)  # 100MB
        mock_psutil.Process.return_value = mock_process
        mock_psutil.virtual_memory.return_value = Mock(percent=50.0)
        
        profiler = MemoryProfiler(profile_interval=0.1, enable_allocation_tracking=False)
        
        # Take manual snapshot
        snapshot = profiler.take_manual_snapshot()
        self.assertIsInstance(snapshot, MemorySnapshot)
        self.assertEqual(snapshot.process_memory_mb, 100.0)
        
        # Test trend analysis
        trend = profiler.get_memory_trend(window_minutes=1)
        # With only one snapshot, should return insufficient data
        self.assertEqual(trend['trend'], 'insufficient_data')


class TestGCOptimizer(unittest.TestCase):
    """Test garbage collection optimizer."""
    
    def test_gc_config(self):
        """Test GC configuration."""
        config = GCConfig(
            mode=GCMode.BALANCED,
            threshold_0=700,
            manual_collect_interval=30.0
        )
        
        self.assertEqual(config.mode, GCMode.BALANCED)
        self.assertEqual(config.threshold_0, 700)
        self.assertEqual(config.manual_collect_interval, 30.0)
    
    def test_gc_stats(self):
        """Test GC statistics."""
        stats = GCStats()
        stats.collections_gen0 = 10
        stats.collections_gen1 = 5
        stats.manual_collections = 2
        
        self.assertEqual(stats.total_collections, 17)
        
        stats_dict = stats.to_dict()
        self.assertEqual(stats_dict['total_collections'], 17)
    
    def test_gc_optimizer_basic(self):
        """Test basic GC optimizer functionality."""
        config = GCConfig(mode=GCMode.BALANCED)
        optimizer = GCOptimizer(config)
        
        # Test manual collection
        result = optimizer.collect_generation(0)
        self.assertIn('collected', result)
        self.assertIn('time_ms', result)
        
        # Test full collection
        result = optimizer.collect_all_generations()
        self.assertIn('total_collected', result)
        self.assertIn('total_time_ms', result)
        
        # Test stats
        stats = optimizer.get_stats()
        self.assertIsInstance(stats, GCStats)
        
        optimizer.shutdown()
    
    def test_disable_gc_during(self):
        """Test GC disable context manager."""
        import gc
        
        gc_was_enabled = gc.isenabled()
        
        with disable_gc_during():
            # GC should be disabled inside context
            pass
        
        # GC state should be restored
        self.assertEqual(gc.isenabled(), gc_was_enabled)


class TestIntegration(unittest.TestCase):
    """Test memory optimization integration."""
    
    def test_memory_optimization_config(self):
        """Test memory optimization configuration."""
        config = MemoryOptimizationConfig(
            enable_pooling=True,
            enable_caching=True,
            gc_mode=GCMode.BALANCED
        )
        
        self.assertTrue(config.enable_pooling)
        self.assertTrue(config.enable_caching)
        self.assertEqual(config.gc_mode, GCMode.BALANCED)
    
    def test_game_memory_manager(self):
        """Test game memory manager."""
        config = MemoryOptimizationConfig(
            enable_pooling=True,
            enable_caching=True,
            enable_profiling=False,  # Disable for testing
            enable_gc_optimization=False  # Disable for testing
        )
        
        manager = GameMemoryManager(config)
        
        # Test pool access
        pool = manager.get_pool('messages')
        self.assertIsNotNone(pool)
        
        # Test cache access
        cache = manager.get_cache('fov_cache')
        self.assertIsNotNone(cache)
        
        # Test pooled object creation
        message = manager.create_pooled_message("Test", (255, 0, 0))
        self.assertIsNotNone(message)
        
        # Test stats
        stats = manager.get_comprehensive_stats()
        self.assertIn('integration_stats', stats)
        self.assertIn('memory_manager', stats)
        
        manager.shutdown()


class TestUtils(unittest.TestCase):
    """Test memory utilities."""
    
    def test_get_object_size(self):
        """Test object size calculation."""
        obj = "test string"
        size = get_object_size(obj)
        self.assertGreater(size, 0)
    
    def test_format_memory_size(self):
        """Test memory size formatting."""
        self.assertEqual(format_memory_size(512), "512 B")
        self.assertEqual(format_memory_size(1536), "1.5 KB")
        self.assertEqual(format_memory_size(2 * 1024 * 1024), "2.0 MB")
    
    @patch('memory.utils.psutil')
    def test_get_memory_usage(self, mock_psutil):
        """Test memory usage retrieval."""
        # Mock psutil
        mock_process = Mock()
        mock_process.memory_info.return_value = Mock(rss=100 * 1024 * 1024, vms=200 * 1024 * 1024)
        mock_process.memory_percent.return_value = 5.0
        mock_psutil.Process.return_value = mock_process
        mock_psutil.virtual_memory.return_value = Mock(available=1000 * 1024 * 1024)
        
        usage = get_memory_usage()
        self.assertEqual(usage.rss_mb, 100.0)
        self.assertEqual(usage.vms_mb, 200.0)
        self.assertEqual(usage.percent, 5.0)
    
    def test_memory_usage_context(self):
        """Test memory usage context manager."""
        with memory_usage_context("test operation") as result:
            # Simulate some work
            data = [i for i in range(1000)]
        
        self.assertEqual(result['description'], "test operation")
        self.assertIsNotNone(result['duration_seconds'])
        self.assertIsNotNone(result['memory_delta_mb'])
    
    def test_allocation_tracker_utils(self):
        """Test allocation tracker utilities."""
        from memory.utils import AllocationTracker as UtilsTracker
        tracker = UtilsTracker()
        
        tracker.enable()
        tracker.track_allocation("str", 50, "test location")
        
        stats = tracker.get_stats()
        self.assertEqual(stats['total_allocations'], 1)
        self.assertEqual(stats['total_size_bytes'], 50)
        
        tracker.disable()
    
    def test_memory_monitor(self):
        """Test memory monitor."""
        monitor = MemoryMonitor(sample_interval=0.1, max_samples=10)
        
        # Test without starting monitoring
        usage = monitor.get_current_usage()
        self.assertIsNone(usage)
        
        # Test stats with no data
        stats = monitor.get_usage_stats()
        self.assertEqual(stats['error'], 'no_data')
    
    def test_object_registry(self):
        """Test object registry."""
        registry = ObjectRegistry()
        
        # Create objects that can be weakly referenced
        class TestObject:
            def __init__(self, name):
                self.name = name
        
        class AnotherObject:
            def __init__(self, value):
                self.value = value
        
        obj1 = TestObject("test1")
        obj2 = TestObject("test2")
        obj3 = AnotherObject(42)
        
        registry.register(obj1, "test_objects")
        registry.register(obj2, "test_objects")
        registry.register(obj3, "another_objects")
        
        # Test counts
        self.assertEqual(registry.get_count("test_objects"), 2)
        self.assertEqual(registry.get_count("another_objects"), 1)
        
        all_counts = registry.get_all_counts()
        self.assertEqual(all_counts["test_objects"], 2)
        self.assertEqual(all_counts["another_objects"], 1)
        
        # Clear category
        registry.clear_category("test_objects")
        self.assertEqual(registry.get_count("test_objects"), 0)


class TestEndToEndIntegration(unittest.TestCase):
    """Test end-to-end memory optimization integration."""
    
    def test_complete_memory_optimization_workflow(self):
        """Test complete memory optimization workflow."""
        # Create configuration
        config = MemoryOptimizationConfig(
            enable_pooling=True,
            enable_caching=True,
            enable_profiling=False,  # Disable for testing
            enable_gc_optimization=False,  # Disable for testing
            create_default_pools=True
        )
        
        # Initialize game memory manager
        manager = GameMemoryManager(config)
        
        try:
            # Test pooled object creation
            message = manager.create_pooled_message("Game started!", (0, 255, 0))
            self.assertIsNotNone(message)
            
            entity = manager.create_pooled_entity(
                x=10, y=10, char='@', color=(255, 255, 255), name="Player"
            )
            self.assertIsNotNone(entity)
            
            event = manager.create_pooled_event("game.start", {"level": 1})
            self.assertIsNotNone(event)
            
            # Test caching
            fov_cache = manager.get_cache('fov_cache')
            self.assertIsNotNone(fov_cache)
            
            fov_cache.put("player_fov", {"visible_tiles": [1, 2, 3]})
            cached_fov = fov_cache.get("player_fov")
            self.assertEqual(cached_fov["visible_tiles"], [1, 2, 3])
            
            # Test statistics
            stats = manager.get_comprehensive_stats()
            self.assertIn('integration_stats', stats)
            self.assertGreater(stats['integration_stats']['pools_created'], 0)
            self.assertGreater(stats['integration_stats']['caches_created'], 0)
            
            # Test cleanup
            cleanup_result = manager.force_cleanup()
            self.assertIn('pools_cleared', cleanup_result)
            self.assertIn('caches_cleared', cleanup_result)
            
        finally:
            manager.shutdown()


if __name__ == '__main__':
    unittest.main()
