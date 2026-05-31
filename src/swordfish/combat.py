"""Pure combat rules for Swordfish."""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Optional, Tuple

from .weapons import Weapon, weapon_ability


GOLD_REWARDS = {
    "rabbit": 5,
    "monster": 15,
    "bird": 8,
    "boar": 20,
    "snapper": 12,
    "wisp": 10,
    "boss": 50,
}


def apply_damage(raw: int, armor: int) -> int:
    """Apply flat armor reduction to incoming damage (minimum 1)."""
    return max(1, raw - armor)


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
    ability = weapon_ability(weapon)

    if ability.key == "mooncut":
        damage += 2
        discovered.append(ability.key)
        messages.append("Mooncut draws a bright second slash.")
    elif ability.key == "finisher":
        discovered.append(ability.key)
        if enemy.hp <= enemy.max_hp / 2:
            damage += 6
            messages.append("Finisher Chop bites into the wounded target.")
        else:
            damage += 1
            messages.append("Finisher Chop thuds, waiting for a weaker foe.")
    elif ability.key == "banner_pierce":
        discovered.append(ability.key)
        if enemy.kind in {"bird", "wisp"}:
            damage += 5
            messages.append("Banner Pierce skewers the airborne target.")
        else:
            damage += 2
            messages.append("Banner Pierce jabs from extra reach.")
    elif ability.key == "sweeping_edge":
        discovered.append(ability.key)
        damage += 2
        if enemy.kind == "rabbit":
            damage += 2
            messages.append("Sweeping Edge catches the small target cleanly.")
        else:
            messages.append("Sweeping Edge carves a wide arc.")
    elif ability.key == "armor_crack":
        discovered.append(ability.key)
        if enemy.kind in {"boar", "snapper", "monster", "boss"}:
            damage += 5
            messages.append("Armor Crack bites into a tough hide.")
        else:
            damage += 2
            messages.append("Armor Crack lands with a heavy thunk.")
    elif ability.key == "needle_crit":
        discovered.append(ability.key)
        damage += 1
        if rng.random() <= 0.35:
            damage += 6
            messages.append("Needle Crit finds a perfect opening.")
        else:
            messages.append("Needle Crit adds a precise little stab.")
    elif ability.key == "thunder_knock":
        discovered.append(ability.key)
        damage += 3
        if enemy.max_hp >= 25:
            damage += 2
            messages.append("Thunder Knock shakes the sturdy enemy.")
        else:
            messages.append("Thunder Knock booms on impact.")
    elif ability.key == "star_bolt":
        discovered.append(ability.key)
        damage += 3
        if enemy.kind == "wisp":
            damage += 4
            messages.append("Star Bolt burns bright through the floating magic.")
        else:
            messages.append("Star Bolt leaps from the staff.")
    elif ability.key == "thornshot":
        discovered.append(ability.key)
        damage += 2
        if enemy.kind in {"rabbit", "bird", "wisp"}:
            damage += 3
            messages.append("Thornshot catches the quick target.")
        else:
            messages.append("Thornshot whistles into the target.")
    elif ability.key == "boltbreaker":
        discovered.append(ability.key)
        damage += 4
        if enemy.max_hp >= 25:
            damage += 3
            messages.append("Boltbreaker punches into the sturdy enemy.")
        else:
            messages.append("Boltbreaker fires with a heavy snap.")

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
