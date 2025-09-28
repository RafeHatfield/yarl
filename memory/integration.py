"""Integration layer for memory optimization with the game engine.

This module provides seamless integration of memory optimization features
with the existing game engine and systems.
"""

from typing import Any, Dict, List, Optional, Type, Callable
from dataclasses import dataclass
import logging
import time

from .core import MemoryManager, MemoryConfig, PoolManager, get_memory_manager
from .pools import create_default_pools, MessagePool, EntityPool, EventPool
from .cache import CacheManager, CacheConfig, CacheStrategy
from .profiler import MemoryProfiler, create_memory_profiler
from .gc_optimizer import GCOptimizer, GCConfig, GCMode, optimize_gc_settings

# Import game engine components
try:
    from engine.system import System
    from engine.game_engine import GameEngine
    GAME_ENGINE_AVAILABLE = True
except ImportError:
    GAME_ENGINE_AVAILABLE = False
    System = object
    GameEngine = None

logger = logging.getLogger(__name__)


@dataclass
class MemoryOptimizationConfig:
    """Configuration for memory optimization integration."""
    
    # Core settings
    enable_pooling: bool = True
    enable_caching: bool = True
    enable_profiling: bool = True
    enable_gc_optimization: bool = True
    
    # Pool settings
    pool_config: MemoryConfig = None
    create_default_pools: bool = True
    
    # Cache settings
    cache_config: CacheConfig = None
    default_cache_strategy: CacheStrategy = CacheStrategy.LRU
    
    # Profiler settings
    profiling_interval: float = 60.0
    enable_allocation_tracking: bool = False
    
    # GC settings
    gc_config: GCConfig = None
    gc_mode: GCMode = GCMode.BALANCED
    
    # Integration settings
    auto_integrate_systems: bool = True
    monitor_memory_usage: bool = True


