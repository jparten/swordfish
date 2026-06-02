import random
import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from swordfish.combat import EnemyState, gold_reward_for_enemy, resolve_attack
from swordfish.weapons import (
    ENCHANTMENT_BY_KEY,
    FISHING_RODS,
    NAME_NOUNS,
    NAME_NOUN_WEIGHTS,
    RANGED_WEAPON_TYPES,
    WEAPON_TYPE_BY_NOUN,
    Weapon,
    ability_summary,
    ARMOR_TIERS,
    armor_tier_for_index,
    discover_traits,
    fishing_rod_for_tier,
    generate_weapon,
    is_ranged_weapon,
    next_fishing_rod,
    rarity_weights_for_rod,
    trait_summary,
    weapon_ability,
)


class WeaponGenerationTests(unittest.TestCase):
    def test_seeded_generation_is_repeatable(self):
        first = generate_weapon(random.Random(1234))
        second = generate_weapon(random.Random(1234))

        self.assertEqual(first.name, second.name)
        self.assertEqual(first.rarity, second.rarity)
        self.assertEqual(first.base_damage, second.base_damage)
        self.assertEqual(
            [enchantment.key for enchantment in first.enchantments],
            [enchantment.key for enchantment in second.enchantments],
        )

    def test_generated_weapon_has_valid_stats(self):
        weapon = generate_weapon(random.Random(8))

        self.assertGreaterEqual(weapon.base_damage, 4)
        self.assertLessEqual(weapon.base_damage, 12)
        self.assertGreaterEqual(len(weapon.enchantments), 1)
        self.assertLessEqual(len(weapon.enchantments), 3)
        self.assertIn(weapon.weapon_type, set(WEAPON_TYPE_BY_NOUN.values()))
        self.assertIsNotNone(weapon.ability)
        self.assertEqual(weapon_ability(weapon), weapon.ability)

    def test_ranged_weapon_types_are_valid(self):
        ranged_types = {"staff", "bow", "crossbow"}

        self.assertTrue(ranged_types.issubset(set(WEAPON_TYPE_BY_NOUN.values())))
        for weapon_type in ranged_types:
            weapon = Weapon(
                name=f"Test {weapon_type}",
                rarity="strange",
                base_damage=6,
                enchantments=(),
                weapon_type=weapon_type,
            )
            self.assertTrue(is_ranged_weapon(weapon))
            self.assertIsNotNone(weapon_ability(weapon))

    def test_ranged_weapon_forms_are_weighted_rare(self):
        noun_weights = dict(zip(NAME_NOUNS, NAME_NOUN_WEIGHTS))
        melee_weights = [
            weight
            for noun, weight in noun_weights.items()
            if WEAPON_TYPE_BY_NOUN[noun] not in RANGED_WEAPON_TYPES
        ]
        ranged_weights = [
            weight
            for noun, weight in noun_weights.items()
            if WEAPON_TYPE_BY_NOUN[noun] in RANGED_WEAPON_TYPES
        ]

        self.assertTrue(ranged_weights)
        self.assertLess(max(ranged_weights), min(melee_weights))

    def test_better_rods_shift_rarity_toward_relics(self):
        starter_weights = dict(rarity_weights_for_rod(0))
        copper_weights = dict(rarity_weights_for_rod(1))
        best_weights = dict(rarity_weights_for_rod(len(FISHING_RODS) - 1))

        self.assertEqual(starter_weights["relic"], 0)
        self.assertEqual(starter_weights["mythic"], 0)
        self.assertGreater(copper_weights["relic"], 0)
        self.assertEqual(copper_weights["mythic"], 0)
        self.assertLess(best_weights["weathered"], starter_weights["weathered"])
        self.assertGreater(best_weights["relic"], starter_weights["relic"])
        self.assertGreater(best_weights["mythic"], starter_weights["mythic"])

    def test_rod_tiers_clamp_and_advance(self):
        self.assertEqual(fishing_rod_for_tier(-5), FISHING_RODS[0])
        self.assertEqual(fishing_rod_for_tier(999), FISHING_RODS[-1])
        self.assertEqual(next_fishing_rod(0), FISHING_RODS[1])
        self.assertIsNone(next_fishing_rod(len(FISHING_RODS) - 1))

    def test_armor_tiers_have_longer_upgrade_path(self):
        self.assertGreaterEqual(len(ARMOR_TIERS), 7)
        self.assertEqual(armor_tier_for_index(-5), ARMOR_TIERS[0])
        self.assertEqual(armor_tier_for_index(999), ARMOR_TIERS[-1])
        self.assertEqual(
            [armor.cost for armor in ARMOR_TIERS],
            sorted(armor.cost for armor in ARMOR_TIERS),
        )
        self.assertEqual(
            [armor.armor_value for armor in ARMOR_TIERS],
            sorted(armor.armor_value for armor in ARMOR_TIERS),
        )

    def test_trait_summary_hides_undiscovered_traits(self):
        weapon = Weapon(
            name="Test Saber",
            rarity="relic",
            base_damage=7,
            enchantments=(
                ENCHANTMENT_BY_KEY["flame"],
                ENCHANTMENT_BY_KEY["leech"],
            ),
        )

        self.assertEqual(trait_summary(weapon), "???, ???")
        discover_traits(weapon, ["flame"])
        self.assertEqual(trait_summary(weapon), "Cinderwake, ???")

    def test_ability_summary_hides_until_discovered(self):
        weapon = generate_weapon(random.Random(12))
        ability = weapon_ability(weapon)

        self.assertEqual(ability_summary(weapon), "???")
        discover_traits(weapon, [ability.key])
        self.assertEqual(ability_summary(weapon), ability.display_name)


