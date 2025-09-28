"""Entity sorting cache for optimized rendering performance.

This module provides caching for entity sorting operations to avoid repeated
sorting of entities by render order. The cache is invalidated when entities
are added, removed, or when their render order changes.

The EntitySortingCache maintains a sorted list of entities and tracks changes
to the entity list to determine when the cache needs to be refreshed.
"""

from typing import List, Set, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class EntitySortingCache:
    """Cache for sorted entity lists to optimize rendering performance.
    
    This class maintains a cached sorted list of entities by render order
    and provides efficient cache invalidation when entities change.
    
    Attributes:
        _cached_entities (List[Any]): Cached sorted entity list
        _entity_signatures (Set[Tuple]): Set of entity signatures for change detection
        _cache_valid (bool): Whether the current cache is valid
        _stats (dict): Performance statistics
    """
    
    def __init__(self):
        """Initialize the entity sorting cache."""
        self._cached_entities: List[Any] = []
        self._entity_signatures: Set[Tuple[int, int, int]] = set()  # (id, x, y, render_order)
        self._cache_valid = False
        
        # Performance statistics
        self._stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'cache_invalidations': 0,
            'total_sorts': 0,
            'entities_processed': 0
        }
    
    def get_sorted_entities(self, entities: List[Any]) -> List[Any]:
        """Get entities sorted by render order, using cache when possible.
        
        Args:
            entities (List[Any]): List of entities to sort
            
        Returns:
            List[Any]: Entities sorted by render order (lowest to highest)
        """
        if self._is_cache_valid(entities):
            self._stats['cache_hits'] += 1
            logger.debug(f"Entity sorting cache hit (entities: {len(entities)})")
            return self._cached_entities
        
        # Cache miss - need to sort and update cache
        self._stats['cache_misses'] += 1
        self._stats['total_sorts'] += 1
        self._stats['entities_processed'] += len(entities)
        
        logger.debug(f"Entity sorting cache miss - sorting {len(entities)} entities")
        
        # Sort entities by render order
        sorted_entities = sorted(entities, key=lambda x: x.render_order.value)
        
        # Update cache
        self._cached_entities = sorted_entities.copy()
        self._entity_signatures = self._generate_signatures(entities)
        self._cache_valid = True
        
        return sorted_entities
    
    def invalidate_cache(self, reason: str = "manual") -> None:
        """Manually invalidate the entity sorting cache.
        
        Args:
            reason (str): Reason for invalidation (for debugging)
        """
        if self._cache_valid:
            self._stats['cache_invalidations'] += 1
            logger.debug(f"Entity sorting cache invalidated: {reason}")
        
        self._cache_valid = False
        self._cached_entities.clear()
        self._entity_signatures.clear()
    
    def _is_cache_valid(self, entities: List[Any]) -> bool:
        """Check if the current cache is valid for the given entity list.
        
        Args:
            entities (List[Any]): Current entity list to check
            
        Returns:
            bool: True if cache is valid, False if it needs refresh
        """
        if not self._cache_valid:
            return False
        
        # Check if entity count changed
        if len(entities) != len(self._cached_entities):
            return False
        
        # Check if entity signatures changed (position, render order, or identity)
        current_signatures = self._generate_signatures(entities)
        if current_signatures != self._entity_signatures:
            return False
        
        return True
    
    def _generate_signatures(self, entities: List[Any]) -> Set[Tuple[int, int, int]]:
        """Generate signatures for entities to detect changes.
        
        Args:
            entities (List[Any]): List of entities
            
        Returns:
            Set[Tuple]: Set of entity signatures (id, x, y, render_order_value)
        """
        signatures = set()
        for entity in entities:
            # Use entity id, position, and render order as signature
            signature = (
                id(entity),
                entity.x,
                entity.y,
                entity.render_order.value
            )
            signatures.add(signature)
        return signatures
    
    def get_cache_stats(self) -> dict:
        """Get performance statistics for the entity sorting cache.
        
        Returns:
            dict: Dictionary containing cache performance metrics
        """
        total_requests = self._stats['cache_hits'] + self._stats['cache_misses']
        hit_rate = (self._stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_hits': self._stats['cache_hits'],
            'cache_misses': self._stats['cache_misses'],
            'cache_invalidations': self._stats['cache_invalidations'],
            'total_sorts': self._stats['total_sorts'],
            'entities_processed': self._stats['entities_processed'],
            'hit_rate_percent': round(hit_rate, 2),
            'total_requests': total_requests
        }
    
    def reset_stats(self) -> None:
        """Reset all performance statistics."""
        for key in self._stats:
            self._stats[key] = 0


# Global cache instance for convenience
_global_entity_cache = EntitySortingCache()


def get_sorted_entities(entities: List[Any]) -> List[Any]:
    """Global function to get sorted entities using the cache.
    
    This provides a simple interface for the entity sorting cache that can
    be used as a drop-in replacement for manual entity sorting.
    
    Args:
        entities (List[Any]): List of entities to sort by render order
        
    Returns:
        List[Any]: Entities sorted by render order (lowest to highest)
    """
    return _global_entity_cache.get_sorted_entities(entities)


def invalidate_entity_cache(reason: str = "manual") -> None:
    """Global function to invalidate the entity sorting cache.
    
    Args:
        reason (str): Reason for invalidation (for debugging)
    """
    _global_entity_cache.invalidate_cache(reason)


def get_entity_cache_stats() -> dict:
    """Global function to get entity sorting cache statistics.
    
    Returns:
        dict: Dictionary containing cache performance metrics
    """
    return _global_entity_cache.get_cache_stats()


def reset_entity_cache_stats() -> None:
    """Global function to reset entity sorting cache statistics."""
    _global_entity_cache.reset_stats()


def reset_entity_cache() -> None:
    """Global function to reset the entity sorting cache to initial state.
    
    This is useful for testing to ensure a clean state between tests.
    """
    global _global_entity_cache
    _global_entity_cache = EntitySortingCache()
