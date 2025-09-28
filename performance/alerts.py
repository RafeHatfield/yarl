"""Performance alert system for detecting and notifying about performance issues.

This module provides a comprehensive alerting system that can monitor performance
metrics and trigger alerts when thresholds are exceeded or anomalies are detected.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum, auto
import time
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Severity levels for performance alerts."""
    
    INFO = auto()
    WARNING = auto()
    CRITICAL = auto()
    EMERGENCY = auto()


class AlertCondition(ABC):
    """Abstract base class for alert conditions."""
    
    @abstractmethod
    def evaluate(self, metrics: Dict[str, Any]) -> bool:
        """Evaluate if the condition is met.
        
        Args:
            metrics (Dict[str, Any]): Current metrics
            
        Returns:
            bool: True if condition is met
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get description of the condition.
        
        Returns:
            str: Condition description
        """
        pass


class ThresholdCondition(AlertCondition):
    """Alert condition based on threshold comparison."""
    
    def __init__(self, metric_name: str, threshold: float, 
                 operator: str = 'greater_than'):
        """Initialize threshold condition.
        
        Args:
            metric_name (str): Name of the metric to check
            threshold (float): Threshold value
            operator (str): Comparison operator ('greater_than', 'less_than', 'equals')
        """
        self.metric_name = metric_name
        self.threshold = threshold
        self.operator = operator
    
    def evaluate(self, metrics: Dict[str, Any]) -> bool:
        """Evaluate threshold condition."""
        value = self._get_metric_value(metrics, self.metric_name)
        if value is None:
            return False
        
        if self.operator == 'greater_than':
            return value > self.threshold
        elif self.operator == 'less_than':
            return value < self.threshold
        elif self.operator == 'equals':
            return abs(value - self.threshold) < 1e-9
        elif self.operator == 'greater_equal':
            return value >= self.threshold
        elif self.operator == 'less_equal':
            return value <= self.threshold
        
        return False
    
    def _get_metric_value(self, metrics: Dict[str, Any], metric_path: str) -> Optional[float]:
        """Get metric value from nested dictionary using dot notation."""
        keys = metric_path.split('.')
        current = metrics
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current if isinstance(current, (int, float)) else None
    
    def get_description(self) -> str:
        """Get condition description."""
        return f"{self.metric_name} {self.operator} {self.threshold}"


class TrendCondition(AlertCondition):
    """Alert condition based on trend analysis."""
    
    def __init__(self, metric_name: str, trend_direction: str, 
                 min_samples: int = 5, trend_threshold: float = 0.1):
        """Initialize trend condition.
        
        Args:
            metric_name (str): Name of the metric to check
            trend_direction (str): Expected trend ('increasing', 'decreasing')
            min_samples (int): Minimum samples needed for trend analysis
            trend_threshold (float): Minimum trend slope to trigger alert
        """
        self.metric_name = metric_name
        self.trend_direction = trend_direction
        self.min_samples = min_samples
        self.trend_threshold = trend_threshold
        self.history = deque(maxlen=50)  # Keep last 50 samples
    
    def evaluate(self, metrics: Dict[str, Any]) -> bool:
        """Evaluate trend condition."""
        value = self._get_metric_value(metrics, self.metric_name)
        if value is None:
            return False
        
        # Add to history
        self.history.append((time.time(), value))
        
        if len(self.history) < self.min_samples:
            return False
        
        # Calculate trend
        values = [v for _, v in self.history]
        trend_slope = self._calculate_trend_slope(values)
        
        if self.trend_direction == 'increasing':
            return trend_slope > self.trend_threshold
        elif self.trend_direction == 'decreasing':
            return trend_slope < -self.trend_threshold
        
        return False
    
    def _get_metric_value(self, metrics: Dict[str, Any], metric_path: str) -> Optional[float]:
        """Get metric value from nested dictionary."""
        keys = metric_path.split('.')
        current = metrics
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current if isinstance(current, (int, float)) else None
    
    def _calculate_trend_slope(self, values: List[float]) -> float:
        """Calculate trend slope using linear regression."""
        if len(values) < 2:
            return 0.0
        
        n = len(values)
        x_values = list(range(n))
        
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        return numerator / denominator if denominator != 0 else 0.0
    
    def get_description(self) -> str:
        """Get condition description."""
        return f"{self.metric_name} trending {self.trend_direction}"


