"""Pure weapon generation rules for Swordfish.

This module deliberately avoids Panda3D imports so it can be tested quickly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Iterable, Optional, Set, Tuple


@dataclass(frozen=True)
class Enchantment:
    key: str
    display_name: str
    description: str


@dataclass
class Weapon:
    name: str
    rarity: str
    base_damage: int
    enchantments: Tuple[Enchantment, ...]
    weapon_type: str = "saber"
    discovered: Set[str] = field(default_factory=set)

    def known_trait_names(self) -> Tuple[str, ...]:
        return tuple(
            enchantment.display_name
            for enchantment in self.enchantments
            if enchantment.key in self.discovered
        )

    def hidden_trait_count(self) -> int:
        return sum(
            1 for enchantment in self.enchantments if enchantment.key not in self.discovered
        )


@dataclass(frozen=True)
class FishingRodTier:
    tier: int
    name: str
    price: int
    rarity_weights: Tuple[int, int, int, int]


ENCHANTMENTS: Tuple[Enchantment, ...] = (
    Enchantment(
        key="flame",
        display_name="Cinderwake",
        description="Adds fire damage when the weapon lands a hit.",
    ),
    Enchantment(
        key="frost",
        display_name="Stillwinter",
        description="Chills enemies and adds a small amount of frost damage.",
    ),
    Enchantment(
        key="shock",
        display_name="Stormspine",
        description="Sometimes releases a burst of lightning.",
    ),
    Enchantment(
        key="leech",
        display_name="Leech-Rune",
        description="Heals the wielder after a successful strike.",
    ),
    Enchantment(
        key="curse",
        display_name="Blood Debt",
        description="Deals extra damage, but bites back at the wielder.",
    ),
    Enchantment(
        key="rabbit_bane",
        display_name="Hare-Husher",
        description="Hits rabbits much harder than anything else.",
    ),
    Enchantment(
        key="monster_bane",
        display_name="Beast-Oath",
        description="Hits monsters much harder than small creatures.",
    ),
)

ENCHANTMENT_BY_KEY = {enchantment.key: enchantment for enchantment in ENCHANTMENTS}

RARITY_TABLE = (
    ("weathered", 55, 1, (4, 6)),
    ("strange", 28, 1, (6, 8)),
    ("relic", 14, 2, (7, 10)),
    ("mythic", 3, 3, (9, 12)),
)
RARITY_ORDER = tuple(row[0] for row in RARITY_TABLE)
RARITY_DETAIL_BY_NAME = {
    rarity: (enchantment_count, damage_range)
    for rarity, _weight, enchantment_count, damage_range in RARITY_TABLE
}

@dataclass(frozen=True)
class ArmorTier:
    name: str
    cost: int
    armor_value: int


ARMOR_TIERS: Tuple[ArmorTier, ...] = (
    ArmorTier(name="Leather Vest", cost=15, armor_value=1),
    ArmorTier(name="Chain Shirt", cost=40, armor_value=2),
    ArmorTier(name="Iron Plate", cost=80, armor_value=4),
    ArmorTier(name="Dragon Scale", cost=150, armor_value=6),
)


def armor_tier_for_index(idx: int) -> ArmorTier:
    """Return an armor tier by index, clamped to valid range."""
    clamped = max(0, min(idx, len(ARMOR_TIERS) - 1))
    return ARMOR_TIERS[clamped]


FISHING_RODS: Tuple[FishingRodTier, ...] = (
    FishingRodTier(
        tier=0,
        name="Splintered Dock Rod",
        price=0,
        rarity_weights=(70, 30, 0, 0),
    ),
    FishingRodTier(
        tier=1,
        name="Copper Hook Rod",
        price=20,
        rarity_weights=(45, 35, 20, 0),
    ),
    FishingRodTier(
        tier=2,
        name="Moon-Reed Rod",
        price=50,
        rarity_weights=(25, 35, 32, 8),
    ),
    FishingRodTier(
        tier=3,
        name="Starbone Rod",
        price=100,
        rarity_weights=(12, 25, 40, 23),
    ),
)

NAME_PREFIXES = (
    "Rust-Crowned",
    "Moon-Drowned",
    "Silt-Bound",
    "Lanternless",
    "Gravewater",
    "Thorn-Gilded",
    "Old-King's",
    "Whispering",
)

NAME_NOUNS = (
    "Saber",
    "Cleaver",
    "Pike",
    "Falchion",
    "Axe",
    "Rapier",
    "Mace",
    "Spear",
)

WEAPON_TYPE_BY_NOUN = {
    "Saber": "saber",
    "Cleaver": "cleaver",
    "Pike": "spear",
    "Falchion": "falchion",
    "Axe": "axe",
    "Rapier": "rapier",
    "Mace": "mace",
    "Spear": "spear",
}


def generate_weapon(rng: Optional[random.Random] = None, rod_tier: int = 0) -> Weapon:
    """Generate a random ancient weapon.

    Passing a seeded ``random.Random`` makes generation repeatable for tests and
    for debug sessions. Better rods unlock stronger rarity tiers and shift the
    roll toward better catches.
    """

    rng = rng or random.Random()
    rarity, enchantment_count, damage_range = _roll_rarity(rng, rod_tier)
    enchantments = tuple(rng.sample(ENCHANTMENTS, enchantment_count))
    noun = rng.choice(NAME_NOUNS)
    name = f"{rng.choice(NAME_PREFIXES)} {noun}"

    return Weapon(
        name=name,
        rarity=rarity,
        base_damage=rng.randint(*damage_range),
        enchantments=enchantments,
        weapon_type=WEAPON_TYPE_BY_NOUN[noun],
    )


def fishing_rod_for_tier(tier: int) -> FishingRodTier:
    """Return the owned rod for a possibly out-of-range tier number."""

    clamped_tier = max(0, min(tier, len(FISHING_RODS) - 1))
    return FISHING_RODS[clamped_tier]


def next_fishing_rod(tier: int) -> Optional[FishingRodTier]:
    """Return the next buyable rod, or ``None`` when the player has the best one."""

    next_tier = tier + 1
    if next_tier >= len(FISHING_RODS):
        return None
    return FISHING_RODS[next_tier]


def rarity_weights_for_rod(tier: int) -> Tuple[Tuple[str, int], ...]:
    """Return the named rarity weights for UI and tests."""

    rod = fishing_rod_for_tier(tier)
    return tuple(zip(RARITY_ORDER, rod.rarity_weights))


def trait_summary(weapon: Weapon) -> str:
    """Return a player-facing trait list with undiscovered powers hidden."""

    visible_traits = list(weapon.known_trait_names())
    visible_traits.extend("???" for _ in range(weapon.hidden_trait_count()))
    return ", ".join(visible_traits) if visible_traits else "none"


def discover_traits(weapon: Weapon, trait_keys: Iterable[str]) -> Tuple[str, ...]:
    """Mark traits as discovered and return the newly revealed display names."""

    newly_revealed = []
    for key in trait_keys:
        if key in ENCHANTMENT_BY_KEY and key not in weapon.discovered:
            weapon.discovered.add(key)
            newly_revealed.append(ENCHANTMENT_BY_KEY[key].display_name)
    return tuple(newly_revealed)


def _roll_rarity(rng: random.Random, rod_tier: int = 0) -> Tuple[str, int, Tuple[int, int]]:
    weights = rarity_weights_for_rod(rod_tier)
    total_weight = sum(weight for _rarity, weight in weights)
    roll = rng.randint(1, total_weight)
    running = 0

    for rarity, weight in weights:
        running += weight
        if roll <= running:
            enchantment_count, damage_range = RARITY_DETAIL_BY_NAME[rarity]
            return rarity, enchantment_count, damage_range

    rarity = RARITY_ORDER[-1]
    enchantment_count, damage_range = RARITY_DETAIL_BY_NAME[rarity]
    return rarity, enchantment_count, damage_range
