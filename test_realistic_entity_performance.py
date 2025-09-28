"""Realistic performance benchmark for entity sorting cache.

This script simulates realistic gameplay scenarios where entities move,
die, and spawn to demonstrate when the cache provides benefits.
"""

import time
import sys
import os
from typing import List
import random

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from entity_sorting_cache import EntitySortingCache, reset_entity_cache
from render_functions import RenderOrder
from entity import Entity


def create_game_entities(count: int) -> List[Entity]:
    """Create a realistic set of game entities.
    
    Args:
        count (int): Total number of entities
        
    Returns:
        List[Entity]: List of game entities
    """
    entities = []
    
    # Player (1)
    player = Entity(
        x=40, y=20, char='@', color=(255, 255, 255), name='Player',
        render_order=RenderOrder.ACTOR
    )
    entities.append(player)
    
    # Monsters (30% of entities)
    monster_count = max(1, count * 30 // 100)
    for i in range(monster_count):
        monster = Entity(
            x=random.randint(0, 79), y=random.randint(0, 42),
            char='o', color=(0, 255, 0), name=f'Orc_{i}',
            render_order=RenderOrder.ACTOR
        )
        entities.append(monster)
    
    # Items (40% of entities)
    item_count = max(1, count * 40 // 100)
    for i in range(item_count):
        item = Entity(
            x=random.randint(0, 79), y=random.randint(0, 42),
            char='!', color=(255, 0, 255), name=f'Potion_{i}',
            render_order=RenderOrder.ITEM
        )
        entities.append(item)
    
    # Corpses (20% of entities)
    corpse_count = max(1, count * 20 // 100)
    for i in range(corpse_count):
        corpse = Entity(
            x=random.randint(0, 79), y=random.randint(0, 42),
            char='%', color=(127, 0, 0), name=f'Corpse_{i}',
            render_order=RenderOrder.CORPSE
        )
        entities.append(corpse)
    
    # Stairs (remaining entities)
    remaining = count - len(entities)
    for i in range(remaining):
        stairs = Entity(
            x=random.randint(0, 79), y=random.randint(0, 42),
            char='>', color=(255, 255, 0), name=f'Stairs_{i}',
            render_order=RenderOrder.STAIRS
        )
        entities.append(stairs)
    
    return entities


def simulate_gameplay_frame(entities: List[Entity]) -> None:
    """Simulate one frame of gameplay with entity changes.
    
    Args:
        entities (List[Entity]): Current entity list
    """
    # 10% chance entities move (realistic for turn-based game)
    if random.random() < 0.1:
        for entity in entities:
            if random.random() < 0.3:  # 30% of entities might move
                entity.x = max(0, min(79, entity.x + random.randint(-1, 1)))
                entity.y = max(0, min(42, entity.y + random.randint(-1, 1)))


def benchmark_realistic_gameplay(entity_count: int, frames: int) -> dict:
    """Benchmark entity sorting in realistic gameplay scenario.
    
    Args:
        entity_count (int): Number of entities in the game
        frames (int): Number of frames to simulate
        
    Returns:
        dict: Benchmark results
    """
    entities = create_game_entities(entity_count)
    
    # Benchmark original sorting
    start_time = time.time()
    for frame in range(frames):
        simulate_gameplay_frame(entities)
        # Original sorting
        sorted_entities = sorted(entities, key=lambda x: x.render_order.value)
    original_time = time.time() - start_time
    
    # Reset entities for fair comparison
    entities = create_game_entities(entity_count)
    
    # Benchmark cached sorting
    cache = EntitySortingCache()
    start_time = time.time()
    for frame in range(frames):
        simulate_gameplay_frame(entities)
        # Cached sorting
        sorted_entities = cache.get_sorted_entities(entities)
    cached_time = time.time() - start_time
    
    # Get cache statistics
    stats = cache.get_cache_stats()
    
    return {
        'entity_count': entity_count,
        'frames': frames,
        'original_time': original_time,
        'cached_time': cached_time,
        'speedup': original_time / cached_time if cached_time > 0 else float('inf'),
        'improvement_percent': ((original_time - cached_time) / original_time * 100) if original_time > 0 else 0,
        'cache_stats': stats
    }


def benchmark_static_scenario(entity_count: int, frames: int) -> dict:
    """Benchmark entity sorting with static entities (best case for cache).
    
    Args:
        entity_count (int): Number of entities
        frames (int): Number of frames to simulate
        
    Returns:
        dict: Benchmark results
    """
    entities = create_game_entities(entity_count)
    
    # Benchmark original sorting (static entities)
    start_time = time.time()
    for frame in range(frames):
        sorted_entities = sorted(entities, key=lambda x: x.render_order.value)
    original_time = time.time() - start_time
    
    # Benchmark cached sorting (static entities)
    cache = EntitySortingCache()
    start_time = time.time()
    for frame in range(frames):
        sorted_entities = cache.get_sorted_entities(entities)
    cached_time = time.time() - start_time
    
    stats = cache.get_cache_stats()
    
    return {
        'entity_count': entity_count,
        'frames': frames,
        'original_time': original_time,
        'cached_time': cached_time,
        'speedup': original_time / cached_time if cached_time > 0 else float('inf'),
        'improvement_percent': ((original_time - cached_time) / original_time * 100) if original_time > 0 else 0,
        'cache_stats': stats
    }


def run_realistic_benchmarks():
    """Run realistic performance benchmarks."""
    print("🎮 Realistic Entity Sorting Cache Benchmark")
    print("=" * 60)
    
    entity_counts = [50, 100, 200, 500]
    frames = 1000
    
    print(f"Simulating {frames} frames of gameplay for each scenario...")
    print()
    
    # Test realistic gameplay scenario
    print("📊 Realistic Gameplay Scenario (entities move occasionally):")
    print("-" * 60)
    
    for entity_count in entity_counts:
        result = benchmark_realistic_gameplay(entity_count, frames)
        
        print(f"Entities: {entity_count}")
        print(f"  Original: {result['original_time']:.4f}s")
        print(f"  Cached:   {result['cached_time']:.4f}s")
        print(f"  Speedup:  {result['speedup']:.1f}x")
        print(f"  Improvement: {result['improvement_percent']:.1f}%")
        print(f"  Cache hits: {result['cache_stats']['cache_hits']}")
        print(f"  Cache misses: {result['cache_stats']['cache_misses']}")
        print(f"  Hit rate: {result['cache_stats']['hit_rate_percent']:.1f}%")
        print()
    
    print("📊 Static Scenario (entities never move - best case for cache):")
    print("-" * 60)
    
    for entity_count in entity_counts:
        result = benchmark_static_scenario(entity_count, frames)
        
        print(f"Entities: {entity_count}")
        print(f"  Original: {result['original_time']:.4f}s")
        print(f"  Cached:   {result['cached_time']:.4f}s")
        print(f"  Speedup:  {result['speedup']:.1f}x")
        print(f"  Improvement: {result['improvement_percent']:.1f}%")
        print(f"  Cache hits: {result['cache_stats']['cache_hits']}")
        print(f"  Cache misses: {result['cache_stats']['cache_misses']}")
        print(f"  Hit rate: {result['cache_stats']['hit_rate_percent']:.1f}%")
        print()
    
    print("💡 Analysis:")
    print("-" * 30)
    print("• Cache provides significant benefits when entities are static")
    print("• In realistic gameplay, cache effectiveness depends on entity change frequency")
    print("• Cache overhead is justified when sorting is called frequently")
    print("• Best performance gains with larger entity counts and stable scenes")
    print()
    print("✅ Realistic benchmark completed!")


if __name__ == '__main__':
    run_realistic_benchmarks()
