"""Comprehensive performance profiling and monitoring system.

This package provides advanced performance monitoring capabilities for the game engine,
including real-time profiling, memory tracking, frame rate analysis, and performance
visualization tools.

Key Components:
- Profiler: High-precision timing and measurement system
- Monitor: System-level performance monitoring
- Analyzer: Performance data analysis and reporting
- Dashboard: Real-time performance visualization
- Alerts: Automatic performance issue detection
- Reports: Detailed performance analysis and recommendations
"""

from .core import (
    PerformanceProfiler, ProfilerContext, ProfilerResult, ProfilerError,
    Timer, HighPrecisionTimer, FrameTimer, SystemTimer,
    get_global_profiler, profile, profile_function
)
from .monitor import (
    PerformanceMonitor, SystemMonitor, MemoryMonitor, FrameRateMonitor,
    EventMonitor, CustomMonitor, MonitorConfig, MonitorResult
)
from .analyzer import (
    PerformanceAnalyzer, AnalysisResult, PerformanceReport, Benchmark,
    BottleneckDetector, TrendAnalyzer, StatisticalAnalyzer, Severity
)
from .dashboard import (
    PerformanceDashboard, DashboardConfig, MetricWidget, ChartWidget,
    AlertWidget, create_dashboard
)
from .alerts import (
    PerformanceAlert, AlertManager, AlertRule, AlertCondition,
    AlertSeverity, create_alert_rule, ThresholdCondition, TrendCondition,
    create_threshold_rule, create_trend_rule
)
from .integration import (
    GameEngineProfiler, SystemProfiler, EventProfiler, StateProfiler,
    integrate_profiling, ProfiledSystem, ProfilingConfig
)
from .utils import (
    format_time, format_memory, format_percentage, format_rate,
    calculate_percentile, moving_average, exponential_smoothing,
    calculate_statistics, RollingStatistics, PerformanceThresholds
)

__all__ = [
    # Core
    'PerformanceProfiler',
    'ProfilerContext',
    'ProfilerResult',
    'ProfilerError',
    'Timer',
    'HighPrecisionTimer',
    'FrameTimer',
    'SystemTimer',
    'get_global_profiler',
    'profile',
    'profile_function',
    
    # Monitor
    'PerformanceMonitor',
    'SystemMonitor',
    'MemoryMonitor',
    'FrameRateMonitor',
    'EventMonitor',
    'CustomMonitor',
    'MonitorConfig',
    'MonitorResult',
    
    # Analyzer
    'PerformanceAnalyzer',
    'AnalysisResult',
    'PerformanceReport',
    'Benchmark',
    'BottleneckDetector',
    'TrendAnalyzer',
    'StatisticalAnalyzer',
    'Severity',
    
    # Dashboard
    'PerformanceDashboard',
    'DashboardConfig',
    'MetricWidget',
    'ChartWidget',
    'AlertWidget',
    'create_dashboard',
    
    # Alerts
    'PerformanceAlert',
    'AlertManager',
    'AlertRule',
    'AlertCondition',
    'AlertSeverity',
    'create_alert_rule',
    'ThresholdCondition',
    'TrendCondition',
    'create_threshold_rule',
    'create_trend_rule',
    
    # Integration
    'GameEngineProfiler',
    'SystemProfiler',
    'EventProfiler',
    'StateProfiler',
    'integrate_profiling',
    'ProfiledSystem',
    'ProfilingConfig',
    
    # Utils
    'format_time',
    'format_memory',
    'format_percentage',
    'format_rate',
    'calculate_percentile',
    'moving_average',
    'exponential_smoothing',
    'calculate_statistics',
    'RollingStatistics',
    'PerformanceThresholds',
]
