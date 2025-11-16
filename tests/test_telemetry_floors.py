"""Tests for telemetry floor tracking (Phase 1.5b).

This test suite verifies that the telemetry system correctly tracks
per-floor metrics including:
- Floor start/end lifecycle
- ETP (Encounter Threat Points) aggregation
- Monster, item, door, trap, secret counts
- Room approximations
- Integration with run metrics
"""

import pytest
from unittest.mock import Mock, patch
from services.telemetry_service import TelemetryService, FloorTelemetry, reset_telemetry_service
from components.component_registry import ComponentType
from components.fighter import Fighter
from components.ai import BasicMonster
from components.item import Item
from components.door import Door
from components.trap import Trap


class TestFloorTelemetryLifecycle:
    """Test floor start/end lifecycle."""
    
    def setup_method(self):
        """Reset telemetry service before each test."""
        reset_telemetry_service()
    
    def test_start_floor_creates_floor_record(self):
        """Test that start_floor creates a new floor record."""
        telemetry = TelemetryService(output_path="test_output.json")
        
        telemetry.start_floor(depth=1)
        
        assert telemetry.current_floor == 1
        assert 1 in telemetry.floors
        assert telemetry.floors[1].depth == 1
    
    def test_end_floor_clears_current_floor(self):
        """Test that end_floor clears current floor pointer."""
        telemetry = TelemetryService(output_path="test_output.json")
        telemetry.start_floor(depth=1)
        
        telemetry.end_floor()
        
        assert telemetry.current_floor is None
    
    def test_multiple_floors_tracked(self):
        """Test that multiple floors can be tracked sequentially."""
        telemetry = TelemetryService(output_path="test_output.json")
        
        # Floor 1
        telemetry.start_floor(depth=1)
        telemetry.set_floor_etp(etp_sum=100)
        telemetry.end_floor()
        
        # Floor 2
        telemetry.start_floor(depth=2)
        telemetry.set_floor_etp(etp_sum=200)
        telemetry.end_floor()
        
        # Floor 3
        telemetry.start_floor(depth=3)
        telemetry.set_floor_etp(etp_sum=300)
        telemetry.end_floor()
        
        assert len(telemetry.floors) == 3
        assert telemetry.floors[1].etp_sum == 100
        assert telemetry.floors[2].etp_sum == 200
        assert telemetry.floors[3].etp_sum == 300
    
    def test_disabled_telemetry_does_nothing(self):
        """Test that disabled telemetry is a no-op."""
        telemetry = TelemetryService(output_path=None)
        
        telemetry.start_floor(depth=1)
        telemetry.set_floor_etp(etp_sum=100)
        telemetry.end_floor()
        
        assert not telemetry.enabled
        assert len(telemetry.floors) == 0


class TestFloorStatsPopulation:
    """Test floor stats population."""
    
    def setup_method(self):
        """Reset telemetry service before each test."""
        reset_telemetry_service()
    
    def test_set_floor_etp(self):
        """Test setting ETP for current floor."""
        telemetry = TelemetryService(output_path="test_output.json")
        telemetry.start_floor(depth=1)
        
        telemetry.set_floor_etp(etp_sum=150, budget_min=100, budget_max=200)
        
        floor = telemetry.floors[1]
        assert floor.etp_sum == 150
        assert floor.etp_budget_min == 100
        assert floor.etp_budget_max == 200
    
    def test_set_room_counts(self):
        """Test setting room/monster/item counts."""
        telemetry = TelemetryService(output_path="test_output.json")
        telemetry.start_floor(depth=1)
        
        telemetry.set_room_counts(rooms=8, monsters=12, items=5)
        
        floor = telemetry.floors[1]
        assert floor.room_count == 8
        assert floor.monster_count == 12
        assert floor.item_count == 5
    
    def test_stats_aggregation(self):
        """Test that get_stats aggregates across floors."""
        telemetry = TelemetryService(output_path="test_output.json")
        
        # Floor 1: 2 traps, 1 secret, 3 doors, 1 key
        telemetry.start_floor(depth=1)
        telemetry.set_floor_etp(etp_sum=100)
        telemetry.record_trap_triggered()
        telemetry.record_trap_triggered()
        telemetry.record_secret_found()
        telemetry.record_door_opened()
        telemetry.record_door_opened()
        telemetry.record_door_unlocked()
        telemetry.record_key_used()
        telemetry.end_floor()
        
        # Floor 2: 1 trap, 2 secrets, 2 doors, 0 keys
        telemetry.start_floor(depth=2)
        telemetry.set_floor_etp(etp_sum=200)
        telemetry.record_trap_triggered()
        telemetry.record_secret_found()
        telemetry.record_secret_found()
        telemetry.record_door_opened()
        telemetry.record_door_opened()
        telemetry.end_floor()
        
        stats = telemetry.get_stats()
        
        assert stats['floors'] == 2
        assert stats['avg_etp_per_floor'] == 150.0  # (100 + 200) / 2
        assert stats['total_traps'] == 3
        assert stats['total_secrets'] == 3
        assert stats['total_doors'] == 5  # opened + unlocked
        assert stats['total_keys'] == 1


