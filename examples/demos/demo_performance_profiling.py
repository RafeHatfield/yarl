"""Demonstration of the comprehensive performance profiling system.

This script showcases the key features of the performance profiling system
including profiling, monitoring, analysis, alerts, and dashboard display.
"""

import time
import random
import threading
from typing import Dict, Any

from performance import (
    # Core profiling
    PerformanceProfiler, get_global_profiler, profile,
    
    # Monitoring
    SystemMonitor, MemoryMonitor, FrameRateMonitor, CustomMonitor, MonitorConfig,
    
    # Analysis
    StatisticalAnalyzer, TrendAnalyzer, BottleneckDetector,
    
    # Alerts
    AlertManager, create_threshold_rule, create_trend_rule, AlertSeverity,
    
    # Integration
    GameEngineProfiler, ProfilingConfig,
    
    # Dashboard
    create_dashboard, DashboardConfig,
    
    # Utils
    format_time, format_memory, format_percentage,
)

from events import EventBus, SimpleEvent, initialize_event_bus
from engine.game_engine import GameEngine
from engine.system import System


class DemoSystem(System):
    """Demo system that simulates various performance characteristics."""
    
    def __init__(self, name: str, base_duration: float = 0.001, variability: float = 0.5):
        """Initialize demo system.
        
        Args:
            name (str): System name
            base_duration (float): Base update duration in seconds
            variability (float): Duration variability factor (0-1)
        """
        super().__init__(name)
        self.base_duration = base_duration
        self.variability = variability
        self.update_count = 0
        self.performance_degradation = 0.0  # Simulates gradual slowdown
    
    def update(self, dt: float) -> None:
        """Simulate system update with variable performance."""
        self.update_count += 1
        
        # Calculate duration with variability and degradation
        duration = self.base_duration * (1 + random.uniform(-self.variability, self.variability))
        duration += self.performance_degradation
        
        # Simulate gradual performance degradation
        if self.update_count % 100 == 0:
            self.performance_degradation += 0.0001
        
        # Simulate work
        time.sleep(max(0.0001, duration))


def simulate_game_operations(profiler: PerformanceProfiler, duration: float = 30.0):
    """Simulate various game operations with profiling.
    
    Args:
        profiler (PerformanceProfiler): Profiler to use
        duration (float): Simulation duration in seconds
    """
    print("🎮 Starting game operation simulation...")
    
    start_time = time.time()
    frame_count = 0
    
    while time.time() - start_time < duration:
        frame_start = time.time()
        
        # Simulate frame processing
        with profiler.profile("frame_processing") as ctx:
            ctx.metadata['frame_number'] = frame_count
            
            # Input processing (fast)
            with profiler.profile("input_processing"):
                time.sleep(0.0005 + random.uniform(0, 0.0005))
            
            # Game logic (variable)
            with profiler.profile("game_logic"):
                complexity = random.choice([0.001, 0.002, 0.005, 0.01])  # Variable complexity
                time.sleep(complexity)
            
            # AI processing (occasionally slow)
            with profiler.profile("ai_processing"):
                if random.random() < 0.1:  # 10% chance of complex AI
                    time.sleep(0.01)  # Expensive AI operation
                else:
                    time.sleep(0.001)
            
            # Rendering (usually fast, occasionally slow)
            with profiler.profile("rendering"):
                if random.random() < 0.05:  # 5% chance of complex rendering
                    time.sleep(0.02)  # Expensive rendering
                else:
                    time.sleep(0.002)
        
        frame_count += 1
        
        # Maintain target frame rate
        frame_time = time.time() - frame_start
        target_frame_time = 1.0 / 60.0  # 60 FPS
        if frame_time < target_frame_time:
            time.sleep(target_frame_time - frame_time)
    
    print(f"✅ Simulation complete: {frame_count} frames processed")


