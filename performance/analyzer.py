"""Performance analysis and reporting system.

This module provides tools for analyzing performance data, detecting bottlenecks,
identifying trends, and generating comprehensive performance reports.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
from dataclasses import dataclass, field
from enum import Enum, auto
import time
import statistics
import logging
from collections import defaultdict, Counter
import json

from .core import ProfilerResult
from .monitor import MonitorResult, MonitorType

logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Types of performance analysis."""
    
    STATISTICAL = auto()    # Statistical analysis of metrics
    TREND = auto()         # Trend analysis over time
    BOTTLENECK = auto()    # Bottleneck detection
    COMPARISON = auto()    # Performance comparison
    REGRESSION = auto()    # Performance regression detection


class Severity(Enum):
    """Severity levels for performance issues."""
    
    INFO = auto()
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


@dataclass
class AnalysisResult:
    """Result of a performance analysis."""
    
    analysis_type: AnalysisType
    timestamp: float
    severity: Severity
    title: str
    description: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis result to dictionary."""
        return {
            'analysis_type': self.analysis_type.name,
            'timestamp': self.timestamp,
            'severity': self.severity.name,
            'title': self.title,
            'description': self.description,
            'metrics': self.metrics,
            'recommendations': self.recommendations,
            'metadata': self.metadata,
        }


@dataclass
class PerformanceReport:
    """Comprehensive performance report."""
    
    title: str
    generation_time: float
    time_range: Tuple[float, float]
    summary: Dict[str, Any] = field(default_factory=dict)
    analyses: List[AnalysisResult] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_analysis(self, analysis: AnalysisResult) -> None:
        """Add an analysis result to the report.
        
        Args:
            analysis (AnalysisResult): Analysis to add
        """
        self.analyses.append(analysis)
        
        # Add unique recommendations
        for rec in analysis.recommendations:
            if rec not in self.recommendations:
                self.recommendations.append(rec)
    
    def get_severity_counts(self) -> Dict[str, int]:
        """Get count of issues by severity.
        
        Returns:
            Dict[str, int]: Severity counts
        """
        counts = defaultdict(int)
        for analysis in self.analyses:
            counts[analysis.severity.name] += 1
        return dict(counts)
    
    def get_critical_issues(self) -> List[AnalysisResult]:
        """Get critical performance issues.
        
        Returns:
            List[AnalysisResult]: Critical issues
        """
        return [a for a in self.analyses if a.severity == Severity.CRITICAL]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            'title': self.title,
            'generation_time': self.generation_time,
            'time_range': self.time_range,
            'summary': self.summary,
            'analyses': [a.to_dict() for a in self.analyses],
            'recommendations': self.recommendations,
            'severity_counts': self.get_severity_counts(),
            'metadata': self.metadata,
        }
    
    def to_json(self) -> str:
        """Convert report to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