class GameMemoryManager:
    """Centralized memory management for the game."""
    
    def __init__(self, config: MemoryOptimizationConfig = None):
        """Initialize game memory manager.
        
        Args:
            config (MemoryOptimizationConfig, optional): Configuration
        """
        self.config = config or MemoryOptimizationConfig()
        
        # Initialize components
        self.memory_manager: Optional[MemoryManager] = None
        self.cache_manager: Optional[CacheManager] = None
        self.memory_profiler: Optional[MemoryProfiler] = None
        self.gc_optimizer: Optional[GCOptimizer] = None
        
        # Pool references
        self.message_pool: Optional[MessagePool] = None
        self.entity_pool: Optional[EntityPool] = None
        self.event_pool: Optional[EventPool] = None
        
        # Statistics
        self.start_time = time.time()
        self.integration_stats = {
            'pools_created': 0,
            'caches_created': 0,
            'systems_integrated': 0,
        }
        
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """Initialize memory management components."""
        try:
            # Initialize memory manager
            if self.config.enable_pooling:
                pool_config = self.config.pool_config or MemoryConfig()
                self.memory_manager = MemoryManager(pool_config)
                
                if self.config.create_default_pools:
                    self._create_default_pools()
            
            # Initialize cache manager
            if self.config.enable_caching:
                cache_config = self.config.cache_config or CacheConfig()
                cache_config.strategy = self.config.default_cache_strategy
                self.cache_manager = CacheManager(cache_config)
                self._create_default_caches()
            
            # Initialize memory profiler
            if self.config.enable_profiling:
                self.memory_profiler = create_memory_profiler(
                    self.config.profiling_interval,
                    self.config.enable_allocation_tracking
                )
                self.memory_profiler.start_profiling()
            
            # Initialize GC optimizer
            if self.config.enable_gc_optimization:
                gc_config = self.config.gc_config or GCConfig()
                gc_config.mode = self.config.gc_mode
                self.gc_optimizer = GCOptimizer(gc_config)
                self.gc_optimizer.start_optimization()
            
            logger.info("Game memory manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing game memory manager: {e}")
            raise
    
    def _create_default_pools(self) -> None:
        """Create default object pools."""
        if not self.memory_manager or not self.memory_manager.pool_manager:
            return
        
        try:
            pools = create_default_pools(self.memory_manager.pool_manager)
            
            # Store references to commonly used pools
            self.message_pool = pools.get('messages')
            self.entity_pool = pools.get('temp_entities')
            self.event_pool = pools.get('events')
            
            self.integration_stats['pools_created'] = len(pools)
            logger.info(f"Created {len(pools)} default object pools")
            
        except Exception as e:
            logger.error(f"Error creating default pools: {e}")
    
    def _create_default_caches(self) -> None:
        """Create default caches."""
        if not self.cache_manager:
            return
        
        try:
            # FOV cache
            self.cache_manager.create_cache(
                'fov_cache',
                CacheStrategy.LRU,
                CacheConfig(max_size=100, default_ttl=60.0)
            )
            
            # Pathfinding cache
            self.cache_manager.create_cache(
                'pathfinding_cache',
                CacheStrategy.LRU,
                CacheConfig(max_size=200, default_ttl=30.0)
            )
            
            # Render cache
            self.cache_manager.create_cache(
                'render_cache',
                CacheStrategy.TTL,
                CacheConfig(max_size=500, default_ttl=10.0)
            )
            
            # Asset cache
            self.cache_manager.create_cache(
                'asset_cache',
                CacheStrategy.WEAK_REF,
                CacheConfig(max_size=1000)
            )
            
            self.integration_stats['caches_created'] = 4
            logger.info("Created default caches")
            
        except Exception as e:
            logger.error(f"Error creating default caches: {e}")
    
    def get_pool(self, pool_name: str):
        """Get a pool by name.
        
        Args:
            pool_name (str): Pool name
            
        Returns:
            ObjectPool: Pool instance or None
        """
        if self.memory_manager and self.memory_manager.pool_manager:
            return self.memory_manager.pool_manager.get_pool(pool_name)
        return None
    
    def get_cache(self, cache_name: str):
        """Get a cache by name.
        
        Args:
            cache_name (str): Cache name
            
        Returns:
            SmartCache: Cache instance or None
        """
        if self.cache_manager:
            return self.cache_manager.get_cache(cache_name)
        return None
    
    def create_pooled_message(self, text: str, color: tuple = (255, 255, 255)):
        """Create a pooled message.
        
        Args:
            text (str): Message text
            color (tuple): Message color
            
        Returns:
            PooledMessage: Message from pool
        """
        if self.message_pool and hasattr(self.message_pool, 'create_message'):
            return self.message_pool.create_message(text, color, auto_release=True)
        elif self.message_pool:
            # Use generic pool interface
            msg = self.message_pool.acquire(auto_release=True)
            if hasattr(msg, 'set_message'):
                msg.set_message(text, color)
            return msg
        else:
            # Fallback to regular message creation
            try:
                from game_messages import Message
                return Message(text, color)
            except ImportError:
                # Create a simple message-like object for testing
                class SimpleMessage:
                    def __init__(self, text, color):
                        self.text = text
                        self.color = color
                return SimpleMessage(text, color)
    
    def create_pooled_entity(self, **kwargs):
        """Create a pooled temporary entity.
        
        Args:
            **kwargs: Entity parameters
            
        Returns:
            PooledEntity: Entity from pool
        """
        if self.entity_pool and hasattr(self.entity_pool, 'create_entity'):
            return self.entity_pool.create_entity(auto_release=True, **kwargs)
        elif self.entity_pool:
            # Use generic pool interface
            entity = self.entity_pool.acquire(auto_release=True)
            if hasattr(entity, 'initialize_entity'):
                entity.initialize_entity(**kwargs)
            return entity
        else:
            # Fallback to regular entity creation
            try:
                from entity import Entity
                return Entity(**kwargs)
            except ImportError:
                # Create a simple entity-like object for testing
                class SimpleEntity:
                    def __init__(self, **kwargs):
                        for key, value in kwargs.items():
                            setattr(self, key, value)
                return SimpleEntity(**kwargs)
    
    def create_pooled_event(self, event_type: str, data: Dict[str, Any] = None):
        """Create a pooled event.
        
        Args:
            event_type (str): Event type
            data (Dict[str, Any], optional): Event data
            
        Returns:
            PooledEvent: Event from pool
        """
        if self.event_pool and hasattr(self.event_pool, 'create_event'):
            return self.event_pool.create_event(event_type, data, auto_release=True)
        elif self.event_pool:
            # Use generic pool interface
            event = self.event_pool.acquire(auto_release=True)
            if hasattr(event, 'set_event'):
                event.set_event(event_type, data)
            return event
        else:
            # Fallback to regular event creation
            try:
                from events import SimpleEvent
                return SimpleEvent(event_type, data)
            except ImportError:
                # Create a simple event-like object for testing
                class SimpleEvent:
                    def __init__(self, event_type, data=None):
                        self.event_type = event_type
                        self.data = data or {}
                return SimpleEvent(event_type, data)
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics.
        
        Returns:
            Dict[str, Any]: Memory statistics
        """
        stats = {
            'uptime_seconds': time.time() - self.start_time,
            'integration_stats': self.integration_stats.copy(),
            'memory_manager': None,
            'cache_manager': None,
            'memory_profiler': None,
            'gc_optimizer': None,
        }
        
        # Memory manager stats
        if self.memory_manager:
            stats['memory_manager'] = self.memory_manager.get_stats().to_dict()
            
            if self.memory_manager.pool_manager:
                stats['pool_manager'] = self.memory_manager.pool_manager.get_stats()
        
        # Cache manager stats
        if self.cache_manager:
            stats['cache_manager'] = self.cache_manager.get_stats()
        
        # Memory profiler stats
        if self.memory_profiler:
            stats['memory_profiler'] = {
                'snapshots_count': len(self.memory_profiler.get_snapshots()),
                'leak_report': self.memory_profiler.get_leak_report(),
                'memory_trend': self.memory_profiler.get_memory_trend(),
            }
        
        # GC optimizer stats
        if self.gc_optimizer:
            stats['gc_optimizer'] = {
                'gc_stats': self.gc_optimizer.get_stats().to_dict(),
                'gc_info': self.gc_optimizer.get_gc_info(),
            }
        
        return stats
    
    def force_cleanup(self) -> Dict[str, Any]:
        """Force cleanup of all memory systems.
        
        Returns:
            Dict[str, Any]: Cleanup results
        """
        results = {
            'pools_cleared': 0,
            'caches_cleared': 0,
            'gc_collected': 0,
            'memory_freed_mb': 0.0,
        }
        
        try:
            # Clear pools
            if self.memory_manager and self.memory_manager.pool_manager:
                pool_stats = self.memory_manager.pool_manager.get_stats()
                results['pools_cleared'] = pool_stats['total_pools']
                self.memory_manager.pool_manager.clear_all_pools()
            
            # Clear caches
            if self.cache_manager:
                cache_stats = self.cache_manager.get_stats()
                results['caches_cleared'] = cache_stats['total_caches']
                self.cache_manager.clear_all_caches()
            
            # Force GC
            if self.gc_optimizer:
                gc_result = self.gc_optimizer.collect_all_generations()
                results['gc_collected'] = gc_result.get('total_collected', 0)
            
            logger.info(f"Memory cleanup completed: {results}")
            
        except Exception as e:
            logger.error(f"Error during memory cleanup: {e}")
            results['error'] = str(e)
        
        return results
    
    def shutdown(self) -> None:
        """Shutdown the game memory manager."""
        try:
            # Shutdown components
            if self.memory_profiler:
                self.memory_profiler.shutdown()
            
            if self.gc_optimizer:
                self.gc_optimizer.shutdown()
            
            if self.cache_manager:
                self.cache_manager.shutdown()
            
            if self.memory_manager:
                self.memory_manager.shutdown()
            
            logger.info("Game memory manager shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during memory manager shutdown: {e}")


class PooledSystem(System):
    """Base class for systems that use memory pooling."""
    
    def __init__(self, name: str, priority: int = 50):
        """Initialize pooled system.
        
        Args:
            name (str): System name
            priority (int): System priority
        """
        super().__init__(name, priority)
        self.memory_manager = get_memory_manager()
        self.pool_manager = None
        
        if self.memory_manager:
            self.pool_manager = self.memory_manager.get_pool_manager()
    
    def get_pool(self, pool_name: str):
        """Get a pool by name.
        
        Args:
            pool_name (str): Pool name
            
        Returns:
            ObjectPool: Pool instance or None
        """
        if self.pool_manager:
            return self.pool_manager.get_pool(pool_name)
        return None
    
    def create_pooled_object(self, pool_name: str, auto_release: bool = True, **kwargs):
        """Create an object from a pool.
        
        Args:
            pool_name (str): Pool name
            auto_release (bool): Whether to auto-release
            **kwargs: Object parameters
            
        Returns:
            Any: Pooled object or None
        """
        pool = self.get_pool(pool_name)
        if pool:
            obj = pool.acquire(auto_release=auto_release)
            
            # Initialize object if it has an initialization method
            if hasattr(obj, 'initialize_component'):
                obj.initialize_component(**kwargs)
            elif hasattr(obj, 'set_data'):
                obj.set_data(**kwargs)
            
            return obj
        return None


class MemoryOptimizedEngine:
    """Game engine wrapper with memory optimization."""
    
    def __init__(self, engine: GameEngine, config: MemoryOptimizationConfig = None):
        """Initialize memory optimized engine.
        
        Args:
            engine (GameEngine): Base game engine
            config (MemoryOptimizationConfig, optional): Configuration
        """
        self.engine = engine
        self.config = config or MemoryOptimizationConfig()
        self.memory_manager = GameMemoryManager(self.config)
        
        # Integration tracking
        self.integrated_systems: List[str] = []
        
        if self.config.auto_integrate_systems:
            self._integrate_systems()
    
    def _integrate_systems(self) -> None:
        """Integrate memory optimization with existing systems."""
        if not GAME_ENGINE_AVAILABLE:
            logger.warning("Game engine not available for integration")
            return
        
        try:
            # Integrate with existing systems
            for system in self.engine.systems:
                if hasattr(system, 'integrate_memory_optimization'):
                    system.integrate_memory_optimization(self.memory_manager)
                    self.integrated_systems.append(system.name)
            
            logger.info(f"Integrated memory optimization with {len(self.integrated_systems)} systems")
            
        except Exception as e:
            logger.error(f"Error integrating systems: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics.
        
        Returns:
            Dict[str, Any]: Memory statistics
        """
        stats = self.memory_manager.get_comprehensive_stats()
        stats['integrated_systems'] = self.integrated_systems.copy()
        return stats
    
    def force_memory_cleanup(self) -> Dict[str, Any]:
        """Force memory cleanup.
        
        Returns:
            Dict[str, Any]: Cleanup results
        """
        return self.memory_manager.force_cleanup()
    
    def shutdown(self) -> None:
        """Shutdown the memory optimized engine."""
        self.memory_manager.shutdown()