class CompositeCondition(AlertCondition):
    """Alert condition that combines multiple conditions."""
    
    def __init__(self, conditions: List[AlertCondition], operator: str = 'and'):
        """Initialize composite condition.
        
        Args:
            conditions (List[AlertCondition]): List of conditions to combine
            operator (str): Logical operator ('and', 'or')
        """
        self.conditions = conditions
        self.operator = operator
    
    def evaluate(self, metrics: Dict[str, Any]) -> bool:
        """Evaluate composite condition."""
        if not self.conditions:
            return False
        
        results = [condition.evaluate(metrics) for condition in self.conditions]
        
        if self.operator == 'and':
            return all(results)
        elif self.operator == 'or':
            return any(results)
        
        return False
    
    def get_description(self) -> str:
        """Get condition description."""
        descriptions = [condition.get_description() for condition in self.conditions]
        return f" {self.operator} ".join(descriptions)


@dataclass
class PerformanceAlert:
    """Represents a performance alert."""
    
    id: str
    title: str
    description: str
    severity: AlertSeverity
    timestamp: float
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    resolved: bool = False
    
    def acknowledge(self) -> None:
        """Acknowledge the alert."""
        self.acknowledged = True
        self.metadata['acknowledged_at'] = time.time()
    
    def resolve(self) -> None:
        """Mark the alert as resolved."""
        self.resolved = True
        self.metadata['resolved_at'] = time.time()
    
    def get_age(self) -> float:
        """Get age of the alert in seconds.
        
        Returns:
            float: Age in seconds
        """
        return time.time() - self.timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity.name,
            'timestamp': self.timestamp,
            'metrics': self.metrics,
            'metadata': self.metadata,
            'acknowledged': self.acknowledged,
            'resolved': self.resolved,
            'age': self.get_age(),
        }


@dataclass
class AlertRule:
    """Defines a rule for triggering performance alerts."""
    
    id: str
    name: str
    condition: AlertCondition
    severity: AlertSeverity
    description: str = ""
    enabled: bool = True
    cooldown_period: float = 300.0  # 5 minutes default cooldown
    max_alerts_per_hour: int = 10
    
    # Internal state
    last_triggered: Optional[float] = field(default=None, init=False)
    trigger_count: int = field(default=0, init=False)
    hourly_triggers: deque = field(default_factory=lambda: deque(maxlen=100), init=False)
    
    def can_trigger(self) -> bool:
        """Check if the rule can trigger an alert.
        
        Returns:
            bool: True if rule can trigger
        """
        if not self.enabled:
            return False
        
        current_time = time.time()
        
        # Check cooldown period
        if (self.last_triggered is not None and 
            current_time - self.last_triggered < self.cooldown_period):
            return False
        
        # Check hourly rate limit
        hour_ago = current_time - 3600
        recent_triggers = [t for t in self.hourly_triggers if t > hour_ago]
        
        if len(recent_triggers) >= self.max_alerts_per_hour:
            return False
        
        return True
    
    def trigger(self, metrics: Dict[str, Any]) -> Optional[PerformanceAlert]:
        """Trigger the alert rule.
        
        Args:
            metrics (Dict[str, Any]): Current metrics
            
        Returns:
            PerformanceAlert: Created alert or None if not triggered
        """
        if not self.can_trigger():
            return None
        
        if not self.condition.evaluate(metrics):
            return None
        
        # Create alert
        current_time = time.time()
        alert = PerformanceAlert(
            id=f"{self.id}_{int(current_time)}",
            title=self.name,
            description=self.description or self.condition.get_description(),
            severity=self.severity,
            timestamp=current_time,
            metrics=metrics.copy(),
            metadata={
                'rule_id': self.id,
                'condition': self.condition.get_description(),
                'trigger_count': self.trigger_count + 1,
            }
        )
        
        # Update rule state
        self.last_triggered = current_time
        self.trigger_count += 1
        self.hourly_triggers.append(current_time)
        
        return alert
    
    def reset_state(self) -> None:
        """Reset the rule's internal state."""
        self.last_triggered = None
        self.trigger_count = 0
        self.hourly_triggers.clear()