class PerformanceAnalyzer(ABC):
    """Abstract base class for performance analyzers."""
    
    def __init__(self, name: str):
        """Initialize performance analyzer.
        
        Args:
            name (str): Analyzer name
        """
        self.name = name
        self.enabled = True
    
    @abstractmethod
    def analyze(self, data: List[Union[ProfilerResult, MonitorResult]]) -> List[AnalysisResult]:
        """Analyze performance data.
        
        Args:
            data (List): Performance data to analyze
            
        Returns:
            List[AnalysisResult]: Analysis results
        """
        pass
    
    @abstractmethod
    def get_analysis_type(self) -> AnalysisType:
        """Get the analysis type.
        
        Returns:
            AnalysisType: Type of analysis performed
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if analyzer is enabled.
        
        Returns:
            bool: True if enabled
        """
        return self.enabled
    
    def enable(self) -> None:
        """Enable the analyzer."""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable the analyzer."""
        self.enabled = False


class StatisticalAnalyzer(PerformanceAnalyzer):
    """Analyzer for statistical performance analysis."""
    
    def __init__(self):
        """Initialize statistical analyzer."""
        super().__init__("statistical")
    
    def analyze(self, data: List[Union[ProfilerResult, MonitorResult]]) -> List[AnalysisResult]:
        """Perform statistical analysis on performance data.
        
        Args:
            data (List): Performance data to analyze
            
        Returns:
            List[AnalysisResult]: Statistical analysis results
        """
        results = []
        
        if not data:
            return results
        
        try:
            # Separate profiler and monitor results
            profiler_results = [d for d in data if isinstance(d, ProfilerResult)]
            monitor_results = [d for d in data if isinstance(d, MonitorResult)]
            
            # Analyze profiler results
            if profiler_results:
                results.extend(self._analyze_profiler_stats(profiler_results))
            
            # Analyze monitor results
            if monitor_results:
                results.extend(self._analyze_monitor_stats(monitor_results))
            
        except Exception as e:
            logger.error(f"Error in statistical analysis: {e}")
        
        return results
    
    def _analyze_profiler_stats(self, results: List[ProfilerResult]) -> List[AnalysisResult]:
        """Analyze profiler statistics.
        
        Args:
            results (List[ProfilerResult]): Profiler results
            
        Returns:
            List[AnalysisResult]: Analysis results
        """
        analyses = []
        
        # Group by operation name
        operations = defaultdict(list)
        for result in results:
            operations[result.name].append(result.duration)
        
        for op_name, durations in operations.items():
            if len(durations) < 2:
                continue
            
            # Calculate statistics
            mean_duration = statistics.mean(durations)
            median_duration = statistics.median(durations)
            stdev_duration = statistics.stdev(durations) if len(durations) > 1 else 0
            min_duration = min(durations)
            max_duration = max(durations)
            
            # Detect outliers (values > 2 standard deviations from mean)
            outliers = [d for d in durations if abs(d - mean_duration) > 2 * stdev_duration]
            outlier_percentage = (len(outliers) / len(durations)) * 100
            
            # Determine severity
            severity = Severity.INFO
            recommendations = []
            
            if outlier_percentage > 20:
                severity = Severity.HIGH
                recommendations.append(f"High variability in {op_name} performance - investigate inconsistent execution times")
            elif outlier_percentage > 10:
                severity = Severity.MEDIUM
                recommendations.append(f"Moderate variability in {op_name} performance - consider optimization")
            
            if max_duration > mean_duration * 5:
                severity = max(severity, Severity.HIGH)
                recommendations.append(f"Extreme outliers detected in {op_name} - investigate worst-case scenarios")
            
            analysis = AnalysisResult(
                analysis_type=AnalysisType.STATISTICAL,
                timestamp=time.time(),
                severity=severity,
                title=f"Statistical Analysis: {op_name}",
                description=f"Performance statistics for {op_name} operation",
                metrics={
                    'operation': op_name,
                    'sample_count': len(durations),
                    'mean_duration': mean_duration,
                    'median_duration': median_duration,
                    'std_deviation': stdev_duration,
                    'min_duration': min_duration,
                    'max_duration': max_duration,
                    'outlier_count': len(outliers),
                    'outlier_percentage': outlier_percentage,
                    'coefficient_of_variation': (stdev_duration / mean_duration) * 100 if mean_duration > 0 else 0,
                },
                recommendations=recommendations
            )
            
            analyses.append(analysis)
        
        return analyses
    
    def _analyze_monitor_stats(self, results: List[MonitorResult]) -> List[AnalysisResult]:
        """Analyze monitor statistics.
        
        Args:
            results (List[MonitorResult]): Monitor results
            
        Returns:
            List[AnalysisResult]: Analysis results
        """
        analyses = []
        
        # Group by monitor type
        by_type = defaultdict(list)
        for result in results:
            by_type[result.monitor_type].append(result)
        
        for monitor_type, type_results in by_type.items():
            if monitor_type == MonitorType.SYSTEM:
                analyses.extend(self._analyze_system_stats(type_results))
            elif monitor_type == MonitorType.FRAME_RATE:
                analyses.extend(self._analyze_framerate_stats(type_results))
            elif monitor_type == MonitorType.MEMORY:
                analyses.extend(self._analyze_memory_stats(type_results))
        
        return analyses
    
    def _analyze_system_stats(self, results: List[MonitorResult]) -> List[AnalysisResult]:
        """Analyze system monitor statistics."""
        analyses = []
        
        # Extract CPU usage
        cpu_values = [r.get_metric('cpu_percent', 0) for r in results if r.get_metric('cpu_percent') is not None]
        if cpu_values:
            mean_cpu = statistics.mean(cpu_values)
            max_cpu = max(cpu_values)
            
            severity = Severity.INFO
            recommendations = []
            
            if mean_cpu > 80:
                severity = Severity.HIGH
                recommendations.append("High average CPU usage - consider optimization or load balancing")
            elif mean_cpu > 60:
                severity = Severity.MEDIUM
                recommendations.append("Moderate CPU usage - monitor for performance impact")
            
            if max_cpu > 95:
                severity = max(severity, Severity.CRITICAL)
                recommendations.append("CPU usage spikes detected - investigate performance bottlenecks")
            
            analyses.append(AnalysisResult(
                analysis_type=AnalysisType.STATISTICAL,
                timestamp=time.time(),
                severity=severity,
                title="CPU Usage Analysis",
                description="Statistical analysis of CPU utilization",
                metrics={
                    'mean_cpu_percent': mean_cpu,
                    'max_cpu_percent': max_cpu,
                    'sample_count': len(cpu_values),
                },
                recommendations=recommendations
            ))
        
        return analyses
    
    def _analyze_framerate_stats(self, results: List[MonitorResult]) -> List[AnalysisResult]:
        """Analyze frame rate statistics."""
        analyses = []
        
        fps_values = [r.get_metric('fps', 0) for r in results if r.get_metric('fps') is not None]
        if fps_values:
            mean_fps = statistics.mean(fps_values)
            min_fps = min(fps_values)
            
            severity = Severity.INFO
            recommendations = []
            
            if mean_fps < 30:
                severity = Severity.HIGH
                recommendations.append("Low average FPS - significant performance optimization needed")
            elif mean_fps < 45:
                severity = Severity.MEDIUM
                recommendations.append("Below-target FPS - consider performance improvements")
            
            if min_fps < 15:
                severity = max(severity, Severity.CRITICAL)
                recommendations.append("Severe FPS drops detected - investigate frame time spikes")
            
            analyses.append(AnalysisResult(
                analysis_type=AnalysisType.STATISTICAL,
                timestamp=time.time(),
                severity=severity,
                title="Frame Rate Analysis",
                description="Statistical analysis of frame rate performance",
                metrics={
                    'mean_fps': mean_fps,
                    'min_fps': min_fps,
                    'sample_count': len(fps_values),
                },
                recommendations=recommendations
            ))
        
        return analyses
    
    def _analyze_memory_stats(self, results: List[MonitorResult]) -> List[AnalysisResult]:
        """Analyze memory usage statistics."""
        analyses = []
        
        memory_values = [r.get_metric('rss', 0) for r in results if r.get_metric('rss') is not None]
        if memory_values:
            mean_memory = statistics.mean(memory_values)
            max_memory = max(memory_values)
            min_memory = min(memory_values)
            memory_growth = max_memory - min_memory
            
            severity = Severity.INFO
            recommendations = []
            
            # Check for memory growth
            growth_percentage = (memory_growth / min_memory) * 100 if min_memory > 0 else 0
            if growth_percentage > 50:
                severity = Severity.HIGH
                recommendations.append("Significant memory growth detected - investigate memory leaks")
            elif growth_percentage > 25:
                severity = Severity.MEDIUM
                recommendations.append("Moderate memory growth - monitor for potential leaks")
            
            analyses.append(AnalysisResult(
                analysis_type=AnalysisType.STATISTICAL,
                timestamp=time.time(),
                severity=severity,
                title="Memory Usage Analysis",
                description="Statistical analysis of memory consumption",
                metrics={
                    'mean_memory_mb': mean_memory / (1024 * 1024),
                    'max_memory_mb': max_memory / (1024 * 1024),
                    'memory_growth_mb': memory_growth / (1024 * 1024),
                    'growth_percentage': growth_percentage,
                    'sample_count': len(memory_values),
                },
                recommendations=recommendations
            ))
        
        return analyses
    
    def get_analysis_type(self) -> AnalysisType:
        """Get analysis type."""
        return AnalysisType.STATISTICAL


class TrendAnalyzer(PerformanceAnalyzer):
    """Analyzer for performance trend analysis."""
    
    def __init__(self, window_size: int = 50):
        """Initialize trend analyzer.
        
        Args:
            window_size (int): Size of the analysis window
        """
        super().__init__("trend")
        self.window_size = window_size
    
    def analyze(self, data: List[Union[ProfilerResult, MonitorResult]]) -> List[AnalysisResult]:
        """Analyze performance trends.
        
        Args:
            data (List): Performance data to analyze
            
        Returns:
            List[AnalysisResult]: Trend analysis results
        """
        results = []
        
        if len(data) < self.window_size:
            return results
        
        try:
            # Sort by timestamp
            sorted_data = sorted(data, key=lambda x: getattr(x, 'timestamp', getattr(x, 'start_time', 0)))
            
            # Analyze different metrics for trends
            if isinstance(sorted_data[0], ProfilerResult):
                results.extend(self._analyze_profiler_trends(sorted_data))
            elif isinstance(sorted_data[0], MonitorResult):
                results.extend(self._analyze_monitor_trends(sorted_data))
            
        except Exception as e:
            logger.error(f"Error in trend analysis: {e}")
        
        return results
    
    def _analyze_profiler_trends(self, results: List[ProfilerResult]) -> List[AnalysisResult]:
        """Analyze profiler trends."""
        analyses = []
        
        # Group by operation
        operations = defaultdict(list)
        for result in results:
            operations[result.name].append((result.start_time, result.duration))
        
        for op_name, time_series in operations.items():
            if len(time_series) < self.window_size:
                continue
            
            # Sort by time
            time_series.sort(key=lambda x: x[0])
            
            # Calculate trend
            durations = [duration for _, duration in time_series[-self.window_size:]]
            trend_slope = self._calculate_trend_slope(durations)
            
            severity = Severity.INFO
            recommendations = []
            
            if trend_slope > 0.001:  # Increasing duration trend
                severity = Severity.MEDIUM
                recommendations.append(f"Performance degradation trend detected in {op_name}")
            elif trend_slope > 0.005:
                severity = Severity.HIGH
                recommendations.append(f"Significant performance degradation in {op_name} - immediate investigation needed")
            
            analyses.append(AnalysisResult(
                analysis_type=AnalysisType.TREND,
                timestamp=time.time(),
                severity=severity,
                title=f"Trend Analysis: {op_name}",
                description=f"Performance trend analysis for {op_name}",
                metrics={
                    'operation': op_name,
                    'trend_slope': trend_slope,
                    'sample_count': len(durations),
                    'recent_mean': statistics.mean(durations),
                },
                recommendations=recommendations
            ))
        
        return analyses
    
    def _analyze_monitor_trends(self, results: List[MonitorResult]) -> List[AnalysisResult]:
        """Analyze monitor trends."""
        analyses = []
        
        # Analyze FPS trends
        fps_values = [(r.timestamp, r.get_metric('fps', 0)) for r in results if r.get_metric('fps') is not None]
        if len(fps_values) >= self.window_size:
            fps_trend = self._calculate_trend_slope([fps for _, fps in fps_values[-self.window_size:]])
            
            severity = Severity.INFO
            recommendations = []
            
            if fps_trend < -0.5:  # Decreasing FPS trend
                severity = Severity.HIGH
                recommendations.append("Frame rate degradation trend detected - investigate performance issues")
            elif fps_trend < -0.1:
                severity = Severity.MEDIUM
                recommendations.append("Moderate FPS decline trend - monitor performance")
            
            analyses.append(AnalysisResult(
                analysis_type=AnalysisType.TREND,
                timestamp=time.time(),
                severity=severity,
                title="FPS Trend Analysis",
                description="Frame rate performance trend analysis",
                metrics={
                    'fps_trend_slope': fps_trend,
                    'sample_count': len(fps_values),
                },
                recommendations=recommendations
            ))
        
        return analyses
    
    def _calculate_trend_slope(self, values: List[float]) -> float:
        """Calculate trend slope using linear regression.
        
        Args:
            values (List[float]): Values to analyze
            
        Returns:
            float: Trend slope
        """
        if len(values) < 2:
            return 0.0
        
        n = len(values)
        x_values = list(range(n))
        
        # Calculate slope using least squares
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(values)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        return numerator / denominator if denominator != 0 else 0.0
    
    def get_analysis_type(self) -> AnalysisType:
        """Get analysis type."""
        return AnalysisType.TREND


class BottleneckDetector(PerformanceAnalyzer):
    """Analyzer for detecting performance bottlenecks."""
    
    def __init__(self, threshold_percentile: float = 95.0):
        """Initialize bottleneck detector.
        
        Args:
            threshold_percentile (float): Percentile threshold for bottleneck detection
        """
        super().__init__("bottleneck")
        self.threshold_percentile = threshold_percentile
    
    def analyze(self, data: List[Union[ProfilerResult, MonitorResult]]) -> List[AnalysisResult]:
        """Detect performance bottlenecks.
        
        Args:
            data (List): Performance data to analyze
            
        Returns:
            List[AnalysisResult]: Bottleneck analysis results
        """
        results = []
        
        if not data:
            return results
        
        try:
            profiler_results = [d for d in data if isinstance(d, ProfilerResult)]
            if profiler_results:
                results.extend(self._detect_profiler_bottlenecks(profiler_results))
            
        except Exception as e:
            logger.error(f"Error in bottleneck detection: {e}")
        
        return results
    
    def _detect_profiler_bottlenecks(self, results: List[ProfilerResult]) -> List[AnalysisResult]:
        """Detect bottlenecks in profiler results."""
        analyses = []
        
        # Calculate total time and find slowest operations
        total_time = sum(r.duration for r in results)
        operation_times = defaultdict(list)
        
        for result in results:
            operation_times[result.name].append(result.duration)
        
        # Calculate aggregate times per operation
        operation_totals = {}
        for op_name, durations in operation_times.items():
            operation_totals[op_name] = {
                'total_time': sum(durations),
                'call_count': len(durations),
                'mean_time': statistics.mean(durations),
                'max_time': max(durations),
                'percentage': (sum(durations) / total_time) * 100 if total_time > 0 else 0
            }
        
        # Sort by total time
        sorted_operations = sorted(operation_totals.items(), key=lambda x: x[1]['total_time'], reverse=True)
        
        # Identify bottlenecks
        for op_name, metrics in sorted_operations[:10]:  # Top 10 time consumers
            severity = Severity.INFO
            recommendations = []
            
            if metrics['percentage'] > 30:
                severity = Severity.HIGH
                recommendations.append(f"{op_name} consumes {metrics['percentage']:.1f}% of total execution time - major bottleneck")
            elif metrics['percentage'] > 15:
                severity = Severity.MEDIUM
                recommendations.append(f"{op_name} consumes {metrics['percentage']:.1f}% of total execution time - optimization opportunity")
            
            # Check for slow individual calls
            if metrics['max_time'] > metrics['mean_time'] * 10:
                severity = max(severity, Severity.HIGH)
                recommendations.append(f"Extreme outliers detected in {op_name} - investigate worst-case performance")
            
            analyses.append(AnalysisResult(
                analysis_type=AnalysisType.BOTTLENECK,
                timestamp=time.time(),
                severity=severity,
                title=f"Bottleneck Analysis: {op_name}",
                description=f"Performance bottleneck analysis for {op_name}",
                metrics=metrics,
                recommendations=recommendations
            ))
        
        return analyses
    
    def get_analysis_type(self) -> AnalysisType:
        """Get analysis type."""
        return AnalysisType.BOTTLENECK


class Benchmark:
    """Performance benchmark for comparison analysis."""
    
    def __init__(self, name: str, baseline_metrics: Dict[str, float]):
        """Initialize benchmark.
        
        Args:
            name (str): Benchmark name
            baseline_metrics (Dict[str, float]): Baseline performance metrics
        """
        self.name = name
        self.baseline_metrics = baseline_metrics
        self.timestamp = time.time()
    
    def compare(self, current_metrics: Dict[str, float]) -> Dict[str, float]:
        """Compare current metrics to baseline.
        
        Args:
            current_metrics (Dict[str, float]): Current performance metrics
            
        Returns:
            Dict[str, float]: Comparison ratios (current/baseline)
        """
        comparison = {}
        
        for metric_name, baseline_value in self.baseline_metrics.items():
            if metric_name in current_metrics and baseline_value > 0:
                comparison[metric_name] = current_metrics[metric_name] / baseline_value
        
        return comparison