class CombatRuleTests(unittest.TestCase):
    def test_rabbit_bane_reveals_only_against_rabbits(self):
        weapon = Weapon(
            name="Test Pike",
            rarity="strange",
            base_damage=5,
            enchantments=(ENCHANTMENT_BY_KEY["rabbit_bane"],),
        )

        monster_result = resolve_attack(
            weapon,
            EnemyState(name="Mire Grub", kind="monster", hp=20, max_hp=20),
            random.Random(1),
        )
        rabbit_result = resolve_attack(
            weapon,
            EnemyState(name="Rabbit", kind="rabbit", hp=20, max_hp=20),
            random.Random(1),
        )

        self.assertEqual(monster_result.damage_dealt, 7)
        self.assertNotIn("rabbit_bane", monster_result.discovered_traits)
        self.assertEqual(rabbit_result.damage_dealt, 14)
        self.assertIn("rabbit_bane", rabbit_result.discovered_traits)

    def test_curse_deals_extra_damage_and_self_damage(self):
        weapon = Weapon(
            name="Test Cleaver",
            rarity="relic",
            base_damage=6,
            enchantments=(ENCHANTMENT_BY_KEY["curse"],),
        )

        result = resolve_attack(
            weapon,
            EnemyState(name="Rabbit", kind="rabbit", hp=20, max_hp=20),
            random.Random(1),
        )

        self.assertEqual(result.damage_dealt, 12)
        self.assertEqual(result.self_damage, 2)
        self.assertIn("curse", result.discovered_traits)

    def test_weapon_ability_reveals_on_attack(self):
        weapon = Weapon(
            name="Test Rapier",
            rarity="strange",
            base_damage=5,
            enchantments=(),
            weapon_type="rapier",
        )

        result = resolve_attack(
            weapon,
            EnemyState(name="Rabbit", kind="rabbit", hp=20, max_hp=20),
            random.Random(2),
        )

        self.assertIn("needle_crit", result.discovered_traits)
        self.assertGreaterEqual(result.damage_dealt, 6)

    def test_ranged_weapon_ability_adds_damage(self):
        weapon = Weapon(
            name="Test Staff",
            rarity="strange",
            base_damage=5,
            enchantments=(),
            weapon_type="staff",
        )

        result = resolve_attack(
            weapon,
            EnemyState(name="Lantern Wisp", kind="wisp", hp=20, max_hp=20),
            random.Random(2),
        )

        self.assertEqual(result.damage_dealt, 12)
        self.assertIn("star_bolt", result.discovered_traits)

    def test_gold_rewards_match_enemy_type(self):
        self.assertEqual(gold_reward_for_enemy("rabbit"), 5)
        self.assertEqual(gold_reward_for_enemy("monster"), 15)
        self.assertEqual(gold_reward_for_enemy("unknown"), 0)


if __name__ == "__main__":
    unittest.main()
