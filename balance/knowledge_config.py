"""Monster Knowledge System Configuration.

Phase 11: Tunable thresholds for knowledge tier progression.
These values control how much interaction is required to unlock
different levels of monster information.

Tier System:
    Tier 0 - Unknown: Never seen this monster type
    Tier 1 - Observed: Seen at least once
    Tier 2 - Battled: Engaged in combat multiple times
    Tier 3 - Understood: Killed several, or experienced special traits
"""

# ═══════════════════════════════════════════════════════════════════════════════
# TIER THRESHOLDS
# ═══════════════════════════════════════════════════════════════════════════════

# Tier 1 - Observed: Just need to see them once
TIER_1_SEEN_COUNT = 1

# Tier 2 - Battled: Requires combat experience
TIER_2_ENGAGED_COUNT = 3
TIER_2_HITS_TAKEN = 3  # Alternative: if monster has hit player this many times

# Tier 3 - Understood: Deep knowledge from extensive experience
TIER_3_KILLED_COUNT = 5
TIER_3_TRAIT_EXPERIENCE_UNLOCKS = True  # If True, experiencing a major trait unlocks Tier 3


# ═══════════════════════════════════════════════════════════════════════════════
# STAT LABEL THRESHOLDS
# ═══════════════════════════════════════════════════════════════════════════════

# Durability labels (based on max_hp + defense/armor)
# Effective durability = max_hp + (defense * 5)
DURABILITY_FRAGILE_MAX = 20
DURABILITY_STURDY_MAX = 40
DURABILITY_TOUGH_MAX = 70
# Above TOUGH_MAX = "monstrous"

# Damage labels (based on average damage per hit)
# Average damage = (damage_min + damage_max) / 2 + power
DAMAGE_LIGHT_MAX = 4
DAMAGE_MODERATE_MAX = 8
DAMAGE_HEAVY_MAX = 14
# Above HEAVY_MAX = "brutal"

# Speed labels (based on speed_bonus ratio)
SPEED_SLUGGISH_MAX = 0.6
SPEED_NORMAL_MAX = 1.2
SPEED_FAST_MAX = 1.8
# Above FAST_MAX = "lightning fast"

# Accuracy labels
ACCURACY_OFTEN_MISSES_MAX = 1
ACCURACY_USUALLY_HITS_MAX = 3
# Above USUALLY_HITS_MAX = "rarely misses"

# Evasion labels
EVASION_EASY_TO_HIT_MAX = 1
EVASION_AVERAGE_MAX = 2
# Above AVERAGE_MAX = "hard to hit"


# ═══════════════════════════════════════════════════════════════════════════════
# TRAIT NAMES (for trait_discovered matching)
# ═══════════════════════════════════════════════════════════════════════════════

# These trait names must match what is passed to register_trait()
TRAIT_PLAGUE_CARRIER = "plague_carrier"
TRAIT_SWARM_AI = "swarm_ai"
TRAIT_PORTAL_CURIOUS = "portal_curious"
TRAIT_FAST_ATTACKER = "fast_attacker"


# ═══════════════════════════════════════════════════════════════════════════════
# MAJOR TRAITS (unlock Tier 3 when experienced)
# ═══════════════════════════════════════════════════════════════════════════════

# Traits that, when experienced personally, unlock Tier 3 understanding
MAJOR_TRAITS = {
    TRAIT_PLAGUE_CARRIER,
    TRAIT_SWARM_AI,
}