class AlertManager:
    """Manages performance alerts and alert rules."""
    
    def __init__(self):
        """Initialize alert manager."""
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.alert_history: List[PerformanceAlert] = []
        
        # Alert handlers
        self.alert_handlers: List[Callable[[PerformanceAlert], None]] = []
        
        # Configuration
        self.max_active_alerts = 100
        self.max_history_size = 1000
        self.auto_resolve_age = 3600.0  # 1 hour
        
        # Statistics
        self.stats = {
            'total_alerts': 0,
            'alerts_by_severity': defaultdict(int),
            'alerts_by_rule': defaultdict(int),
        }
    
    def add_rule(self, rule: AlertRule) -> None:
        """Add an alert rule.
        
        Args:
            rule (AlertRule): Alert rule to add
        """
        self.rules[rule.id] = rule
        logger.debug(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove an alert rule.
        
        Args:
            rule_id (str): ID of rule to remove
            
        Returns:
            bool: True if rule was removed
        """
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.debug(f"Removed alert rule: {rule_id}")
            return True
        return False
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable an alert rule.
        
        Args:
            rule_id (str): ID of rule to enable
            
        Returns:
            bool: True if rule was enabled
        """
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable an alert rule.
        
        Args:
            rule_id (str): ID of rule to disable
            
        Returns:
            bool: True if rule was disabled
        """
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            return True
        return False
    
    def add_alert_handler(self, handler: Callable[[PerformanceAlert], None]) -> None:
        """Add an alert handler.
        
        Args:
            handler (Callable): Function to handle alerts
        """
        self.alert_handlers.append(handler)
    
    def check_alerts(self, metrics: Dict[str, Any]) -> List[PerformanceAlert]:
        """Check all rules and trigger alerts if conditions are met.
        
        Args:
            metrics (Dict[str, Any]): Current performance metrics
            
        Returns:
            List[PerformanceAlert]: List of triggered alerts
        """
        triggered_alerts = []
        
        for rule in self.rules.values():
            try:
                alert = rule.trigger(metrics)
                if alert:
                    self._handle_new_alert(alert)
                    triggered_alerts.append(alert)
            except Exception as e:
                logger.error(f"Error checking alert rule {rule.id}: {e}")
        
        # Auto-resolve old alerts
        self._auto_resolve_alerts()
        
        return triggered_alerts
    
    def _handle_new_alert(self, alert: PerformanceAlert) -> None:
        """Handle a new alert."""
        # Add to active alerts
        self.active_alerts[alert.id] = alert
        
        # Add to history
        self.alert_history.append(alert)
        
        # Update statistics
        self.stats['total_alerts'] += 1
        self.stats['alerts_by_severity'][alert.severity.name] += 1
        
        # Extract rule ID from metadata
        rule_id = alert.metadata.get('rule_id', 'unknown')
        self.stats['alerts_by_rule'][rule_id] += 1
        
        # Call alert handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
        
        # Cleanup if needed
        self._cleanup_alerts()
        
        logger.warning(f"Performance alert triggered: {alert.title}")
    
    def _auto_resolve_alerts(self) -> None:
        """Auto-resolve old alerts."""
        current_time = time.time()
        to_resolve = []
        
        for alert_id, alert in self.active_alerts.items():
            if not alert.resolved and alert.get_age() > self.auto_resolve_age:
                to_resolve.append(alert_id)
        
        for alert_id in to_resolve:
            self.resolve_alert(alert_id, auto_resolved=True)
    
    def _cleanup_alerts(self) -> None:
        """Clean up old alerts to maintain limits."""
        # Limit active alerts
        if len(self.active_alerts) > self.max_active_alerts:
            # Remove oldest resolved alerts
            resolved_alerts = [(aid, alert) for aid, alert in self.active_alerts.items() if alert.resolved]
            resolved_alerts.sort(key=lambda x: x[1].timestamp)
            
            to_remove = len(self.active_alerts) - self.max_active_alerts
            for i in range(min(to_remove, len(resolved_alerts))):
                alert_id = resolved_alerts[i][0]
                del self.active_alerts[alert_id]
        
        # Limit history size
        if len(self.alert_history) > self.max_history_size:
            self.alert_history = self.alert_history[-self.max_history_size:]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert.
        
        Args:
            alert_id (str): ID of alert to acknowledge
            
        Returns:
            bool: True if alert was acknowledged
        """
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledge()
            logger.info(f"Alert acknowledged: {alert_id}")
            return True
        return False
    
    def resolve_alert(self, alert_id: str, auto_resolved: bool = False) -> bool:
        """Resolve an alert.
        
        Args:
            alert_id (str): ID of alert to resolve
            auto_resolved (bool): Whether alert was auto-resolved
            
        Returns:
            bool: True if alert was resolved
        """
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolve()
            if auto_resolved:
                alert.metadata['auto_resolved'] = True
            
            logger.info(f"Alert resolved: {alert_id}")
            return True
        return False
    
    def get_active_alerts(self, severity: AlertSeverity = None) -> List[PerformanceAlert]:
        """Get active alerts.
        
        Args:
            severity (AlertSeverity, optional): Filter by severity
            
        Returns:
            List[PerformanceAlert]: Active alerts
        """
        alerts = [alert for alert in self.active_alerts.values() if not alert.resolved]
        
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def get_alert_history(self, limit: int = None) -> List[PerformanceAlert]:
        """Get alert history.
        
        Args:
            limit (int, optional): Maximum number of alerts to return
            
        Returns:
            List[PerformanceAlert]: Historical alerts
        """
        history = sorted(self.alert_history, key=lambda x: x.timestamp, reverse=True)
        
        if limit:
            history = history[:limit]
        
        return history
    
    def get_stats(self) -> Dict[str, Any]:
        """Get alert manager statistics.
        
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        stats = self.stats.copy()
        stats.update({
            'active_alerts': len([a for a in self.active_alerts.values() if not a.resolved]),
            'total_active': len(self.active_alerts),
            'history_size': len(self.alert_history),
            'rules_count': len(self.rules),
            'enabled_rules': len([r for r in self.rules.values() if r.enabled]),
        })
        
        return stats
    
    def clear_history(self) -> None:
        """Clear alert history."""
        self.alert_history.clear()
        logger.info("Alert history cleared")
    
    def reset_all_rules(self) -> None:
        """Reset state for all rules."""
        for rule in self.rules.values():
            rule.reset_state()
        logger.info("All alert rules reset")


def create_alert_rule(rule_id: str, name: str, condition: AlertCondition,
                     severity: AlertSeverity = AlertSeverity.WARNING,
                     description: str = "", **kwargs) -> AlertRule:
    """Create an alert rule with common defaults.
    
    Args:
        rule_id (str): Unique rule ID
        name (str): Rule name
        condition (AlertCondition): Alert condition
        severity (AlertSeverity): Alert severity
        description (str): Rule description
        **kwargs: Additional rule parameters
        
    Returns:
        AlertRule: Created alert rule
    """
    return AlertRule(
        id=rule_id,
        name=name,
        condition=condition,
        severity=severity,
        description=description,
        **kwargs
    )


def create_threshold_rule(rule_id: str, name: str, metric_name: str,
                         threshold: float, operator: str = 'greater_than',
                         severity: AlertSeverity = AlertSeverity.WARNING) -> AlertRule:
    """Create a threshold-based alert rule.
    
    Args:
        rule_id (str): Unique rule ID
        name (str): Rule name
        metric_name (str): Metric to monitor
        threshold (float): Threshold value
        operator (str): Comparison operator
        severity (AlertSeverity): Alert severity
        
    Returns:
        AlertRule: Created alert rule
    """
    condition = ThresholdCondition(metric_name, threshold, operator)
    return create_alert_rule(rule_id, name, condition, severity)


def create_trend_rule(rule_id: str, name: str, metric_name: str,
                     trend_direction: str, severity: AlertSeverity = AlertSeverity.WARNING,
                     **kwargs) -> AlertRule:
    """Create a trend-based alert rule.
    
    Args:
        rule_id (str): Unique rule ID
        name (str): Rule name
        metric_name (str): Metric to monitor
        trend_direction (str): Expected trend direction
        severity (AlertSeverity): Alert severity
        **kwargs: Additional trend condition parameters
        
    Returns:
        AlertRule: Created alert rule
    """
    condition = TrendCondition(metric_name, trend_direction, **kwargs)
    return create_alert_rule(rule_id, name, condition, severity)