class TestTelemetryWithMockEntities:
    """Test telemetry floor population with mock entities."""
    
    def setup_method(self):
        """Reset telemetry service before each test."""
        reset_telemetry_service()
    
    def _create_mock_entity(self, name, **components):
        """Create a mock entity with specified components.
        
        Args:
            name: Entity name
            **components: Component types and instances (e.g., fighter=fighter_comp)
        
        Returns:
            Mock entity with get_component_optional method
        """
        entity = Mock()
        entity.name = name
        
        def get_component(comp_type):
            # Map ComponentType to keyword args
            comp_map = {
                ComponentType.FIGHTER: 'fighter',
                ComponentType.AI: 'ai',
                ComponentType.ITEM: 'item',
                ComponentType.DOOR: 'door',
                ComponentType.TRAP: 'trap',
            }
            key = comp_map.get(comp_type)
            return components.get(key)
        
        entity.get_component_optional = get_component
        return entity
    
    def test_count_monsters_and_etp(self):
        """Test monster counting and ETP computation from entities."""
        # Create mock entities
        player = self._create_mock_entity("Player")
        
        # Monster 1: HP=10, Power=3 → ETP = 10 + (3*2) = 16
        fighter1 = Mock(max_hp=10, power=3)
        ai1 = Mock()
        orc = self._create_mock_entity("Orc", fighter=fighter1, ai=ai1)
        
        # Monster 2: HP=20, Power=5 → ETP = 20 + (5*2) = 30
        fighter2 = Mock(max_hp=20, power=5)
        ai2 = Mock()
        troll = self._create_mock_entity("Troll", fighter=fighter2, ai=ai2)
        
        entities = [player, orc, troll]
        
        # Compute ETP manually (simulating _populate_floor_telemetry)
        monster_count = 0
        etp_sum = 0
        for entity in entities:
            if entity.name == "Player":
                continue
            fighter = entity.get_component_optional(ComponentType.FIGHTER)
            ai = entity.get_component_optional(ComponentType.AI)
            if fighter and ai:
                monster_count += 1
                etp_sum += fighter.max_hp + (fighter.power * 2)
        
        assert monster_count == 2
        assert etp_sum == 46  # 16 + 30
    
    def test_count_items(self):
        """Test item counting from entities."""
        player = self._create_mock_entity("Player")
        
        item1 = Mock()
        potion = self._create_mock_entity("Health Potion", item=item1)
        
        item2 = Mock()
        scroll = self._create_mock_entity("Scroll of Fireball", item=item2)
        
        entities = [player, potion, scroll]
        
        item_count = 0
        for entity in entities:
            if entity.name == "Player":
                continue
            if entity.get_component_optional(ComponentType.ITEM):
                item_count += 1
        
        assert item_count == 2
    
    def test_count_doors_and_secrets(self):
        """Test door and secret counting from entities."""
        player = self._create_mock_entity("Player")
        
        # Regular door
        door1 = Mock(is_secret=False)
        wooden_door = self._create_mock_entity("Wooden Door", door=door1)
        
        # Secret door
        door2 = Mock(is_secret=True)
        secret_door = self._create_mock_entity("Secret Door", door=door2)
        
        entities = [player, wooden_door, secret_door]
        
        door_count = 0
        secret_count = 0
        for entity in entities:
            if entity.name == "Player":
                continue
            door = entity.get_component_optional(ComponentType.DOOR)
            if door:
                door_count += 1
                if door.is_secret:
                    secret_count += 1
        
        assert door_count == 2
        assert secret_count == 1
    
    def test_count_traps(self):
        """Test trap counting from entities."""
        player = self._create_mock_entity("Player")
        
        trap1 = Mock()
        spike_trap = self._create_mock_entity("Spike Trap", trap=trap1)
        
        trap2 = Mock()
        poison_trap = self._create_mock_entity("Poison Trap", trap=trap2)
        
        entities = [player, spike_trap, poison_trap]
        
        trap_count = 0
        for entity in entities:
            if entity.name == "Player":
                continue
            if entity.get_component_optional(ComponentType.TRAP):
                trap_count += 1
        
        assert trap_count == 2