def demonstrate_core_profiling():
    """Demonstrate core profiling functionality."""
    print("\n" + "="*60)
    print("🔍 CORE PROFILING DEMONSTRATION")
    print("="*60)
    
    profiler = PerformanceProfiler("demo_profiler")
    
    # Basic profiling
    print("\n1. Basic Profiling:")
    with profiler.profile("basic_operation") as ctx:
        ctx.metadata['operation_type'] = 'demo'
        time.sleep(0.01)
    
    # Decorator profiling
    print("2. Decorator Profiling:")
    @profiler.profile_decorator("decorated_function")
    def slow_function(n):
        total = 0
        for i in range(n):
            total += i * i
        return total
    
    result = slow_function(10000)
    
    # Nested profiling
    print("3. Nested Profiling:")
    with profiler.profile("outer_operation"):
        time.sleep(0.005)
        with profiler.profile("inner_operation_1"):
            time.sleep(0.003)
        with profiler.profile("inner_operation_2"):
            time.sleep(0.002)
    
    # Display results
    results = profiler.get_results()
    print(f"\n📊 Profiling Results ({len(results)} operations):")
    
    for result in results:
        duration_str = format_time(result.duration)
        print(f"  • {result.name}: {duration_str}")
        if result.children:
            for child in result.children:
                child_duration_str = format_time(child.duration)
                print(f"    └─ {child.name}: {child_duration_str}")
    
    stats = profiler.get_stats()
    print(f"\n📈 Statistics:")
    print(f"  • Total operations: {stats['total_profiles']}")
    print(f"  • Average duration: {format_time(stats['average_duration'])}")
    print(f"  • Min duration: {format_time(stats['min_duration'])}")
    print(f"  • Max duration: {format_time(stats['max_duration'])}")


def demonstrate_monitoring():
    """Demonstrate performance monitoring."""
    print("\n" + "="*60)
    print("📊 PERFORMANCE MONITORING DEMONSTRATION")
    print("="*60)
    
    config = MonitorConfig(
        sample_interval=0.5,
        monitor_cpu=True,
        monitor_memory=True,
        target_fps=60.0
    )
    
    # Create monitors
    system_monitor = SystemMonitor(config)
    memory_monitor = MemoryMonitor(config)
    framerate_monitor = FrameRateMonitor(config)
    custom_monitor = CustomMonitor("game_metrics", config)
    
    # Add custom metrics
    game_state = {'entities': 0, 'level': 1}
    custom_monitor.add_metric_callback("entity_count", lambda: game_state['entities'])
    custom_monitor.add_metric_callback("current_level", lambda: game_state['level'])
    
    print("\n🔄 Collecting monitoring data...")
    
    # Simulate monitoring for a short period
    for i in range(10):
        # Update game state
        game_state['entities'] = random.randint(50, 200)
        if i % 3 == 0:
            game_state['level'] += 1
        
        # Record frame
        framerate_monitor.record_frame()
        
        # Sample monitors
        system_result = system_monitor.sample()
        memory_result = memory_monitor.sample()
        framerate_result = framerate_monitor.sample()
        custom_result = custom_monitor.sample()
        
        # Simulate some work
        time.sleep(0.1)
    
    print("\n📋 Monitoring Results:")
    
    # System metrics
    if system_result and system_monitor.system_available:
        print(f"  🖥️  System:")
        if 'cpu_percent' in system_result.metrics:
            print(f"     CPU: {format_percentage(system_result.metrics['cpu_percent'])}")
        if 'process_cpu_percent' in system_result.metrics:
            print(f"     Process CPU: {format_percentage(system_result.metrics['process_cpu_percent'])}")
    
    # Memory metrics
    if memory_result:
        print(f"  💾 Memory:")
        if 'rss' in memory_result.metrics:
            print(f"     RSS: {format_memory(memory_result.metrics['rss'])}")
        if 'system_percent' in memory_result.metrics:
            print(f"     System: {format_percentage(memory_result.metrics['system_percent'])}")
    
    # Frame rate metrics
    if framerate_result:
        print(f"  🎯 Frame Rate:")
        if 'fps' in framerate_result.metrics:
            print(f"     FPS: {framerate_result.metrics['fps']:.1f}")
        if 'frame_time_ms' in framerate_result.metrics:
            print(f"     Frame Time: {framerate_result.metrics['frame_time_ms']:.2f}ms")
    
    # Custom metrics
    if custom_result:
        print(f"  🎮 Game Metrics:")
        print(f"     Entities: {custom_result.metrics.get('entity_count', 'N/A')}")
        print(f"     Level: {custom_result.metrics.get('current_level', 'N/A')}")


