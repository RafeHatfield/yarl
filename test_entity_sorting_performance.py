"""Performance benchmark for entity sorting cache.

This script demonstrates the performance benefits of the entity sorting cache
by comparing cached vs uncached sorting operations with various entity counts.
"""

import time
import sys
import os
from typing import List

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from entity_sorting_cache import EntitySortingCache, reset_entity_cache
from render_functions import RenderOrder
from entity import Entity


def create_test_entities(count: int) -> List[Entity]:
    """Create a list of test entities with random render orders.
    
    Args:
        count (int): Number of entities to create
        
    Returns:
        List[Entity]: List of test entities
    """
    entities = []
    render_orders = [RenderOrder.STAIRS, RenderOrder.CORPSE, RenderOrder.ITEM, RenderOrder.ACTOR]
    
    for i in range(count):
        render_order = render_orders[i % len(render_orders)]
        entity = Entity(
            x=i % 100, y=i // 100,
            char='X', color=(255, 255, 255),
            name=f'Entity_{i}',
            render_order=render_order
        )
        entities.append(entity)
    
    return entities


def benchmark_original_sorting(entities: List[Entity], iterations: int) -> float:
    """Benchmark original sorting method (no cache).
    
    Args:
        entities (List[Entity]): Entities to sort
        iterations (int): Number of sorting iterations
        
    Returns:
        float: Total time in seconds
    """
    start_time = time.time()
    
    for _ in range(iterations):
        # Original sorting method
        sorted_entities = sorted(entities, key=lambda x: x.render_order.value)
    
    end_time = time.time()
    return end_time - start_time


def benchmark_cached_sorting(entities: List[Entity], iterations: int) -> float:
    """Benchmark cached sorting method.
    
    Args:
        entities (List[Entity]): Entities to sort
        iterations (int): Number of sorting iterations
        
    Returns:
        float: Total time in seconds
    """
    cache = EntitySortingCache()
    start_time = time.time()
    
    for _ in range(iterations):
        # Cached sorting method
        sorted_entities = cache.get_sorted_entities(entities)
    
    end_time = time.time()
    return end_time - start_time


def run_performance_comparison():
    """Run comprehensive performance comparison."""
    print("🚀 Entity Sorting Cache Performance Benchmark")
    print("=" * 60)
    
    entity_counts = [10, 50, 100, 500, 1000]
    iterations = 1000
    
    print(f"Running {iterations} iterations for each entity count...")
    print()
    
    results = []
    
    for entity_count in entity_counts:
        print(f"📊 Testing with {entity_count} entities:")
        
        # Create test entities
        entities = create_test_entities(entity_count)
        
        # Benchmark original sorting
        original_time = benchmark_original_sorting(entities, iterations)
        
        # Benchmark cached sorting
        cached_time = benchmark_cached_sorting(entities, iterations)
        
        # Calculate performance improvement
        if cached_time > 0:
            speedup = original_time / cached_time
            improvement_percent = ((original_time - cached_time) / original_time) * 100
        else:
            speedup = float('inf')
            improvement_percent = 100.0
        
        results.append({
            'entity_count': entity_count,
            'original_time': original_time,
            'cached_time': cached_time,
            'speedup': speedup,
            'improvement_percent': improvement_percent
        })
        
        print(f"  Original sorting: {original_time:.4f}s")
        print(f"  Cached sorting:   {cached_time:.4f}s")
        print(f"  Speedup:          {speedup:.1f}x")
        print(f"  Improvement:      {improvement_percent:.1f}%")
        print()
    
    # Print summary
    print("📈 Performance Summary:")
    print("-" * 60)
    print(f"{'Entities':<10} {'Original':<12} {'Cached':<12} {'Speedup':<10} {'Improvement'}")
    print("-" * 60)
    
    for result in results:
        print(f"{result['entity_count']:<10} "
              f"{result['original_time']:.4f}s{'':<4} "
              f"{result['cached_time']:.4f}s{'':<4} "
              f"{result['speedup']:.1f}x{'':<6} "
              f"{result['improvement_percent']:.1f}%")
    
    # Calculate average improvement
    avg_improvement = sum(r['improvement_percent'] for r in results) / len(results)
    avg_speedup = sum(r['speedup'] for r in results) / len(results)
    
    print("-" * 60)
    print(f"Average speedup: {avg_speedup:.1f}x")
    print(f"Average improvement: {avg_improvement:.1f}%")
    print()
    
    # Test cache behavior
    print("🧪 Cache Behavior Analysis:")
    print("-" * 30)
    
    cache = EntitySortingCache()
    test_entities = create_test_entities(100)
    
    # First sort (cache miss)
    cache.get_sorted_entities(test_entities)
    
    # Multiple cache hits
    for _ in range(10):
        cache.get_sorted_entities(test_entities)
    
    # Get stats
    stats = cache.get_cache_stats()
    
    print(f"Cache hits: {stats['cache_hits']}")
    print(f"Cache misses: {stats['cache_misses']}")
    print(f"Hit rate: {stats['hit_rate_percent']:.1f}%")
    print(f"Total sorts performed: {stats['total_sorts']}")
    print(f"Total requests: {stats['total_requests']}")
    print()
    
    print("✅ Benchmark completed successfully!")


if __name__ == '__main__':
    run_performance_comparison()