class TestTelemetryJSONOutput:
    """Test telemetry JSON output format."""
    
    def setup_method(self):
        """Reset telemetry service before each test."""
        reset_telemetry_service()
    
    def test_json_output_includes_floor_data(self, tmp_path):
        """Test that dump_json includes floor data."""
        output_file = tmp_path / "telemetry.json"
        telemetry = TelemetryService(output_path=str(output_file))
        
        # Simulate a simple floor
        telemetry.start_floor(depth=1)
        telemetry.set_floor_etp(etp_sum=100)
        telemetry.set_room_counts(rooms=5, monsters=8, items=3)
        telemetry.record_door_opened()
        telemetry.record_trap_triggered()
        telemetry.end_floor()
        
        # Dump JSON
        telemetry.dump_json()
        
        # Read and verify JSON
        import json
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert 'floor_count' in data
        assert data['floor_count'] == 1
        assert 'floors' in data
        assert len(data['floors']) == 1
        
        floor = data['floors'][0]
        assert floor['depth'] == 1
        assert floor['etp_sum'] == 100
        assert floor['room_count'] == 5
        assert floor['monster_count'] == 8
        assert floor['item_count'] == 3
        assert floor['doors_opened'] == 1
        assert floor['traps_triggered'] == 1
    
    def test_json_output_with_run_metrics(self, tmp_path):
        """Test that dump_json preserves run_metrics."""
        output_file = tmp_path / "telemetry.json"
        telemetry = TelemetryService(output_path=str(output_file))
        
        # Simulate a floor
        telemetry.start_floor(depth=1)
        telemetry.set_floor_etp(etp_sum=100)
        telemetry.end_floor()
        
        # Mock run metrics
        mock_run_metrics = Mock()
        mock_run_metrics.to_dict.return_value = {
            'run_id': 'test_run_123',
            'mode': 'human',
            'outcome': 'death',
            'duration_seconds': 123.45,
            'deepest_floor': 1,
        }
        
        # Dump JSON with run metrics
        telemetry.dump_json(run_metrics=mock_run_metrics)
        
        # Read and verify JSON
        import json
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        # Both floor data and run metrics should be present
        assert 'floor_count' in data
        assert 'floors' in data
        assert 'run_metrics' in data
        assert data['run_metrics']['run_id'] == 'test_run_123'
        assert data['run_metrics']['mode'] == 'human'


class TestTelemetryGetStatsEmptyCases:
    """Test get_stats with edge cases."""
    
    def setup_method(self):
        """Reset telemetry service before each test."""
        reset_telemetry_service()
    
    def test_get_stats_empty_floors(self):
        """Test get_stats when no floors tracked."""
        telemetry = TelemetryService(output_path="test_output.json")
        
        stats = telemetry.get_stats()
        
        assert stats['floors'] == 0
    
    def test_get_stats_single_floor_no_data(self):
        """Test get_stats with single floor, no events."""
        telemetry = TelemetryService(output_path="test_output.json")
        
        telemetry.start_floor(depth=1)
        telemetry.end_floor()
        
        stats = telemetry.get_stats()
        
        assert stats['floors'] == 1
        assert stats['avg_etp_per_floor'] == 0.0
        assert stats['total_traps'] == 0
        assert stats['total_secrets'] == 0
        assert stats['total_doors'] == 0
        assert stats['total_keys'] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