def demonstrate_analysis():
    """Demonstrate performance analysis."""
    print("\n" + "="*60)
    print("🔬 PERFORMANCE ANALYSIS DEMONSTRATION")
    print("="*60)
    
    profiler = PerformanceProfiler("analysis_demo")
    
    # Generate test data with performance issues
    print("\n🧪 Generating test data with performance patterns...")
    
    # Simulate operations with different characteristics
    operations = [
        ("fast_operation", 0.001, 0.1),      # Fast, consistent
        ("variable_operation", 0.005, 0.8),  # Variable performance
        ("degrading_operation", 0.002, 0.2), # Gradually degrading
        ("bottleneck_operation", 0.05, 0.1), # Slow bottleneck
    ]
    
    for i in range(50):
        for op_name, base_duration, variability in operations:
            # Simulate performance degradation for degrading_operation
            if op_name == "degrading_operation":
                duration = base_duration + (i * 0.0001)  # Gradual increase
            else:
                duration = base_duration * (1 + random.uniform(-variability, variability))
            
            with profiler.profile(op_name):
                time.sleep(max(0.0001, duration))
    
    # Create analyzers
    statistical_analyzer = StatisticalAnalyzer()
    trend_analyzer = TrendAnalyzer(window_size=10)
    bottleneck_detector = BottleneckDetector()
    
    # Analyze results
    results = profiler.get_results()
    print(f"📊 Analyzing {len(results)} profiling results...")
    
    # Statistical analysis
    statistical_analyses = statistical_analyzer.analyze(results)
    print(f"\n📈 Statistical Analysis ({len(statistical_analyses)} findings):")
    for analysis in statistical_analyses:
        print(f"  • {analysis.title}")
        print(f"    Severity: {analysis.severity.name}")
        if analysis.recommendations:
            print(f"    Recommendation: {analysis.recommendations[0]}")
    
    # Trend analysis
    trend_analyses = trend_analyzer.analyze(results)
    print(f"\n📉 Trend Analysis ({len(trend_analyses)} findings):")
    for analysis in trend_analyses:
        print(f"  • {analysis.title}")
        print(f"    Severity: {analysis.severity.name}")
        if 'trend_slope' in analysis.metrics:
            slope = analysis.metrics['trend_slope']
            direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
            print(f"    Trend: {direction} (slope: {slope:.6f})")
    
    # Bottleneck detection
    bottleneck_analyses = bottleneck_detector.analyze(results)
    print(f"\n🚨 Bottleneck Analysis ({len(bottleneck_analyses)} findings):")
    for analysis in bottleneck_analyses:
        print(f"  • {analysis.title}")
        print(f"    Severity: {analysis.severity.name}")
        if 'percentage' in analysis.metrics:
            print(f"    Time consumption: {analysis.metrics['percentage']:.1f}%")


def demonstrate_alerts():
    """Demonstrate performance alerting."""
    print("\n" + "="*60)
    print("🚨 PERFORMANCE ALERTING DEMONSTRATION")
    print("="*60)
    
    alert_manager = AlertManager()
    
    # Create alert rules
    rules = [
        create_threshold_rule(
            "high_cpu", "High CPU Usage", "cpu_percent", 80.0,
            severity=AlertSeverity.WARNING
        ),
        create_threshold_rule(
            "critical_cpu", "Critical CPU Usage", "cpu_percent", 95.0,
            severity=AlertSeverity.CRITICAL
        ),
        create_threshold_rule(
            "high_memory", "High Memory Usage", "memory_mb", 500.0,
            severity=AlertSeverity.WARNING
        ),
        create_threshold_rule(
            "low_fps", "Low Frame Rate", "fps", 30.0, "less_than",
            severity=AlertSeverity.WARNING
        ),
    ]
    
    for rule in rules:
        alert_manager.add_rule(rule)
    
    print(f"📋 Created {len(rules)} alert rules")
    
    # Simulate metrics that trigger alerts
    test_scenarios = [
        {"name": "Normal Operation", "cpu_percent": 45.0, "memory_mb": 200.0, "fps": 58.0},
        {"name": "High CPU", "cpu_percent": 85.0, "memory_mb": 250.0, "fps": 55.0},
        {"name": "Critical CPU", "cpu_percent": 98.0, "memory_mb": 300.0, "fps": 45.0},
        {"name": "High Memory", "cpu_percent": 60.0, "memory_mb": 600.0, "fps": 50.0},
        {"name": "Low FPS", "cpu_percent": 70.0, "memory_mb": 400.0, "fps": 25.0},
        {"name": "Multiple Issues", "cpu_percent": 90.0, "memory_mb": 700.0, "fps": 20.0},
    ]
    
    print("\n🧪 Testing alert scenarios:")
    
    for scenario in test_scenarios:
        print(f"\n  📊 Scenario: {scenario['name']}")
        metrics = {k: v for k, v in scenario.items() if k != 'name'}
        
        alerts = alert_manager.check_alerts(metrics)
        
        if alerts:
            print(f"    🚨 {len(alerts)} alert(s) triggered:")
            for alert in alerts:
                print(f"      • [{alert.severity.name}] {alert.title}")
        else:
            print("    ✅ No alerts triggered")
        
        time.sleep(0.1)  # Small delay between scenarios
    
    # Show alert statistics
    stats = alert_manager.get_stats()
    print(f"\n📈 Alert Statistics:")
    print(f"  • Total alerts: {stats['total_alerts']}")
    print(f"  • Active alerts: {stats['active_alerts']}")
    print(f"  • Rules: {stats['rules_count']} ({stats['enabled_rules']} enabled)")
    
    # Show active alerts
    active_alerts = alert_manager.get_active_alerts()
    if active_alerts:
        print(f"\n🔔 Active Alerts ({len(active_alerts)}):")
        for alert in active_alerts[:5]:  # Show first 5
            age = format_time(alert.get_age())
            print(f"  • [{alert.severity.name}] {alert.title} (age: {age})")


