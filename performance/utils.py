"""Utility functions for performance profiling and monitoring.

This module provides helper functions for formatting, calculating statistics,
and working with performance data.
"""

from typing import Any, List, Dict, Optional, Union, Tuple
import time
import statistics
from collections import deque


def format_time(seconds: float, precision: int = 3) -> str:
    """Format time duration in a human-readable format.
    
    Args:
        seconds (float): Time in seconds
        precision (int): Number of decimal places
        
    Returns:
        str: Formatted time string
    """
    if seconds >= 1.0:
        return f"{seconds:.{precision}f}s"
    elif seconds >= 0.001:
        return f"{seconds * 1000:.{precision}f}ms"
    elif seconds >= 0.000001:
        return f"{seconds * 1000000:.{precision}f}μs"
    else:
        return f"{seconds * 1000000000:.{precision}f}ns"


def format_memory(bytes_value: int, precision: int = 2) -> str:
    """Format memory size in a human-readable format.
    
    Args:
        bytes_value (int): Memory size in bytes
        precision (int): Number of decimal places
        
    Returns:
        str: Formatted memory string
    """
    if bytes_value >= 1024**3:  # GB
        return f"{bytes_value / (1024**3):.{precision}f} GB"
    elif bytes_value >= 1024**2:  # MB
        return f"{bytes_value / (1024**2):.{precision}f} MB"
    elif bytes_value >= 1024:  # KB
        return f"{bytes_value / 1024:.{precision}f} KB"
    else:
        return f"{bytes_value} B"


def format_percentage(value: float, precision: int = 1) -> str:
    """Format percentage value.
    
    Args:
        value (float): Percentage value (0-100)
        precision (int): Number of decimal places
        
    Returns:
        str: Formatted percentage string
    """
    return f"{value:.{precision}f}%"


def format_rate(value: float, unit: str = "ops", precision: int = 2) -> str:
    """Format rate value (per second).
    
    Args:
        value (float): Rate value
        unit (str): Unit name
        precision (int): Number of decimal places
        
    Returns:
        str: Formatted rate string
    """
    if value >= 1000000:
        return f"{value / 1000000:.{precision}f}M {unit}/s"
    elif value >= 1000:
        return f"{value / 1000:.{precision}f}K {unit}/s"
    else:
        return f"{value:.{precision}f} {unit}/s"


def calculate_percentile(values: List[float], percentile: float) -> float:
    """Calculate percentile of a list of values.
    
    Args:
        values (List[float]): List of values
        percentile (float): Percentile to calculate (0-100)
        
    Returns:
        float: Percentile value
    """
    if not values:
        return 0.0
    
    sorted_values = sorted(values)
    k = (len(sorted_values) - 1) * (percentile / 100.0)
    f = int(k)
    c = k - f
    
    if f + 1 < len(sorted_values):
        return sorted_values[f] * (1 - c) + sorted_values[f + 1] * c
    else:
        return sorted_values[f]


def moving_average(values: List[float], window_size: int) -> List[float]:
    """Calculate moving average of values.
    
    Args:
        values (List[float]): List of values
        window_size (int): Size of the moving window
        
    Returns:
        List[float]: Moving averages
    """
    if len(values) < window_size:
        return []
    
    averages = []
    for i in range(len(values) - window_size + 1):
        window = values[i:i + window_size]
        averages.append(sum(window) / len(window))
    
    return averages


def exponential_smoothing(values: List[float], alpha: float = 0.3) -> List[float]:
    """Apply exponential smoothing to values.
    
    Args:
        values (List[float]): List of values
        alpha (float): Smoothing factor (0-1)
        
    Returns:
        List[float]: Smoothed values
    """
    if not values:
        return []
    
    smoothed = [values[0]]
    
    for i in range(1, len(values)):
        smoothed_value = alpha * values[i] + (1 - alpha) * smoothed[i - 1]
        smoothed.append(smoothed_value)
    
    return smoothed


def calculate_statistics(values: List[float]) -> Dict[str, float]:
    """Calculate comprehensive statistics for a list of values.
    
    Args:
        values (List[float]): List of values
        
    Returns:
        Dict[str, float]: Statistics dictionary
    """
    if not values:
        return {}
    
    stats = {
        'count': len(values),
        'sum': sum(values),
        'mean': statistics.mean(values),
        'median': statistics.median(values),
        'min': min(values),
        'max': max(values),
    }
    
    if len(values) > 1:
        stats.update({
            'std_dev': statistics.stdev(values),
            'variance': statistics.variance(values),
        })
        
        # Percentiles
        stats.update({
            'p25': calculate_percentile(values, 25),
            'p75': calculate_percentile(values, 75),
            'p90': calculate_percentile(values, 90),
            'p95': calculate_percentile(values, 95),
            'p99': calculate_percentile(values, 99),
        })
        
        # Coefficient of variation
        if stats['mean'] > 0:
            stats['cv'] = (stats['std_dev'] / stats['mean']) * 100
    
    return stats


