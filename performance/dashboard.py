"""Simple performance dashboard for real-time monitoring.

This module provides a text-based dashboard for monitoring performance metrics
in real-time. It's designed to be lightweight and work in terminal environments.
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
import time
import threading
from collections import deque

from .utils import format_time, format_memory, format_percentage, format_rate
from .alerts import AlertManager, PerformanceAlert, AlertSeverity


@dataclass
class DashboardConfig:
    """Configuration for the performance dashboard."""
    
    # Display settings
    refresh_interval: float = 1.0      # Seconds between updates
    max_lines: int = 50               # Maximum lines to display
    show_alerts: bool = True          # Show active alerts
    show_trends: bool = True          # Show trend indicators
    
    # Metric display settings
    show_system_metrics: bool = True
    show_memory_metrics: bool = True
    show_frame_metrics: bool = True
    show_event_metrics: bool = True
    
    # Alert settings
    max_alerts_shown: int = 5
    alert_age_limit: float = 300.0    # 5 minutes
    
    # Formatting
    decimal_places: int = 2
    use_colors: bool = True           # Use ANSI colors if supported


class MetricWidget:
    """Widget for displaying a single metric."""
    
    def __init__(self, name: str, format_func: Callable[[Any], str] = str,
                 trend_history_size: int = 10):
        """Initialize metric widget.
        
        Args:
            name (str): Metric name
            format_func (Callable): Function to format the metric value
            trend_history_size (int): Number of values to keep for trend calculation
        """
        self.name = name
        self.format_func = format_func
        self.history = deque(maxlen=trend_history_size)
        self.current_value = None
        self.last_update = None
    
    def update(self, value: Any) -> None:
        """Update the metric value.
        
        Args:
            value (Any): New metric value
        """
        if isinstance(value, (int, float)):
            self.history.append(value)
        
        self.current_value = value
        self.last_update = time.time()
    
    def get_trend(self) -> str:
        """Get trend indicator.
        
        Returns:
            str: Trend indicator ('↑', '↓', '→', '?')
        """
        if len(self.history) < 2:
            return '?'
        
        recent = list(self.history)[-3:]  # Last 3 values
        if len(recent) < 2:
            return '?'
        
        # Simple trend calculation
        if recent[-1] > recent[0] * 1.05:  # 5% increase
            return '↑'
        elif recent[-1] < recent[0] * 0.95:  # 5% decrease
            return '↓'
        else:
            return '→'
    
    def format_value(self) -> str:
        """Format the current value.
        
        Returns:
            str: Formatted value
        """
        if self.current_value is None:
            return "N/A"
        
        return self.format_func(self.current_value)
    
    def render(self, show_trend: bool = True) -> str:
        """Render the widget as a string.
        
        Args:
            show_trend (bool): Whether to show trend indicator
            
        Returns:
            str: Rendered widget
        """
        value_str = self.format_value()
        
        if show_trend:
            trend = self.get_trend()
            return f"{self.name}: {value_str} {trend}"
        else:
            return f"{self.name}: {value_str}"


class ChartWidget:
    """Simple ASCII chart widget for displaying metric history."""
    
    def __init__(self, name: str, width: int = 40, height: int = 8):
        """Initialize chart widget.
        
        Args:
            name (str): Chart name
            width (int): Chart width in characters
            height (int): Chart height in lines
        """
        self.name = name
        self.width = width
        self.height = height
        self.data = deque(maxlen=width)
    
    def add_data_point(self, value: float) -> None:
        """Add a data point to the chart.
        
        Args:
            value (float): Data point value
        """
        self.data.append(value)
    
    def render(self) -> List[str]:
        """Render the chart as ASCII art.
        
        Returns:
            List[str]: Chart lines
        """
        if not self.data:
            return [f"{self.name}: No data"]
        
        # Normalize data to chart height
        min_val = min(self.data)
        max_val = max(self.data)
        
        if max_val == min_val:
            # All values are the same
            normalized = [self.height // 2] * len(self.data)
        else:
            normalized = [
                int((val - min_val) / (max_val - min_val) * (self.height - 1))
                for val in self.data
            ]
        
        # Create chart lines
        lines = [f"{self.name} ({min_val:.2f} - {max_val:.2f})"]
        
        # Build chart from top to bottom
        for row in range(self.height - 1, -1, -1):
            line = ""
            for col, height_val in enumerate(normalized):
                if height_val >= row:
                    line += "█"
                else:
                    line += " "
            
            # Pad line to full width
            line = line.ljust(self.width)
            lines.append(line)
        
        return lines


class AlertWidget:
    """Widget for displaying active alerts."""
    
    def __init__(self, max_alerts: int = 5):
        """Initialize alert widget.
        
        Args:
            max_alerts (int): Maximum alerts to display
        """
        self.max_alerts = max_alerts
    
    def render(self, alerts: List[PerformanceAlert], use_colors: bool = True) -> List[str]:
        """Render alerts as strings.
        
        Args:
            alerts (List[PerformanceAlert]): Alerts to display
            use_colors (bool): Whether to use ANSI colors
            
        Returns:
            List[str]: Alert lines
        """
        if not alerts:
            return ["Alerts: None"]
        
        lines = ["Active Alerts:"]
        
        # Sort by severity and time
        sorted_alerts = sorted(alerts, key=lambda x: (x.severity.value, -x.timestamp))
        
        for alert in sorted_alerts[:self.max_alerts]:
            severity_str = alert.severity.name
            age = alert.get_age()
            age_str = format_time(age)
            
            # Color coding
            if use_colors:
                if alert.severity == AlertSeverity.CRITICAL:
                    color = "\033[91m"  # Red
                elif alert.severity == AlertSeverity.WARNING:
                    color = "\033[93m"  # Yellow
                else:
                    color = "\033[92m"  # Green
                reset = "\033[0m"
            else:
                color = ""
                reset = ""
            
            status = "ACK" if alert.acknowledged else "NEW"
            line = f"  {color}[{severity_str}]{reset} {alert.title} ({age_str} ago) [{status}]"
            lines.append(line)
        
        if len(alerts) > self.max_alerts:
            lines.append(f"  ... and {len(alerts) - self.max_alerts} more")
        
        return lines


class PerformanceDashboard:
    """Main performance dashboard class."""
    
    def __init__(self, config: DashboardConfig = None):
        """Initialize performance dashboard.
        
        Args:
            config (DashboardConfig, optional): Dashboard configuration
        """
        self.config = config or DashboardConfig()
        
        # Widgets
        self.metric_widgets: Dict[str, MetricWidget] = {}
        self.chart_widgets: Dict[str, ChartWidget] = {}
        self.alert_widget = AlertWidget(self.config.max_alerts_shown)
        
        # Data sources
        self.alert_manager: Optional[AlertManager] = None
        self.metrics_callback: Optional[Callable[[], Dict[str, Any]]] = None
        
        # Display state
        self.running = False
        self.display_thread: Optional[threading.Thread] = None
        self.last_update = time.time()
        
        # Initialize default widgets
        self._initialize_widgets()
    
    def _initialize_widgets(self) -> None:
        """Initialize default metric widgets."""
        # System metrics
        if self.config.show_system_metrics:
            self.metric_widgets['cpu'] = MetricWidget(
                "CPU", lambda x: format_percentage(x, 1)
            )
            self.chart_widgets['cpu'] = ChartWidget("CPU Usage %")
        
        # Memory metrics
        if self.config.show_memory_metrics:
            self.metric_widgets['memory'] = MetricWidget(
                "Memory", lambda x: format_memory(x)
            )
            self.chart_widgets['memory'] = ChartWidget("Memory Usage")
        
        # Frame rate metrics
        if self.config.show_frame_metrics:
            self.metric_widgets['fps'] = MetricWidget(
                "FPS", lambda x: f"{x:.1f}"
            )
            self.chart_widgets['fps'] = ChartWidget("Frame Rate")
        
        # Event metrics
        if self.config.show_event_metrics:
            self.metric_widgets['events'] = MetricWidget(
                "Events/sec", lambda x: format_rate(x, "events")
            )
    
    def set_alert_manager(self, alert_manager: AlertManager) -> None:
        """Set the alert manager for displaying alerts.
        
        Args:
            alert_manager (AlertManager): Alert manager instance
        """
        self.alert_manager = alert_manager
    
    def set_metrics_callback(self, callback: Callable[[], Dict[str, Any]]) -> None:
        """Set callback for retrieving metrics.
        
        Args:
            callback (Callable): Function that returns current metrics
        """
        self.metrics_callback = callback
    
    def add_metric_widget(self, name: str, widget: MetricWidget) -> None:
        """Add a custom metric widget.
        
        Args:
            name (str): Widget name
            widget (MetricWidget): Widget instance
        """
        self.metric_widgets[name] = widget
    
    def add_chart_widget(self, name: str, widget: ChartWidget) -> None:
        """Add a custom chart widget.
        
        Args:
            name (str): Widget name
            widget (ChartWidget): Widget instance
        """
        self.chart_widgets[name] = widget
    
    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update dashboard with new metrics.
        
        Args:
            metrics (Dict[str, Any]): Performance metrics
        """
        current_time = time.time()
        
        # Update system metrics
        if 'monitor_metrics' in metrics:
            monitor_metrics = metrics['monitor_metrics']
            
            # System metrics
            if 'system' in monitor_metrics:
                system_metrics = monitor_metrics['system']
                if 'cpu_percent' in system_metrics and 'cpu' in self.metric_widgets:
                    cpu_value = system_metrics['cpu_percent']
                    self.metric_widgets['cpu'].update(cpu_value)
                    if 'cpu' in self.chart_widgets:
                        self.chart_widgets['cpu'].add_data_point(cpu_value)
            
            # Memory metrics
            if 'memory' in monitor_metrics:
                memory_metrics = monitor_metrics['memory']
                if 'rss' in memory_metrics and 'memory' in self.metric_widgets:
                    memory_value = memory_metrics['rss']
                    self.metric_widgets['memory'].update(memory_value)
                    if 'memory' in self.chart_widgets:
                        self.chart_widgets['memory'].add_data_point(memory_value / (1024 * 1024))  # MB
            
            # Frame rate metrics
            if 'framerate' in monitor_metrics:
                framerate_metrics = monitor_metrics['framerate']
                if 'fps' in framerate_metrics and 'fps' in self.metric_widgets:
                    fps_value = framerate_metrics['fps']
                    self.metric_widgets['fps'].update(fps_value)
                    if 'fps' in self.chart_widgets:
                        self.chart_widgets['fps'].add_data_point(fps_value)
        
        # Update event metrics
        if 'event_metrics' in metrics and 'events' in self.metric_widgets:
            event_metrics = metrics['event_metrics']
            if 'recent_events_per_second' in event_metrics:
                events_value = event_metrics['recent_events_per_second']
                self.metric_widgets['events'].update(events_value)
        
        self.last_update = current_time
    
    def render(self) -> str:
        """Render the dashboard as a string.
        
        Returns:
            str: Rendered dashboard
        """
        lines = []
        
        # Header
        lines.append("=" * 60)
        lines.append("Performance Dashboard")
        lines.append(f"Last Update: {time.strftime('%H:%M:%S', time.localtime(self.last_update))}")
        lines.append("=" * 60)
        
        # Metric widgets
        if self.metric_widgets:
            lines.append("\nMetrics:")
            for widget in self.metric_widgets.values():
                lines.append(f"  {widget.render(self.config.show_trends)}")
        
        # Chart widgets (simplified for text display)
        if self.chart_widgets and self.config.show_trends:
            lines.append("\nTrends:")
            for name, widget in self.chart_widgets.items():
                if widget.data:
                    recent_values = list(widget.data)[-5:]  # Last 5 values
                    trend_line = " ".join([f"{v:.1f}" for v in recent_values])
                    lines.append(f"  {name}: {trend_line}")
        
        # Alerts
        if self.config.show_alerts and self.alert_manager:
            active_alerts = self.alert_manager.get_active_alerts()
            # Filter by age
            current_time = time.time()
            recent_alerts = [
                alert for alert in active_alerts 
                if current_time - alert.timestamp <= self.config.alert_age_limit
            ]
            
            alert_lines = self.alert_widget.render(recent_alerts, self.config.use_colors)
            lines.append("")
            lines.extend(alert_lines)
        
        # Footer
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def start(self) -> None:
        """Start the dashboard display loop."""
        if self.running:
            return
        
        self.running = True
        self.display_thread = threading.Thread(target=self._display_loop, daemon=True)
        self.display_thread.start()
    
    def stop(self) -> None:
        """Stop the dashboard display loop."""
        self.running = False
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=1.0)
    
    def _display_loop(self) -> None:
        """Main display loop (runs in separate thread)."""
        while self.running:
            try:
                # Update metrics if callback is available
                if self.metrics_callback:
                    metrics = self.metrics_callback()
                    self.update_metrics(metrics)
                
                # Clear screen and display dashboard
                # Note: This is a simple implementation
                # In a real terminal app, you'd use proper screen clearing
                print("\033[2J\033[H")  # Clear screen and move cursor to top
                print(self.render())
                
                # Sleep until next update
                time.sleep(self.config.refresh_interval)
                
            except Exception as e:
                print(f"Dashboard error: {e}")
                time.sleep(1.0)
    
    def print_once(self) -> None:
        """Print the dashboard once (for non-interactive use)."""
        if self.metrics_callback:
            metrics = self.metrics_callback()
            self.update_metrics(metrics)
        
        print(self.render())


def create_dashboard(alert_manager: AlertManager = None,
                    metrics_callback: Callable[[], Dict[str, Any]] = None,
                    config: DashboardConfig = None) -> PerformanceDashboard:
    """Create a configured performance dashboard.
    
    Args:
        alert_manager (AlertManager, optional): Alert manager for displaying alerts
        metrics_callback (Callable, optional): Function to retrieve metrics
        config (DashboardConfig, optional): Dashboard configuration
        
    Returns:
        PerformanceDashboard: Configured dashboard
    """
    dashboard = PerformanceDashboard(config)
    
    if alert_manager:
        dashboard.set_alert_manager(alert_manager)
    
    if metrics_callback:
        dashboard.set_metrics_callback(metrics_callback)
    
    return dashboard
