"""Tests for the spell registry system."""

import pytest
from spells.spell_definition import SpellDefinition
from spells.spell_registry import SpellRegistry, get_spell_registry
from spells.spell_types import SpellCategory, TargetingType, DamageType


class TestSpellRegistry:
    """Tests for SpellRegistry class."""
    
    def setup_method(self):
        """Set up test registry before each test."""
        self.registry = SpellRegistry()
        
        # Create test spells
        self.fireball = SpellDefinition(
            spell_id="fireball",
            name="Fireball",
            category=SpellCategory.OFFENSIVE,
            targeting=TargetingType.AOE,
            damage="3d6",
            damage_type=DamageType.FIRE,
            radius=3,
            cast_message="The fireball explodes!"
        )
        
        self.heal = SpellDefinition(
            spell_id="heal",
            name="Heal",
            category=SpellCategory.HEALING,
            targeting=TargetingType.SELF,
            heal_amount=20
        )
    
    def test_register_spell(self):
        """Test registering a spell."""
        self.registry.register(self.fireball)
        
        assert self.registry.has("fireball")
        assert len(self.registry) == 1
    
    def test_register_duplicate_raises_error(self):
        """Test that registering duplicate spell_id raises error."""
        self.registry.register(self.fireball)
        
        with pytest.raises(ValueError, match="already registered"):
            self.registry.register(self.fireball)
    
    def test_get_spell(self):
        """Test retrieving a spell."""
        self.registry.register(self.fireball)
        
        spell = self.registry.get("fireball")
        assert spell is not None
        assert spell.spell_id == "fireball"
        assert spell.name == "Fireball"
        assert spell.damage == "3d6"
    
    def test_get_nonexistent_spell(self):
        """Test getting a spell that doesn't exist."""
        spell = self.registry.get("nonexistent")
        assert spell is None
    
    def test_has_spell(self):
        """Test checking if spell exists."""
        assert not self.registry.has("fireball")
        
        self.registry.register(self.fireball)
        assert self.registry.has("fireball")
    
    def test_contains_operator(self):
        """Test 'in' operator for spell registry."""
        assert "fireball" not in self.registry
        
        self.registry.register(self.fireball)
        assert "fireball" in self.registry
    
    def test_list_all(self):
        """Test listing all spells."""
        self.registry.register(self.fireball)
        self.registry.register(self.heal)
        
        all_spells = self.registry.list_all()
        assert len(all_spells) == 2
        spell_ids = {s.spell_id for s in all_spells}
        assert spell_ids == {"fireball", "heal"}
    
    def test_list_by_category(self):
        """Test filtering spells by category."""
        self.registry.register(self.fireball)
        self.registry.register(self.heal)
        
        offensive = self.registry.list_by_category(SpellCategory.OFFENSIVE)
        assert len(offensive) == 1
        assert offensive[0].spell_id == "fireball"
        
        healing = self.registry.list_by_category(SpellCategory.HEALING)
        assert len(healing) == 1
        assert healing[0].spell_id == "heal"
    
    def test_clear(self):
        """Test clearing all spells."""
        self.registry.register(self.fireball)
        self.registry.register(self.heal)
        assert len(self.registry) == 2
        
        self.registry.clear()
        assert len(self.registry) == 0
        assert not self.registry.has("fireball")
    
    def test_len(self):
        """Test __len__ method."""
        assert len(self.registry) == 0
        
        self.registry.register(self.fireball)
        assert len(self.registry) == 1
        
        self.registry.register(self.heal)
        assert len(self.registry) == 2
    
    def test_repr(self):
        """Test __repr__ method."""
        repr_str = repr(self.registry)
        assert "SpellRegistry" in repr_str
        assert "0 spells" in repr_str
        
        self.registry.register(self.fireball)
        repr_str = repr(self.registry)
        assert "1 spells" in repr_str


class TestSpellDefinition:
    """Tests for SpellDefinition dataclass."""
    
    def test_minimal_definition(self):
        """Test creating a minimal spell definition."""
        spell = SpellDefinition(
            spell_id="test",
            name="Test Spell",
            category=SpellCategory.UTILITY,
            targeting=TargetingType.SELF
        )
        
        assert spell.spell_id == "test"
        assert spell.name == "Test Spell"
        assert spell.damage is None
        assert spell.radius == 0
        assert spell.consumable is True
    
    def test_full_definition(self):
        """Test creating a complete spell definition."""
        spell = SpellDefinition(
            spell_id="dragon_fart",
            name="Dragon Fart",
            category=SpellCategory.OFFENSIVE,
            targeting=TargetingType.CONE,
            damage="2d8",
            damage_type=DamageType.POISON,
            cone_range=8,
            cone_width=45,
            creates_hazard=True,
            hazard_type="poison",
            hazard_duration=5,
            hazard_damage=3,
            cast_message="The dragon unleashes a noxious cloud!",
            success_message="Enemies choke on toxic fumes!",
            max_range=8
        )
        
        assert spell.damage == "2d8"
        assert spell.creates_hazard is True
        assert spell.hazard_type == "poison"
    
    def test_validation_empty_spell_id(self):
        """Test that empty spell_id raises error."""
        with pytest.raises(ValueError, match="spell_id cannot be empty"):
            SpellDefinition(
                spell_id="",
                name="Test",
                category=SpellCategory.UTILITY,
                targeting=TargetingType.SELF
            )
    
    def test_validation_empty_name(self):
        """Test that empty name raises error."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            SpellDefinition(
                spell_id="test",
                name="",
                category=SpellCategory.UTILITY,
                targeting=TargetingType.SELF
            )
    
    def test_validation_negative_radius(self):
        """Test that negative radius raises error."""
        with pytest.raises(ValueError, match="radius cannot be negative"):
            SpellDefinition(
                spell_id="test",
                name="Test",
                category=SpellCategory.UTILITY,
                targeting=TargetingType.SELF,
                radius=-1
            )
    
    def test_validation_negative_range(self):
        """Test that negative max_range raises error."""
        with pytest.raises(ValueError, match="max_range cannot be negative"):
            SpellDefinition(
                spell_id="test",
                name="Test",
                category=SpellCategory.UTILITY,
                targeting=TargetingType.SELF,
                max_range=-1
            )


class TestGlobalRegistry:
    """Tests for global spell registry functions."""
    
    def test_get_spell_registry_singleton(self):
        """Test that get_spell_registry returns same instance."""
        from spells.spell_registry import get_spell_registry
        
        registry1 = get_spell_registry()
        registry2 = get_spell_registry()
        
        assert registry1 is registry2
    
    def test_convenience_functions(self):
        """Test register_spell and get_spell convenience functions."""
        from spells.spell_registry import register_spell, get_spell
        
        # Clear registry first
        get_spell_registry().clear()
        
        spell = SpellDefinition(
            spell_id="test_conv",
            name="Test",
            category=SpellCategory.UTILITY,
            targeting=TargetingType.SELF
        )
        
        register_spell(spell)
        retrieved = get_spell("test_conv")
        
        assert retrieved is not None
        assert retrieved.spell_id == "test_conv"