def detect_outliers(values: List[float], method: str = 'iqr', threshold: float = 1.5) -> Tuple[List[int], List[float]]:
    """Detect outliers in a list of values.
    
    Args:
        values (List[float]): List of values
        method (str): Detection method ('iqr', 'zscore', 'modified_zscore')
        threshold (float): Threshold for outlier detection
        
    Returns:
        Tuple[List[int], List[float]]: Indices and values of outliers
    """
    if len(values) < 4:
        return [], []
    
    outlier_indices = []
    outlier_values = []
    
    if method == 'iqr':
        q1 = calculate_percentile(values, 25)
        q3 = calculate_percentile(values, 75)
        iqr = q3 - q1
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        
        for i, value in enumerate(values):
            if value < lower_bound or value > upper_bound:
                outlier_indices.append(i)
                outlier_values.append(value)
    
    elif method == 'zscore':
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values)
        
        for i, value in enumerate(values):
            z_score = abs((value - mean) / std_dev) if std_dev > 0 else 0
            if z_score > threshold:
                outlier_indices.append(i)
                outlier_values.append(value)
    
    elif method == 'modified_zscore':
        median = statistics.median(values)
        mad = statistics.median([abs(x - median) for x in values])
        
        for i, value in enumerate(values):
            modified_z_score = 0.6745 * (value - median) / mad if mad > 0 else 0
            if abs(modified_z_score) > threshold:
                outlier_indices.append(i)
                outlier_values.append(value)
    
    return outlier_indices, outlier_values


def calculate_trend(values: List[float]) -> Dict[str, float]:
    """Calculate trend information for a list of values.
    
    Args:
        values (List[float]): List of values (in chronological order)
        
    Returns:
        Dict[str, float]: Trend information
    """
    if len(values) < 2:
        return {'slope': 0.0, 'direction': 'stable'}
    
    # Calculate linear regression slope
    n = len(values)
    x_values = list(range(n))
    
    x_mean = statistics.mean(x_values)
    y_mean = statistics.mean(values)
    
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
    denominator = sum((x - x_mean) ** 2 for x in x_values)
    
    slope = numerator / denominator if denominator != 0 else 0.0
    
    # Determine trend direction
    if abs(slope) < 0.001:
        direction = 'stable'
    elif slope > 0:
        direction = 'increasing'
    else:
        direction = 'decreasing'
    
    # Calculate correlation coefficient
    if len(values) > 1:
        try:
            correlation = statistics.correlation(x_values, values)
        except statistics.StatisticsError:
            correlation = 0.0
    else:
        correlation = 0.0
    
    return {
        'slope': slope,
        'direction': direction,
        'correlation': correlation,
        'trend_strength': abs(correlation),
    }


def smooth_data(values: List[float], method: str = 'moving_average', **kwargs) -> List[float]:
    """Smooth data using various methods.
    
    Args:
        values (List[float]): Values to smooth
        method (str): Smoothing method
        **kwargs: Method-specific parameters
        
    Returns:
        List[float]: Smoothed values
    """
    if method == 'moving_average':
        window_size = kwargs.get('window_size', 5)
        return moving_average(values, window_size)
    
    elif method == 'exponential':
        alpha = kwargs.get('alpha', 0.3)
        return exponential_smoothing(values, alpha)
    
    else:
        return values.copy()


def aggregate_metrics(metrics_list: List[Dict[str, Any]], 
                     aggregation_method: str = 'mean') -> Dict[str, Any]:
    """Aggregate multiple metric dictionaries.
    
    Args:
        metrics_list (List[Dict[str, Any]]): List of metric dictionaries
        aggregation_method (str): Aggregation method ('mean', 'sum', 'max', 'min')
        
    Returns:
        Dict[str, Any]: Aggregated metrics
    """
    if not metrics_list:
        return {}
    
    # Find all unique keys
    all_keys = set()
    for metrics in metrics_list:
        all_keys.update(metrics.keys())
    
    aggregated = {}
    
    for key in all_keys:
        values = []
        for metrics in metrics_list:
            if key in metrics and isinstance(metrics[key], (int, float)):
                values.append(metrics[key])
        
        if values:
            if aggregation_method == 'mean':
                aggregated[key] = statistics.mean(values)
            elif aggregation_method == 'sum':
                aggregated[key] = sum(values)
            elif aggregation_method == 'max':
                aggregated[key] = max(values)
            elif aggregation_method == 'min':
                aggregated[key] = min(values)
            else:
                aggregated[key] = statistics.mean(values)  # Default to mean
    
    return aggregated


