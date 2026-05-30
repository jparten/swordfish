# Swordfish Project Instructions

## Project Identity

- Working title: `Swordfish`.
- Genre target: 3D fantasy fishing and combat prototype.
- Engine choice: Panda3D.
- Language choice: Python.
- Audience for explanations: the primary user is new to game development, and their dad is comfortable with Python. Explain game-dev concepts clearly and avoid assuming prior engine knowledge.

## Core Premise

The player fishes an ancient lake for forgotten weapons. Each recovered weapon can have hidden powers, enchantments, quirks, curses, or strange behaviors. The player discovers what a weapon does by testing it in combat against rabid white rabbits and occasional monsters. Defeated enemies award gold, and a rod shop lets the player buy better fishing rods that unlock stronger weapon rarities.

The strongest design pillar is discovery through experimentation. The game should make the player wonder, "What does this weapon actually do?" and then give them playful ways to find out.

## Recommended First Milestone

Build a small vertical slice before expanding the world:

- A simple 3D scene with ground, lake, player, and test arena.
- Basic third-person or top-down 3D movement.
- A fishing interaction that generates one random weapon.
- A small weapon inventory or current-weapon slot.
- A few enemy rabbits that can be spawned or placed in the arena.
- A basic attack that applies weapon effects.
- A discovery log that reveals weapon traits after the player observes them in combat.

Do not start with a large open world, complex art pipeline, crafting system, or full story. Prove the loop first.

## Technical Direction

- Use Panda3D and Python for the game runtime.
- Use `pyenv virtualenv` for dependencies. Do not install packages into the user's native/system Python.
- Keep game logic testable outside the renderer when practical.
- Separate pure rules from engine objects:
  - Weapon generation
  - Enchantment definitions
  - Damage calculations
  - Discovery conditions
- Rarity tables
- Fishing rod tiers and their rarity odds
- Enemy gold rewards
- Prefer small Python modules with clear names over a single large script.
- Prefer data-driven definitions for weapons, enchantments, enemies, and effects once the prototype has more than a handful of examples.
- Use seeded random generation for reproducible tests and debug sessions.
- Keep the first implementation simple enough that a Python programmer new to Panda3D can follow it.

## Testing Strategy

Use automated tests for pure game logic:

- Weapon generator returns valid weapons.
- Rarity and enchantment combinations obey constraints.
- Better fishing rods shift catch odds toward stronger rarities.
- Damage and status effects produce expected results.
- Enemy gold rewards match the intended economy.
- Discovery rules reveal traits at the correct time.
- Seeded random generation is repeatable.

Use manual/debug testing for engine behavior:

- A debug scene or hotkeys should quickly spawn weapons and enemies.
- Combat should show clear feedback through logs, labels, particles, sound, or simple visual cues.
- The player should be able to test a weapon within seconds of launching the prototype.

## Design Tone

- Fantasy, strange, and playful.
- Ancient lake mystery plus slightly absurd testing grounds.
- Combat should be stylized rather than graphic.
- Rabbits can be dangerous and chaotic, but avoid realistic gore.

## Collaboration Notes

- Before major coding work, ask only the questions that would materially change architecture, controls, platform, or scope.
- When implementing, favor a working prototype over polished art.
- Explain what each new system does in beginner-friendly terms.
- Keep changes small and verifiable.
- If adding dependencies, document how to install and run them.
- If a dev server or game window is needed, provide exact commands to run the prototype.

## Current Decision Log

- Godot was considered first.
- Panda3D was selected because the project should be 3D and the user's dad is comfortable with Python.
- The first build should focus on validating the fishing-to-weapon-to-combat-discovery loop.