def demonstrate_integration():
    """Demonstrate game engine integration."""
    print("\n" + "="*60)
    print("🎮 GAME ENGINE INTEGRATION DEMONSTRATION")
    print("="*60)
    
    # Initialize event bus
    initialize_event_bus()
    
    # Create profiling configuration
    config = ProfilingConfig(
        enable_profiling=True,
        enable_monitoring=True,
        enable_analysis=True,
        profile_systems=True,
        profile_events=True,
        analysis_interval=5.0,
        async_analysis=False  # Synchronous for demo
    )
    
    # Create game engine
    engine = GameEngine(target_fps=60)
    
    # Add demo systems
    systems = [
        DemoSystem("input_system", 0.001, 0.2),
        DemoSystem("ai_system", 0.005, 0.5),
        DemoSystem("physics_system", 0.003, 0.3),
        DemoSystem("render_system", 0.008, 0.4),
    ]
    
    for system in systems:
        engine.register_system(system)
    
    print(f"🏗️  Created game engine with {len(systems)} systems")
    
    # Create and integrate profiler
    game_profiler = GameEngineProfiler(config)
    game_profiler.integrate_with_engine(engine)
    
    print("🔗 Integrated performance profiling with game engine")
    
    # Simulate some game events
    event_bus = game_profiler.event_profiler.event_bus if game_profiler.event_profiler else None
    if event_bus:
        print("📡 Dispatching game events...")
        for i in range(20):
            event_type = random.choice(["player.move", "enemy.spawn", "item.pickup", "level.complete"])
            event = SimpleEvent(event_type, {"frame": i})
            event_bus.dispatch(event)
    
    # Run engine for a short time
    print("⚙️  Running game engine simulation...")
    
    engine.start()
    start_time = time.time()
    
    while time.time() - start_time < 3.0:  # Run for 3 seconds
        engine.update()
        time.sleep(1.0 / 60.0)  # 60 FPS
    
    engine.stop()
    
    # Get comprehensive metrics
    metrics = game_profiler.get_comprehensive_metrics()
    
    print("\n📊 Integration Results:")
    print(f"  🔍 Profiler: {metrics['profiler_stats']['total_profiles']} operations profiled")
    
    if metrics['system_metrics']:
        print(f"  ⚙️  Systems: {len(metrics['system_metrics'])} systems monitored")
        for system_name, system_metrics in metrics['system_metrics'].items():
            if 'avg_update_time' in system_metrics:
                avg_time = format_time(system_metrics['avg_update_time'])
                print(f"     • {system_name}: {avg_time} avg")
    
    if metrics['event_metrics']:
        event_metrics = metrics['event_metrics']
        print(f"  📡 Events: {event_metrics.get('total_events', 0)} events processed")
    
    # Cleanup
    game_profiler.shutdown()