class RollingStatistics:
    """Calculate rolling statistics for streaming data."""
    
    def __init__(self, window_size: int = 100):
        """Initialize rolling statistics.
        
        Args:
            window_size (int): Size of the rolling window
        """
        self.window_size = window_size
        self.values = deque(maxlen=window_size)
        self._sum = 0.0
        self._sum_squares = 0.0
    
    def add_value(self, value: float) -> None:
        """Add a new value to the rolling window.
        
        Args:
            value (float): Value to add
        """
        if len(self.values) == self.window_size:
            # Remove oldest value from sums
            old_value = self.values[0]
            self._sum -= old_value
            self._sum_squares -= old_value ** 2
        
        # Add new value
        self.values.append(value)
        self._sum += value
        self._sum_squares += value ** 2
    
    def get_mean(self) -> float:
        """Get current mean.
        
        Returns:
            float: Current mean
        """
        return self._sum / len(self.values) if self.values else 0.0
    
    def get_variance(self) -> float:
        """Get current variance.
        
        Returns:
            float: Current variance
        """
        if len(self.values) < 2:
            return 0.0
        
        n = len(self.values)
        mean = self.get_mean()
        return (self._sum_squares - n * mean ** 2) / (n - 1)
    
    def get_std_dev(self) -> float:
        """Get current standard deviation.
        
        Returns:
            float: Current standard deviation
        """
        return self.get_variance() ** 0.5
    
    def get_statistics(self) -> Dict[str, float]:
        """Get comprehensive rolling statistics.
        
        Returns:
            Dict[str, float]: Statistics dictionary
        """
        if not self.values:
            return {}
        
        values_list = list(self.values)
        
        return {
            'count': len(values_list),
            'mean': self.get_mean(),
            'std_dev': self.get_std_dev(),
            'min': min(values_list),
            'max': max(values_list),
            'median': statistics.median(values_list),
        }


class PerformanceThresholds:
    """Manage performance thresholds and alerts."""
    
    def __init__(self):
        """Initialize performance thresholds."""
        self.thresholds = {
            # Time-based thresholds (seconds)
            'frame_time_warning': 1.0 / 45,  # Below 45 FPS
            'frame_time_critical': 1.0 / 20,  # Below 20 FPS
            'system_update_warning': 0.01,    # 10ms per system update
            'system_update_critical': 0.05,   # 50ms per system update
            
            # Memory thresholds (bytes)
            'memory_warning': 500 * 1024 * 1024,    # 500MB
            'memory_critical': 1024 * 1024 * 1024,  # 1GB
            'memory_growth_warning': 100 * 1024 * 1024,  # 100MB growth
            
            # CPU thresholds (percentage)
            'cpu_warning': 70.0,
            'cpu_critical': 90.0,
            
            # Event thresholds
            'event_rate_warning': 1000.0,  # Events per second
            'event_rate_critical': 5000.0,
        }
    
    def check_threshold(self, metric_name: str, value: float) -> Optional[str]:
        """Check if a value exceeds thresholds.
        
        Args:
            metric_name (str): Name of the metric
            value (float): Value to check
            
        Returns:
            str: Threshold level ('warning', 'critical') or None
        """
        critical_key = f"{metric_name}_critical"
        warning_key = f"{metric_name}_warning"
        
        if critical_key in self.thresholds and value >= self.thresholds[critical_key]:
            return 'critical'
        elif warning_key in self.thresholds and value >= self.thresholds[warning_key]:
            return 'warning'
        
        return None
    
    def set_threshold(self, metric_name: str, level: str, value: float) -> None:
        """Set a threshold value.
        
        Args:
            metric_name (str): Name of the metric
            level (str): Threshold level ('warning', 'critical')
            value (float): Threshold value
        """
        key = f"{metric_name}_{level}"
        self.thresholds[key] = value
    
    def get_threshold(self, metric_name: str, level: str) -> Optional[float]:
        """Get a threshold value.
        
        Args:
            metric_name (str): Name of the metric
            level (str): Threshold level
            
        Returns:
            float: Threshold value or None if not found
        """
        key = f"{metric_name}_{level}"
        return self.thresholds.get(key)


def create_performance_summary(metrics: Dict[str, Any]) -> str:
    """Create a human-readable performance summary.
    
    Args:
        metrics (Dict[str, Any]): Performance metrics
        
    Returns:
        str: Formatted performance summary
    """
    lines = ["Performance Summary", "=" * 50]
    
    # System metrics
    if 'system_metrics' in metrics:
        lines.append("\nSystem Performance:")
        for system_name, system_metrics in metrics['system_metrics'].items():
            if 'avg_update_time' in system_metrics:
                avg_time = system_metrics['avg_update_time']
                lines.append(f"  {system_name}: {format_time(avg_time)} avg")
    
    # Frame rate
    if 'monitor_metrics' in metrics and 'framerate' in metrics['monitor_metrics']:
        framerate_metrics = metrics['monitor_metrics']['framerate']
        if 'fps' in framerate_metrics:
            fps = framerate_metrics['fps']
            lines.append(f"\nFrame Rate: {fps:.1f} FPS")
    
    # Memory usage
    if 'monitor_metrics' in metrics and 'memory' in metrics['monitor_metrics']:
        memory_metrics = metrics['monitor_metrics']['memory']
        if 'rss' in memory_metrics:
            memory_mb = memory_metrics['rss'] / (1024 * 1024)
            lines.append(f"Memory Usage: {memory_mb:.1f} MB")
    
    # Event rate
    if 'event_metrics' in metrics and 'recent_events_per_second' in metrics['event_metrics']:
        event_rate = metrics['event_metrics']['recent_events_per_second']
        lines.append(f"Event Rate: {event_rate:.1f} events/sec")
    
    return "\n".join(lines)
