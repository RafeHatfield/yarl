from io_layer.bot_metrics import (
    BotDecisionTelemetry,
    BotMetricsRecorder,
)


def test_bot_metrics_recorder_summarizes_counts():
    recorder = BotMetricsRecorder(enabled=True, run_id="run-1")

    recorder.record_decision(
        BotDecisionTelemetry(
            run_id="run-1",
            floor=1,
            turn_number=1,
            action_type="move",
            reason="explore",
            in_explore=True,
            visible_enemies=0,
        )
    )
    recorder.record_decision(
        BotDecisionTelemetry(
            run_id="run-1",
            floor=1,
            turn_number=2,
            action_type="attack",
            reason="combat_engage",
            in_combat=True,
            visible_enemies=1,
        )
    )
    recorder.record_decision(
        BotDecisionTelemetry(
            run_id="run-1",
            floor=2,
            turn_number=3,
            action_type="drink_potion",
            reason="heal_low_hp",
            low_hp=True,
        )
    )

    summary = recorder.summarize()
    summary_dict = summary.to_dict()

    assert summary.total_steps == 3
    assert summary.floors_seen == 2
    assert summary.action_counts["move"] == 1
    assert summary.action_counts["attack"] == 1
    assert summary.action_counts["drink_potion"] == 1
    assert summary.context_counts["in_combat"] == 1
    assert summary.context_counts["in_explore"] == 1
    assert summary.context_counts["low_hp"] == 1
    assert summary.reason_counts["heal_low_hp"] == 1
    assert summary_dict["run_id"] == "run-1"