def demonstrate_dashboard():
    """Demonstrate performance dashboard."""
    print("\n" + "="*60)
    print("📺 PERFORMANCE DASHBOARD DEMONSTRATION")
    print("="*60)
    
    # Create dashboard configuration
    dashboard_config = DashboardConfig(
        refresh_interval=1.0,
        show_alerts=True,
        show_trends=True,
        use_colors=False  # Disable colors for demo
    )
    
    # Create alert manager with some rules
    alert_manager = AlertManager()
    alert_manager.add_rule(create_threshold_rule(
        "demo_cpu", "Demo High CPU", "cpu_percent", 75.0
    ))
    
    # Create metrics callback
    demo_metrics = {
        'cpu_percent': 45.0,
        'memory_mb': 200.0,
        'fps': 58.0,
        'events_per_sec': 15.0
    }
    
    def get_demo_metrics():
        # Simulate changing metrics
        demo_metrics['cpu_percent'] += random.uniform(-5, 5)
        demo_metrics['cpu_percent'] = max(0, min(100, demo_metrics['cpu_percent']))
        
        demo_metrics['memory_mb'] += random.uniform(-10, 10)
        demo_metrics['memory_mb'] = max(50, demo_metrics['memory_mb'])
        
        demo_metrics['fps'] += random.uniform(-2, 2)
        demo_metrics['fps'] = max(20, min(60, demo_metrics['fps']))
        
        demo_metrics['events_per_sec'] += random.uniform(-3, 3)
        demo_metrics['events_per_sec'] = max(0, demo_metrics['events_per_sec'])
        
        # Check for alerts
        alert_manager.check_alerts(demo_metrics)
        
        return {
            'monitor_metrics': {
                'system': {'cpu_percent': demo_metrics['cpu_percent']},
                'memory': {'rss': demo_metrics['memory_mb'] * 1024 * 1024},
                'framerate': {'fps': demo_metrics['fps']},
            },
            'event_metrics': {
                'recent_events_per_second': demo_metrics['events_per_sec']
            }
        }
    
    # Create dashboard
    dashboard = create_dashboard(
        alert_manager=alert_manager,
        metrics_callback=get_demo_metrics,
        config=dashboard_config
    )
    
    print("📺 Dashboard created - showing 5 snapshots:")
    
    # Show several dashboard snapshots
    for i in range(5):
        print(f"\n📸 Snapshot {i + 1}:")
        print("-" * 40)
        dashboard.print_once()
        time.sleep(1.0)


def main():
    """Main demonstration function."""
    print("🚀 COMPREHENSIVE PERFORMANCE PROFILING SYSTEM DEMONSTRATION")
    print("=" * 80)
    print("This demo showcases all major components of the performance profiling system:")
    print("• Core Profiling - High-precision timing and measurement")
    print("• Performance Monitoring - Real-time system metrics")
    print("• Performance Analysis - Statistical analysis and bottleneck detection")
    print("• Alert System - Automated performance issue detection")
    print("• Game Engine Integration - Seamless integration with existing systems")
    print("• Performance Dashboard - Real-time visualization")
    
    try:
        # Run demonstrations
        demonstrate_core_profiling()
        demonstrate_monitoring()
        demonstrate_analysis()
        demonstrate_alerts()
        demonstrate_integration()
        demonstrate_dashboard()
        
        print("\n" + "="*80)
        print("✅ DEMONSTRATION COMPLETE")
        print("="*80)
        print("The performance profiling system is ready for production use!")
        print("\nKey Benefits:")
        print("• 🎯 Precise performance measurement with sub-millisecond accuracy")
        print("• 📊 Comprehensive monitoring of system resources and game metrics")
        print("• 🔬 Advanced analysis for bottleneck detection and trend analysis")
        print("• 🚨 Proactive alerting for performance issues")
        print("• 🎮 Seamless integration with existing game engine architecture")
        print("• 📺 Real-time dashboard for performance visualization")
        print("\nNext Steps:")
        print("• Integrate with your game engine using GameEngineProfiler")
        print("• Configure monitoring and alerting rules for your specific needs")
        print("• Use the dashboard for real-time performance monitoring")
        print("• Analyze profiling data to optimize critical code paths")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demonstration interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
