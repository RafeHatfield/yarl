"""Instrumentation and telemetry subsystem for the game.

This package contains modules for tracking and reporting gameplay metrics,
performance data, and run statistics.
"""

from instrumentation.run_metrics import RunMetrics, RunMetricsRecorder

__all__ = ["RunMetrics", "RunMetricsRecorder"]

