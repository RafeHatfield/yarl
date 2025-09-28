"""Demonstration of the memory optimization system.

This script showcases the capabilities of the memory optimization system
including object pooling, smart caching, memory profiling, and GC optimization.
"""

import time
import sys
import os
from typing import List

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from memory import (
    # Core components
    MemoryManager, MemoryConfig, PoolManager, ObjectPool, PoolableObject,
    PoolStrategy,
    
    # Specialized pools
    MessagePool, EntityPool, EventPool, PooledMessage, PooledEntity, PooledEvent,
    create_default_pools,
    
    # Caching
    CacheManager, CacheConfig, CacheStrategy, LRUCache, TTLCache,
    
    # Profiling
    MemoryProfiler, create_memory_profiler, LeakDetector,
    
    # GC Optimization
    GCOptimizer, GCConfig, GCMode, disable_gc_during,
    
    # Integration
    GameMemoryManager, MemoryOptimizationConfig,
    
    # Utilities
    get_memory_usage, format_memory_size, memory_usage_context,
    get_global_allocation_tracker, get_global_memory_monitor,
)


def print_header(title: str) -> None:
    """Print a formatted header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_subheader(title: str) -> None:
    """Print a formatted subheader."""
    print(f"\n{'-' * 40}")
    print(f"  {title}")
    print(f"{'-' * 40}")


def demo_object_pooling() -> None:
    """Demonstrate object pooling capabilities."""
    print_header("OBJECT POOLING DEMONSTRATION")
    
    # Create a simple poolable object
    class GameMessage(PoolableObject):
        def __init__(self):
            self.text = ""
            self.color = (255, 255, 255)
            self.timestamp = 0.0
        
        def reset(self):
            self.text = ""
            self.color = (255, 255, 255)
            self.timestamp = 0.0
        
        def set_message(self, text: str, color: tuple = (255, 255, 255)):
            self.text = text
            self.color = color
            self.timestamp = time.time()
    
    print("Creating object pool with 10 initial objects...")
    pool = ObjectPool(GameMessage, initial_size=10, max_size=50)
    
    print(f"Pool created: {pool}")
    print(f"Initial stats: {pool.get_stats()}")
    
    print("\nAcquiring and using objects from pool...")
    messages = []
    
    # Acquire multiple objects
    for i in range(5):
        msg = pool.acquire()
        msg.set_message(f"Message {i+1}", (255, i*50, 0))
        messages.append(msg)
        print(f"  Created: '{msg.text}' with color {msg.color}")
    
    print(f"\nPool stats after acquisition: {pool.get_stats()}")
    
    # Release objects back to pool
    print("\nReleasing objects back to pool...")
    for msg in messages:
        pool.release(msg)
    
    print(f"Pool stats after release: {pool.get_stats()}")
    
    # Demonstrate auto-release with context manager
    print("\nUsing auto-release context manager...")
    with pool.acquire(auto_release=True) as msg:
        msg.set_message("Auto-released message", (0, 255, 0))
        print(f"  Using: '{msg.text}'")
    
    print(f"Pool stats after auto-release: {pool.get_stats()}")


def demo_specialized_pools() -> None:
    """Demonstrate specialized pools for game objects."""
    print_header("SPECIALIZED POOLS DEMONSTRATION")
    
    # Create pool manager and default pools
    print("Creating pool manager with default pools...")
    manager = PoolManager()
    pools = create_default_pools(manager)
    
    print(f"Created {len(pools)} default pools:")
    for name, pool in pools.items():
        stats = pool.get_stats()
        print(f"  {name}: {stats['total_count']} objects, hit rate: {stats['hit_rate']:.1f}%")
    
    # Demonstrate message pool
    print_subheader("Message Pool")
    message_pool = pools['messages']
    
    combat_messages = []
    for i in range(3):
        msg = message_pool.acquire(auto_release=True)
        msg.set_message(f"You hit the orc for {i+5} damage!", (255, 100, 100))
        combat_messages.append(msg)
        print(f"  Combat: {msg.text}")
    
    # Demonstrate entity pool
    print_subheader("Entity Pool")
    entity_pool = pools['temp_entities']
    
    temp_entities = []
    for i in range(2):
        entity = entity_pool.acquire(auto_release=True)
        entity.initialize_entity(
            x=i*10, y=i*5, char='*', color=(255, 255, 0), 
            name=f"Effect_{i}", blocks=False
        )
        temp_entities.append(entity)
        print(f"  Effect: {entity.name} at ({entity.x}, {entity.y})")
    
    # Demonstrate event pool
    print_subheader("Event Pool")
    event_pool = pools['events']
    
    game_events = []
    for event_type in ['player.move', 'enemy.attack', 'item.pickup']:
        event = event_pool.acquire(auto_release=True)
        event.set_event(event_type, {'timestamp': time.time()})
        game_events.append(event)
        print(f"  Event: {event.event_type}")
    
    # Show final stats
    print_subheader("Final Pool Statistics")
    manager_stats = manager.get_stats()
    print(f"Total pools: {manager_stats['total_pools']}")
    print(f"Total objects: {manager_stats['aggregate']['total_objects']}")
    print(f"Average hit rate: {manager_stats['aggregate']['average_hit_rate']:.1f}%")


def demo_smart_caching() -> None:
    """Demonstrate smart caching capabilities."""
    print_header("SMART CACHING DEMONSTRATION")
    
    # Create cache manager
    cache_manager = CacheManager()
    
    # Demonstrate LRU Cache
    print_subheader("LRU Cache")
    lru_cache = cache_manager.create_cache("lru_demo", CacheStrategy.LRU, 
                                          CacheConfig(max_size=3))
    
    print("Adding items to LRU cache (max size: 3)...")
    for i in range(5):
        key = f"key_{i}"
        value = f"value_{i}"
        lru_cache.put(key, value)
        print(f"  Added: {key} -> {value}")
    
    print("\nCache contents after adding 5 items:")
    for i in range(5):
        key = f"key_{i}"
        value = lru_cache.get(key)
        status = "HIT" if value else "MISS"
        print(f"  {key}: {value} ({status})")
    
    lru_stats = lru_cache.get_stats()
    print(f"\nLRU Cache stats: {lru_stats.hits} hits, {lru_stats.misses} misses, "
          f"{lru_stats.hit_rate:.1f}% hit rate")
    
    # Demonstrate TTL Cache
    print_subheader("TTL Cache")
    ttl_cache = cache_manager.create_cache("ttl_demo", CacheStrategy.TTL,
                                          CacheConfig(default_ttl=2.0))
    
    print("Adding items to TTL cache (2 second TTL)...")
    ttl_cache.put("temp_data", {"calculation": "expensive_result"})
    print("  Added: temp_data -> expensive_result")
    
    print("Retrieving immediately:")
    result = ttl_cache.get("temp_data")
    print(f"  Result: {result} ({'HIT' if result else 'MISS'})")
    
    print("Waiting 2.5 seconds for expiration...")
    time.sleep(2.5)
    
    print("Retrieving after expiration:")
    result = ttl_cache.get("temp_data")
    print(f"  Result: {result} ({'HIT' if result else 'MISS'})")
    
    # Show cache manager stats
    print_subheader("Cache Manager Statistics")
    manager_stats = cache_manager.get_stats()
    print(f"Total caches: {manager_stats['total_caches']}")
    print(f"Total hits: {manager_stats['aggregate']['total_hits']}")
    print(f"Total misses: {manager_stats['aggregate']['total_misses']}")
    print(f"Average hit rate: {manager_stats['aggregate']['average_hit_rate']:.1f}%")


def demo_memory_profiling() -> None:
    """Demonstrate memory profiling capabilities."""
    print_header("MEMORY PROFILING DEMONSTRATION")
    
    # Create memory profiler
    print("Creating memory profiler...")
    profiler = create_memory_profiler(profile_interval=1.0, enable_allocation_tracking=True)
    
    # Take initial snapshot
    print("Taking initial memory snapshot...")
    initial_snapshot = profiler.take_manual_snapshot()
    print(f"  Initial memory: {initial_snapshot.process_memory_mb:.1f} MB")
    print(f"  System memory: {initial_snapshot.system_memory_percent:.1f}%")
    
    # Simulate memory usage
    print("\nSimulating memory usage...")
    data_structures = []
    
    for i in range(3):
        # Create some data structures
        large_list = [j for j in range(10000)]
        large_dict = {f"key_{j}": f"value_{j}" for j in range(5000)}
        data_structures.append((large_list, large_dict))
        
        # Take snapshot
        snapshot = profiler.take_manual_snapshot()
        print(f"  Step {i+1}: {snapshot.process_memory_mb:.1f} MB "
              f"(+{snapshot.process_memory_mb - initial_snapshot.process_memory_mb:.1f} MB)")
        
        time.sleep(0.5)
    
    # Analyze memory trend
    print("\nAnalyzing memory trend...")
    trend = profiler.get_memory_trend(window_minutes=1)
    if trend['trend'] != 'no_data' and trend['trend'] != 'insufficient_data':
        print(f"  Trend: {trend['trend']}")
        print(f"  Memory delta: {trend['memory_delta_mb']:.1f} MB")
        print(f"  Growth rate: {trend['growth_rate_mb_per_hour']:.1f} MB/hour")
    else:
        print(f"  Trend analysis: {trend['trend']}")
    
    # Get leak report
    print("\nLeak detection report...")
    leak_report = profiler.get_leak_report()
    print(f"  Total leaks detected: {leak_report['total_leaks']}")
    print(f"  Critical leaks: {leak_report['critical_leaks']}")
    print(f"  High severity leaks: {leak_report['high_leaks']}")
    
    # Clean up
    del data_structures
    profiler.shutdown()


def demo_gc_optimization() -> None:
    """Demonstrate garbage collection optimization."""
    print_header("GC OPTIMIZATION DEMONSTRATION")
    
    # Create GC optimizer
    print("Creating GC optimizer with balanced mode...")
    config = GCConfig(mode=GCMode.BALANCED, log_collections=True)
    optimizer = GCOptimizer(config)
    
    # Show initial GC info
    print("Initial GC information:")
    gc_info = optimizer.get_gc_info()
    print(f"  Enabled: {gc_info['enabled']}")
    print(f"  Mode: {gc_info['mode']}")
    if gc_info['thresholds']:
        print(f"  Thresholds: {gc_info['thresholds']}")
    
    # Demonstrate manual collection
    print("\nPerforming manual garbage collection...")
    result = optimizer.collect_all_generations()
    print(f"  Collected {result['total_collected']} objects in {result['total_time_ms']:.2f}ms")
    
    # Demonstrate GC disable context
    print("\nDemonstrating GC disable context...")
    with disable_gc_during():
        print("  GC is temporarily disabled during this block")
        # Simulate critical section work
        temp_data = [i for i in range(1000)]
        del temp_data
    print("  GC is re-enabled after the block")
    
    # Show GC statistics
    print("\nGC Statistics:")
    stats = optimizer.get_stats()
    print(f"  Generation 0 collections: {stats.collections_gen0}")
    print(f"  Generation 1 collections: {stats.collections_gen1}")
    print(f"  Generation 2 collections: {stats.collections_gen2}")
    print(f"  Manual collections: {stats.manual_collections}")
    print(f"  Total GC time: {stats.total_gc_time_ms:.2f}ms")
    print(f"  Average GC time: {stats.average_gc_time_ms:.2f}ms")
    
    optimizer.shutdown()


def demo_integrated_system() -> None:
    """Demonstrate the integrated memory optimization system."""
    print_header("INTEGRATED MEMORY OPTIMIZATION SYSTEM")
    
    # Create comprehensive configuration
    config = MemoryOptimizationConfig(
        enable_pooling=True,
        enable_caching=True,
        enable_profiling=False,  # Disable for demo
        enable_gc_optimization=True,
        create_default_pools=True,
        gc_mode=GCMode.BALANCED
    )
    
    print("Initializing integrated memory optimization system...")
    memory_manager = GameMemoryManager(config)
    
    # Demonstrate integrated usage
    print("\nUsing integrated memory optimization:")
    
    # Create pooled objects
    print("  Creating pooled game objects...")
    message = memory_manager.create_pooled_message("Welcome to the game!", (0, 255, 0))
    print(f"    Message: {message.text}")
    
    entity = memory_manager.create_pooled_entity(
        x=25, y=15, char='@', color=(255, 255, 255), name="Hero"
    )
    print(f"    Entity: {entity.name} at ({entity.x}, {entity.y})")
    
    event = memory_manager.create_pooled_event("game.start", {"level": 1, "difficulty": "normal"})
    print(f"    Event: {event.event_type} with data {event.data}")
    
    # Use caching
    print("  Using smart caching...")
    fov_cache = memory_manager.get_cache('fov_cache')
    pathfinding_cache = memory_manager.get_cache('pathfinding_cache')
    
    # Cache some game data
    fov_cache.put("player_fov", {"visible": [(x, y) for x in range(5) for y in range(5)]})
    pathfinding_cache.put("path_to_exit", {"path": [(1, 1), (2, 2), (3, 3)]})
    
    print("    Cached FOV and pathfinding data")
    
    # Retrieve cached data
    cached_fov = fov_cache.get("player_fov")
    cached_path = pathfinding_cache.get("path_to_exit")
    
    print(f"    Retrieved FOV: {len(cached_fov['visible'])} visible tiles")
    print(f"    Retrieved path: {len(cached_path['path'])} steps")
    
    # Show comprehensive statistics
    print("\nComprehensive system statistics:")
    stats = memory_manager.get_comprehensive_stats()
    
    print(f"  System uptime: {stats['uptime_seconds']:.1f} seconds")
    print(f"  Pools created: {stats['integration_stats']['pools_created']}")
    print(f"  Caches created: {stats['integration_stats']['caches_created']}")
    
    if stats['memory_manager']:
        mem_stats = stats['memory_manager']
        print(f"  Total pools: {mem_stats['total_pools']}")
        print(f"  Pool hit rate: {mem_stats['pool_hit_rate']:.1f}%")
    
    if stats['cache_manager']:
        cache_stats = stats['cache_manager']
        print(f"  Total caches: {cache_stats['total_caches']}")
        print(f"  Cache hit rate: {cache_stats['aggregate']['average_hit_rate']:.1f}%")
    
    if stats['gc_optimizer']:
        gc_stats = stats['gc_optimizer']['gc_stats']
        print(f"  GC collections: {gc_stats['total_collections']}")
        print(f"  GC time: {gc_stats['total_gc_time_ms']:.2f}ms")
    
    # Demonstrate cleanup
    print("\nPerforming system cleanup...")
    cleanup_result = memory_manager.force_cleanup()
    print(f"  Cleared {cleanup_result['pools_cleared']} pools")
    print(f"  Cleared {cleanup_result['caches_cleared']} caches")
    print(f"  Collected {cleanup_result['gc_collected']} objects")
    
    memory_manager.shutdown()


def demo_performance_comparison() -> None:
    """Demonstrate performance comparison between pooled and non-pooled objects."""
    print_header("PERFORMANCE COMPARISON")
    
    # Test parameters
    num_iterations = 1000
    
    print(f"Comparing performance over {num_iterations} iterations...")
    
    # Non-pooled performance
    print_subheader("Non-Pooled Object Creation")
    
    class RegularMessage:
        def __init__(self, text: str, color: tuple):
            self.text = text
            self.color = color
            self.timestamp = time.time()
    
    with memory_usage_context("Non-pooled creation") as regular_result:
        start_time = time.time()
        
        for i in range(num_iterations):
            msg = RegularMessage(f"Message {i}", (255, 255, 255))
            # Simulate usage
            _ = msg.text
            del msg
        
        regular_time = time.time() - start_time
    
    print(f"  Time: {regular_time:.4f} seconds")
    print(f"  Memory delta: {regular_result['memory_delta_mb']:.2f} MB")
    
    # Pooled performance
    print_subheader("Pooled Object Creation")
    
    message_pool = MessagePool(initial_size=50, max_size=200)
    
    with memory_usage_context("Pooled creation") as pooled_result:
        start_time = time.time()
        
        for i in range(num_iterations):
            with message_pool.acquire(auto_release=True) as msg:
                msg.set_message(f"Message {i}", (255, 255, 255))
                # Simulate usage
                _ = msg.text
        
        pooled_time = time.time() - start_time
    
    print(f"  Time: {pooled_time:.4f} seconds")
    print(f"  Memory delta: {pooled_result['memory_delta_mb']:.2f} MB")
    
    # Performance comparison
    print_subheader("Performance Analysis")
    
    time_improvement = ((regular_time - pooled_time) / regular_time) * 100
    memory_improvement = regular_result['memory_delta_mb'] - pooled_result['memory_delta_mb']
    
    print(f"  Time improvement: {time_improvement:.1f}%")
    print(f"  Memory savings: {memory_improvement:.2f} MB")
    
    pool_stats = message_pool.get_stats()
    print(f"  Pool hit rate: {pool_stats['hit_rate']:.1f}%")
    print(f"  Pool efficiency: {pool_stats['hits']} hits, {pool_stats['misses']} misses")


def main():
    """Run the complete memory optimization demonstration."""
    print("🚀 MEMORY OPTIMIZATION SYSTEM DEMONSTRATION")
    print("=" * 60)
    print("This demo showcases the comprehensive memory optimization")
    print("capabilities including pooling, caching, profiling, and GC optimization.")
    
    try:
        # Run all demonstrations
        demo_object_pooling()
        demo_specialized_pools()
        demo_smart_caching()
        demo_memory_profiling()
        demo_gc_optimization()
        demo_integrated_system()
        demo_performance_comparison()
        
        print_header("DEMONSTRATION COMPLETE")
        print("✅ All memory optimization features demonstrated successfully!")
        print("\nKey Benefits:")
        print("  • Reduced memory allocation overhead through object pooling")
        print("  • Improved cache hit rates with smart caching strategies")
        print("  • Comprehensive memory leak detection and profiling")
        print("  • Optimized garbage collection for better performance")
        print("  • Integrated system for seamless game engine integration")
        
        print("\nThe memory optimization system is ready for production use!")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
