#!/usr/bin/env python3
"""Performance test for tile rendering optimization.

This script compares the performance of optimized vs original tile rendering
to demonstrate the benefits of the caching system.
"""

import sys
import os
import time
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from loader_functions.initialize_new_game import get_game_variables, get_constants
from fov_functions import initialize_fov, recompute_fov
from render_functions import render_all, _render_tiles_original
from render_optimization import render_tiles_optimized, get_tile_optimization_stats, reset_tile_optimization_stats


def create_test_scenario():
    """Create a test scenario with game state."""
    constants = get_constants()
    player, entities, game_map, message_log, game_state = get_game_variables(constants)
    
    # Initialize FOV
    fov_map = initialize_fov(game_map)
    recompute_fov(fov_map, player.x, player.y, 10)
    
    return {
        'player': player,
        'entities': entities,
        'game_map': game_map,
        'fov_map': fov_map,
        'colors': constants['colors']
    }


def benchmark_original_rendering(scenario, num_frames=100):
    """Benchmark the original tile rendering approach."""
    print(f"🔄 Benchmarking original rendering ({num_frames} frames)...")
    
    mock_con = Mock()
    
    with patch('tcod.libtcodpy.console_set_char_background'):
        start_time = time.time()
        
        for _ in range(num_frames):
            _render_tiles_original(
                mock_con,
                scenario['game_map'],
                scenario['fov_map'],
                scenario['colors']
            )
        
        end_time = time.time()
    
    total_time = end_time - start_time
    avg_time = total_time / num_frames
    
    print(f"  ⏱️  Total time: {total_time:.4f}s")
    print(f"  📊 Average per frame: {avg_time*1000:.2f}ms")
    print(f"  🎯 Estimated FPS: {1/avg_time:.1f}")
    
    return total_time, avg_time


def benchmark_optimized_rendering(scenario, num_frames=100):
    """Benchmark the optimized tile rendering approach."""
    print(f"🚀 Benchmarking optimized rendering ({num_frames} frames)...")
    
    mock_con = Mock()
    reset_tile_optimization_stats()
    
    with patch('tcod.libtcodpy.console_set_char_background'):
        start_time = time.time()
        
        for i in range(num_frames):
            # Force full redraw on first frame, then use optimization
            force_redraw = (i == 0)
            render_tiles_optimized(
                mock_con,
                scenario['game_map'],
                scenario['fov_map'],
                scenario['colors'],
                force_full_redraw=force_redraw
            )
        
        end_time = time.time()
    
    total_time = end_time - start_time
    avg_time = total_time / num_frames
    
    # Get optimization stats
    stats = get_tile_optimization_stats()
    
    print(f"  ⏱️  Total time: {total_time:.4f}s")
    print(f"  📊 Average per frame: {avg_time*1000:.2f}ms")
    print(f"  🎯 Estimated FPS: {1/avg_time:.1f}")
    print(f"  📈 Cache hit rate: {stats['cache_hit_rate']*100:.1f}%")
    print(f"  🔄 Full redraws: {stats['full_redraws']}")
    print(f"  🎨 Avg tiles per frame: {stats['avg_tiles_per_frame']:.1f}")
    
    return total_time, avg_time, stats


