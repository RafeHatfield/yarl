"""Hierarchical state system for nested state management.

This module provides hierarchical state capabilities, allowing states
to contain child states and enabling complex state compositions.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field
import logging

from .core import State, StateContext, StateResult, StateMachine, StateMachineError


logger = logging.getLogger(__name__)


class HierarchicalState(State):
    """A state that can contain child states.
    
    Hierarchical states allow for complex state compositions where
    a state can have its own internal state machine managing child states.
    """
    
    def __init__(self, state_id: str, name: str = None):
        """Initialize hierarchical state.
        
        Args:
            state_id (str): Unique identifier for this state
            name (str, optional): Human-readable name for this state
        """
        super().__init__(state_id, name)
        
        # Child state management
        self.child_states: Dict[str, State] = {}
        self.current_child: Optional[State] = None
        self.default_child: Optional[str] = None
        
        # Internal state machine for children
        self.child_machine: Optional[StateMachine] = None
        
        # Hierarchical behavior configuration
        self.propagate_events = True  # Whether to propagate events to children
        self.concurrent_children = False  # Whether children can run concurrently
        
        # Child state callbacks
        self.on_child_enter: Optional[Callable[[State, StateContext], None]] = None
        self.on_child_exit: Optional[Callable[[State, StateContext], None]] = None
    
    def add_child_state(self, child_state: State, is_default: bool = False) -> None:
        """Add a child state.
        
        Args:
            child_state (State): Child state to add
            is_default (bool): Whether this is the default child state
        """
        if child_state.state_id in self.child_states:
            raise StateMachineError(f"Child state {child_state.state_id} already exists")
        
        self.child_states[child_state.state_id] = child_state
        
        if is_default or not self.default_child:
            self.default_child = child_state.state_id
        
        # Initialize child state machine if needed
        if not self.child_machine:
            self.child_machine = StateMachine(f"{self.state_id}_children")
        
        self.child_machine.add_state(child_state)
        
        logger.debug(f"Added child state {child_state.state_id} to {self.state_id}")
    
    def remove_child_state(self, child_state_id: str) -> bool:
        """Remove a child state.
        
        Args:
            child_state_id (str): ID of child state to remove
            
        Returns:
            bool: True if child was removed
        """
        if child_state_id not in self.child_states:
            return False
        
        # Can't remove current child
        if self.current_child and self.current_child.state_id == child_state_id:
            raise StateMachineError(f"Cannot remove current child state: {child_state_id}")
        
        del self.child_states[child_state_id]
        
        if self.child_machine:
            self.child_machine.remove_state(child_state_id)
        
        # Update default child if necessary
        if self.default_child == child_state_id:
            self.default_child = next(iter(self.child_states.keys()), None)
        
        logger.debug(f"Removed child state {child_state_id} from {self.state_id}")
        return True
    
    def enter(self, context: StateContext) -> StateResult:
        """Enter the hierarchical state.
        
        Args:
            context (StateContext): State context
            
        Returns:
            StateResult: Result of entering the state
        """
        result = self.on_enter(context)
        
        if result != StateResult.ERROR and self.default_child:
            # Start child state machine with default child
            if self.child_machine and not self.child_machine.is_running():
                success = self.child_machine.start(self.default_child)
                if success:
                    self.current_child = self.child_states[self.default_child]
                    if self.on_child_enter:
                        self.on_child_enter(self.current_child, context)
                else:
                    logger.error(f"Failed to start child state machine for {self.state_id}")
                    return StateResult.ERROR
        
        return result
    
    def exit(self, context: StateContext) -> StateResult:
        """Exit the hierarchical state.
        
        Args:
            context (StateContext): State context
            
        Returns:
            StateResult: Result of exiting the state
        """
        # Stop child state machine
        if self.child_machine and self.child_machine.is_running():
            if self.current_child and self.on_child_exit:
                self.on_child_exit(self.current_child, context)
            
            self.child_machine.stop()
            self.current_child = None
        
        return self.on_exit(context)
    
    def update(self, context: StateContext, dt: float) -> StateResult:
        """Update the hierarchical state.
        
        Args:
            context (StateContext): State context
            dt (float): Delta time since last update
            
        Returns:
            StateResult: Result of the update
        """
        # Update parent state
        result = self.on_update(context, dt)
        
        if result == StateResult.ERROR:
            return result
        
        # Update child state machine
        if self.child_machine and self.child_machine.is_running():
            self.child_machine.update(dt)
            
            # Check if child state changed
            new_child = self.child_machine.get_current_state()
            if new_child != self.current_child:
                if self.current_child and self.on_child_exit:
                    self.on_child_exit(self.current_child, context)
                
                self.current_child = new_child
                
                if self.current_child and self.on_child_enter:
                    self.on_child_enter(self.current_child, context)
        
        return result
    
    def handle_event(self, event, context: StateContext) -> StateResult:
        """Handle an event in the hierarchical state.
        
        Args:
            event: Event to handle
            context (StateContext): State context
            
        Returns:
            StateResult: Result of handling the event
        """
        # Handle event in parent state first
        result = self.on_handle_event(event, context)
        
        # Propagate to child if configured and parent didn't consume it
        if (self.propagate_events and 
            result == StateResult.CONTINUE and 
            self.child_machine and 
            self.child_machine.is_running()):
            
            child_result = self.child_machine.handle_event(event)
            # Convert event result to state result
            if child_result.name == 'HANDLED':
                result = StateResult.CONTINUE
            elif child_result.name == 'ERROR':
                result = StateResult.ERROR
        
        return result
    
    def transition_child_to(self, child_state_id: str) -> bool:
        """Transition to a specific child state.
        
        Args:
            child_state_id (str): ID of child state to transition to
            
        Returns:
            bool: True if transition was successful
        """
        if not self.child_machine or not self.child_machine.is_running():
            logger.warning(f"Child state machine not running for {self.state_id}")
            return False
        
        return self.child_machine.transition_to(child_state_id)
    
    def get_current_child(self) -> Optional[State]:
        """Get the current child state.
        
        Returns:
            State: Current child state, None if no child is active
        """
        return self.current_child
    
    def get_child_states(self) -> Dict[str, State]:
        """Get all child states.
        
        Returns:
            Dict[str, State]: Dictionary of child states
        """
        return self.child_states.copy()
    
    def has_child(self, child_state_id: str) -> bool:
        """Check if a child state exists.
        
        Args:
            child_state_id (str): Child state ID to check
            
        Returns:
            bool: True if child exists
        """
        return child_state_id in self.child_states
    
    # Abstract methods for subclasses to implement
    @abstractmethod
    def on_enter(self, context: StateContext) -> StateResult:
        """Called when entering this hierarchical state.
        
        Args:
            context (StateContext): State context
            
        Returns:
            StateResult: Result of entering the state
        """
        pass
    
    @abstractmethod
    def on_exit(self, context: StateContext) -> StateResult:
        """Called when exiting this hierarchical state.
        
        Args:
            context (StateContext): State context
            
        Returns:
            StateResult: Result of exiting the state
        """
        pass
    
    @abstractmethod
    def on_update(self, context: StateContext, dt: float) -> StateResult:
        """Called when updating this hierarchical state.
        
        Args:
            context (StateContext): State context
            dt (float): Delta time since last update
            
        Returns:
            StateResult: Result of the update
        """
        pass
    
    def on_handle_event(self, event, context: StateContext) -> StateResult:
        """Called when handling an event in this hierarchical state.
        
        Default implementation returns CONTINUE. Override to handle events.
        
        Args:
            event: Event to handle
            context (StateContext): State context
            
        Returns:
            StateResult: Result of handling the event
        """
        return StateResult.CONTINUE


class CompositeState(HierarchicalState):
    """A hierarchical state that manages multiple concurrent child states.
    
    Composite states allow multiple child states to be active simultaneously,
    useful for complex behaviors that require parallel state management.
    """
    
    def __init__(self, state_id: str, name: str = None):
        """Initialize composite state.
        
        Args:
            state_id (str): Unique identifier for this state
            name (str, optional): Human-readable name for this state
        """
        super().__init__(state_id, name)
        self.concurrent_children = True
        self.active_children: Set[str] = set()
        
        # Composite-specific configuration
        self.require_all_children = False  # Whether all children must be active
        self.completion_policy = 'any'  # 'any', 'all', or 'custom'
    
    def add_child_state(self, child_state: State, auto_activate: bool = True) -> None:
        """Add a child state to the composite.
        
        Args:
            child_state (State): Child state to add
            auto_activate (bool): Whether to activate the child automatically
        """
        super().add_child_state(child_state)
        
        if auto_activate:
            self.active_children.add(child_state.state_id)
    
    def activate_child(self, child_state_id: str) -> bool:
        """Activate a child state.
        
        Args:
            child_state_id (str): ID of child state to activate
            
        Returns:
            bool: True if child was activated
        """
        if child_state_id not in self.child_states:
            return False
        
        self.active_children.add(child_state_id)
        
        # If we're currently active, start the child
        if self.active and child_state_id not in self.active_children:
            child_state = self.child_states[child_state_id]
            # Implementation would start the child state
            logger.debug(f"Activated child state {child_state_id} in composite {self.state_id}")
        
        return True
    
    def deactivate_child(self, child_state_id: str) -> bool:
        """Deactivate a child state.
        
        Args:
            child_state_id (str): ID of child state to deactivate
            
        Returns:
            bool: True if child was deactivated
        """
        if child_state_id not in self.active_children:
            return False
        
        self.active_children.remove(child_state_id)
        
        # If we're currently active, stop the child
        if self.active:
            # Implementation would stop the child state
            logger.debug(f"Deactivated child state {child_state_id} in composite {self.state_id}")
        
        return True
    
    def get_active_children(self) -> Set[str]:
        """Get IDs of currently active children.
        
        Returns:
            Set[str]: Set of active child state IDs
        """
        return self.active_children.copy()
    
    def is_child_active(self, child_state_id: str) -> bool:
        """Check if a child state is active.
        
        Args:
            child_state_id (str): Child state ID to check
            
        Returns:
            bool: True if child is active
        """
        return child_state_id in self.active_children
    
    def on_enter(self, context: StateContext) -> StateResult:
        """Enter the composite state and activate children.
        
        Args:
            context (StateContext): State context
            
        Returns:
            StateResult: Result of entering the state
        """
        # Activate all designated children
        for child_id in self.active_children:
            if child_id in self.child_states:
                child_state = self.child_states[child_id]
                # Implementation would enter the child state
                logger.debug(f"Entering child state {child_id} in composite {self.state_id}")
        
        return StateResult.CONTINUE
    
    def on_exit(self, context: StateContext) -> StateResult:
        """Exit the composite state and deactivate children.
        
        Args:
            context (StateContext): State context
            
        Returns:
            StateResult: Result of exiting the state
        """
        # Deactivate all active children
        for child_id in list(self.active_children):
            if child_id in self.child_states:
                child_state = self.child_states[child_id]
                # Implementation would exit the child state
                logger.debug(f"Exiting child state {child_id} in composite {self.state_id}")
        
        return StateResult.CONTINUE
    
    def on_update(self, context: StateContext, dt: float) -> StateResult:
        """Update the composite state and all active children.
        
        Args:
            context (StateContext): State context
            dt (float): Delta time since last update
            
        Returns:
            StateResult: Result of the update
        """
        # Update all active children
        for child_id in self.active_children:
            if child_id in self.child_states:
                child_state = self.child_states[child_id]
                # Implementation would update the child state
                # child_result = child_state.update(context, dt)
        
        return StateResult.CONTINUE


@dataclass
class StateHierarchy:
    """Represents a hierarchy of states with parent-child relationships."""
    
    root_state: State
    state_tree: Dict[str, List[str]] = field(default_factory=dict)
    parent_map: Dict[str, str] = field(default_factory=dict)
    
    def add_child_relationship(self, parent_id: str, child_id: str) -> None:
        """Add a parent-child relationship.
        
        Args:
            parent_id (str): Parent state ID
            child_id (str): Child state ID
        """
        if parent_id not in self.state_tree:
            self.state_tree[parent_id] = []
        
        self.state_tree[parent_id].append(child_id)
        self.parent_map[child_id] = parent_id
    
    def get_children(self, state_id: str) -> List[str]:
        """Get children of a state.
        
        Args:
            state_id (str): State ID
            
        Returns:
            List[str]: List of child state IDs
        """
        return self.state_tree.get(state_id, [])
    
    def get_parent(self, state_id: str) -> Optional[str]:
        """Get parent of a state.
        
        Args:
            state_id (str): State ID
            
        Returns:
            str: Parent state ID, None if no parent
        """
        return self.parent_map.get(state_id)
    
    def get_ancestors(self, state_id: str) -> List[str]:
        """Get all ancestors of a state.
        
        Args:
            state_id (str): State ID
            
        Returns:
            List[str]: List of ancestor state IDs (from immediate parent to root)
        """
        ancestors = []
        current = state_id
        
        while current in self.parent_map:
            parent = self.parent_map[current]
            ancestors.append(parent)
            current = parent
        
        return ancestors
    
    def get_descendants(self, state_id: str) -> List[str]:
        """Get all descendants of a state.
        
        Args:
            state_id (str): State ID
            
        Returns:
            List[str]: List of descendant state IDs
        """
        descendants = []
        
        def collect_descendants(current_id: str):
            children = self.get_children(current_id)
            for child_id in children:
                descendants.append(child_id)
                collect_descendants(child_id)
        
        collect_descendants(state_id)
        return descendants
    
    def is_ancestor(self, ancestor_id: str, descendant_id: str) -> bool:
        """Check if one state is an ancestor of another.
        
        Args:
            ancestor_id (str): Potential ancestor state ID
            descendant_id (str): Potential descendant state ID
            
        Returns:
            bool: True if ancestor_id is an ancestor of descendant_id
        """
        return ancestor_id in self.get_ancestors(descendant_id)
    
    def get_common_ancestor(self, state_id1: str, state_id2: str) -> Optional[str]:
        """Get the lowest common ancestor of two states.
        
        Args:
            state_id1 (str): First state ID
            state_id2 (str): Second state ID
            
        Returns:
            str: Common ancestor state ID, None if no common ancestor
        """
        ancestors1 = set(self.get_ancestors(state_id1))
        ancestors2 = set(self.get_ancestors(state_id2))
        
        common_ancestors = ancestors1.intersection(ancestors2)
        
        if not common_ancestors:
            return None
        
        # Find the lowest (closest to the states) common ancestor
        for ancestor in self.get_ancestors(state_id1):
            if ancestor in common_ancestors:
                return ancestor
        
        return None
    
    def get_depth(self, state_id: str) -> int:
        """Get the depth of a state in the hierarchy.
        
        Args:
            state_id (str): State ID
            
        Returns:
            int: Depth (0 for root, 1 for immediate children, etc.)
        """
        return len(self.get_ancestors(state_id))
    
    def validate_hierarchy(self) -> List[str]:
        """Validate the state hierarchy for cycles and orphans.
        
        Returns:
            List[str]: List of validation errors
        """
        errors = []
        
        # Check for cycles
        visited = set()
        rec_stack = set()
        
        def has_cycle(state_id: str) -> bool:
            if state_id in rec_stack:
                return True
            if state_id in visited:
                return False
            
            visited.add(state_id)
            rec_stack.add(state_id)
            
            for child_id in self.get_children(state_id):
                if has_cycle(child_id):
                    return True
            
            rec_stack.remove(state_id)
            return False
        
        if has_cycle(self.root_state.state_id):
            errors.append("Cycle detected in state hierarchy")
        
        # Check for orphaned states (states with parents that don't exist)
        all_states = set(self.state_tree.keys())
        for child_states in self.state_tree.values():
            all_states.update(child_states)
        
        for child_id, parent_id in self.parent_map.items():
            if parent_id not in all_states:
                errors.append(f"Orphaned state: {child_id} has non-existent parent {parent_id}")
        
        return errors
