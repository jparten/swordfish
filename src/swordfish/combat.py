"""Pure combat rules for Swordfish."""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Optional, Tuple

from .weapons import Weapon


GOLD_REWARDS = {
    "rabbit": 5,
    "monster": 15,
    "bird": 8,
    "boar": 20,
}


@dataclass(frozen=True)
class EnemyState:
    name: str
    kind: str
    hp: int
    max_hp: int


@dataclass(frozen=True)
class AttackResult:
    damage_dealt: int
    enemy_hp_after: int
    self_damage: int
    healing: int
    discovered_traits: Tuple[str, ...]
    messages: Tuple[str, ...]
    defeated: bool


def gold_reward_for_enemy(enemy_kind: str) -> int:
    """Return the coin reward for defeating an enemy kind."""

    return GOLD_REWARDS.get(enemy_kind, 0)


def resolve_attack(
    weapon: Weapon, enemy: EnemyState, rng: Optional[random.Random] = None
) -> AttackResult:
    """Resolve one weapon attack against one enemy without touching Panda3D."""

    rng = rng or random.Random()
    damage = weapon.base_damage
    self_damage = 0
    healing = 0
    discovered = []
    messages = [f"{weapon.name} hits {enemy.name}."]

    for enchantment in weapon.enchantments:
        key = enchantment.key

        if key == "flame":
            damage += 3
            discovered.append(key)
            messages.append("Cinders flash along the blade.")
        elif key == "frost":
            damage += 2
            discovered.append(key)
            messages.append(f"Cold mist clings to {enemy.name}.")
        elif key == "shock":
            if rng.random() <= 0.45:
                damage += 5
                discovered.append(key)
                messages.append("Lightning snaps from the weapon.")
        elif key == "leech":
            healing += 2
            discovered.append(key)
            messages.append("A green rune drinks the impact and heals you.")
        elif key == "curse":
            damage += 4
            self_damage += 2
            discovered.append(key)
            messages.append("The weapon demands a blood price.")
        elif key == "rabbit_bane" and enemy.kind == "rabbit":
            damage += 7
            discovered.append(key)
            messages.append("The weapon hums with suspiciously specific rabbit hatred.")
        elif key == "monster_bane" and enemy.kind == "monster":
            damage += 8
            discovered.append(key)
            messages.append("Ancient monster-slaying letters flare awake.")

    enemy_hp_after = max(0, enemy.hp - damage)
    defeated = enemy_hp_after == 0
    messages.append(f"{enemy.name} takes {damage} damage.")
    if defeated:
        messages.append(f"{enemy.name} is defeated.")

    return AttackResult(
        damage_dealt=damage,
        enemy_hp_after=enemy_hp_after,
        self_damage=self_damage,
        healing=healing,
        discovered_traits=tuple(dict.fromkeys(discovered)),
        messages=tuple(messages),
        defeated=defeated,
    )