def run_performance_comparison():
    """Run a comprehensive performance comparison."""
    print("🧪 Tile Rendering Performance Test")
    print("=" * 50)
    
    # Create test scenario
    scenario = create_test_scenario()
    map_size = scenario['game_map'].width * scenario['game_map'].height
    print(f"📏 Map size: {scenario['game_map'].width}×{scenario['game_map'].height} = {map_size} tiles")
    print()
    
    # Benchmark original rendering
    orig_total, orig_avg = benchmark_original_rendering(scenario, num_frames=100)
    print()
    
    # Benchmark optimized rendering
    opt_total, opt_avg, stats = benchmark_optimized_rendering(scenario, num_frames=100)
    print()
    
    # Calculate improvements
    time_improvement = ((orig_total - opt_total) / orig_total) * 100
    fps_improvement = ((1/opt_avg) - (1/orig_avg)) / (1/orig_avg) * 100
    
    print("📊 Performance Comparison")
    print("-" * 30)
    print(f"⚡ Time improvement: {time_improvement:.1f}% faster")
    print(f"🎯 FPS improvement: {fps_improvement:.1f}% higher")
    print(f"💾 Cache efficiency: {stats['cache_hit_rate']*100:.1f}% hit rate")
    
    if time_improvement > 0:
        print(f"✅ Optimization successful! {time_improvement:.1f}% performance gain")
    else:
        print(f"⚠️  Optimization overhead: {abs(time_improvement):.1f}% slower")
        print("   (This is expected for small maps or single-frame tests)")
    
    print()
    print("🔍 Optimization Details:")
    print(f"  • Total frames rendered: {stats['total_frames']}")
    print(f"  • Full redraws: {stats['full_redraws']} ({stats['full_redraws']/stats['total_frames']*100:.1f}%)")
    print(f"  • Cache hits: {stats['cache_hits']}")
    print(f"  • Cache misses: {stats['cache_misses']}")
    print(f"  • Tiles cached: {stats['tiles_cached']}")
    print(f"  • Tiles redrawn: {stats['tiles_redrawn']}")


def run_scaling_test():
    """Test how optimization scales with different scenarios."""
    print("\n🔬 Scaling Test - Multiple FOV Changes")
    print("=" * 50)
    
    scenario = create_test_scenario()
    mock_con = Mock()
    
    # Test with frequent FOV changes (worst case for optimization)
    print("🔄 Testing with frequent FOV changes (worst case)...")
    reset_tile_optimization_stats()
    
    with patch('tcod.libtcodpy.console_set_char_background'):
        start_time = time.time()
        
        for i in range(50):
            # Move player position to trigger FOV changes
            x = scenario['player'].x + (i % 10) - 5
            y = scenario['player'].y + (i % 10) - 5
            recompute_fov(scenario['fov_map'], x, y, 10)
            
            render_tiles_optimized(
                mock_con,
                scenario['game_map'],
                scenario['fov_map'],
                scenario['colors'],
                force_full_redraw=True  # Simulate FOV change
            )
        
        end_time = time.time()
    
    worst_case_time = end_time - start_time
    worst_case_stats = get_tile_optimization_stats()
    
    print(f"  ⏱️  Time: {worst_case_time:.4f}s")
    print(f"  📊 Avg per frame: {worst_case_time/50*1000:.2f}ms")
    print(f"  🔄 Full redraws: {worst_case_stats['full_redraws']}")
    
    # Test with no FOV changes (best case for optimization)
    print("\n🎯 Testing with no FOV changes (best case)...")
    reset_tile_optimization_stats()
    
    with patch('tcod.libtcodpy.console_set_char_background'):
        start_time = time.time()
        
        for i in range(50):
            render_tiles_optimized(
                mock_con,
                scenario['game_map'],
                scenario['fov_map'],
                scenario['colors'],
                force_full_redraw=(i == 0)  # Only first frame
            )
        
        end_time = time.time()
    
    best_case_time = end_time - start_time
    best_case_stats = get_tile_optimization_stats()
    
    print(f"  ⏱️  Time: {best_case_time:.4f}s")
    print(f"  📊 Avg per frame: {best_case_time/50*1000:.2f}ms")
    print(f"  🔄 Full redraws: {best_case_stats['full_redraws']}")
    print(f"  📈 Cache hit rate: {best_case_stats['cache_hit_rate']*100:.1f}%")
    
    improvement = ((worst_case_time - best_case_time) / worst_case_time) * 100
    print(f"\n⚡ Best case improvement: {improvement:.1f}% faster than worst case")


if __name__ == "__main__":
    try:
        run_performance_comparison()
        run_scaling_test()
        print("\n🎉 Performance testing completed successfully!")
    except Exception as e:
        print(f"\n❌ Performance test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