def integrate_memory_optimization(engine: GameEngine, 
                                config: MemoryOptimizationConfig = None) -> MemoryOptimizedEngine:
    """Integrate memory optimization with a game engine.
    
    Args:
        engine (GameEngine): Game engine to optimize
        config (MemoryOptimizationConfig, optional): Configuration
        
    Returns:
        MemoryOptimizedEngine: Memory optimized engine
    """
    if not GAME_ENGINE_AVAILABLE:
        raise ImportError("Game engine components not available")
    
    return MemoryOptimizedEngine(engine, config)


def create_optimized_engine(target_fps: int = 60, 
                           memory_config: MemoryOptimizationConfig = None) -> MemoryOptimizedEngine:
    """Create a new game engine with memory optimization.
    
    Args:
        target_fps (int): Target FPS
        memory_config (MemoryOptimizationConfig, optional): Memory configuration
        
    Returns:
        MemoryOptimizedEngine: Optimized game engine
    """
    if not GAME_ENGINE_AVAILABLE:
        raise ImportError("Game engine components not available")
    
    engine = GameEngine(target_fps=target_fps)
    return integrate_memory_optimization(engine, memory_config)


# Global game memory manager instance
_global_game_memory_manager: Optional[GameMemoryManager] = None


def get_game_memory_manager() -> Optional[GameMemoryManager]:
    """Get the global game memory manager.
    
    Returns:
        GameMemoryManager: Global game memory manager or None
    """
    return _global_game_memory_manager


def initialize_game_memory_manager(config: MemoryOptimizationConfig = None) -> GameMemoryManager:
    """Initialize the global game memory manager.
    
    Args:
        config (MemoryOptimizationConfig, optional): Configuration
        
    Returns:
        GameMemoryManager: Initialized game memory manager
    """
    global _global_game_memory_manager
    _global_game_memory_manager = GameMemoryManager(config)
    return _global_game_memory_manager


def shutdown_game_memory_manager() -> None:
    """Shutdown the global game memory manager."""
    global _global_game_memory_manager
    if _global_game_memory_manager:
        _global_game_memory_manager.shutdown()
        _global_game_memory_manager = None
