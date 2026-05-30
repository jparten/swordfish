# Swordfish

Swordfish is a tiny Panda3D vertical slice for a 3D fantasy game about fishing ancient weapons out of a lake and discovering their hidden powers in combat.

This first build is intentionally small. It has a lake, a dock, a rod shop, a test arena, rabbits, an occasional monster, random weapons, hidden weapon traits, and a combat log that reveals what a weapon does as you use it.

The current visual pass uses simple low-poly procedural shapes. The player has a face and a readable body silhouette, weapons use shaped low-poly blades and heads instead of simple cubes, attacks play a swing animation, enemies flash/slide back when hit, and rabbits shed a small stylized fur chip with a few red droplets. Rabbits hop around the arena, tense up before lunging, and pop into a small fur puff when defeated. The lake has a rounded natural shoreline, blocks walking into deep water, and is surrounded by simple trees. Fishing now has a small timing moment with a visible line to the bobber: cast, watch the bobber, press `E` again when it bites, then pull a weapon out with a splash. Defeated rabbits drop 5 gold coins, monsters drop 15, and the shop sells better fishing rods that unlock stronger weapon rarities. The inspection card shows a rotating preview of the recovered weapon, and every weapon form has its own special visual detail.

## Important Environment Rule

Use `pyenv virtualenv`. Do not install Panda3D into the native/system Python.

The repo includes `.python-version` set to `swordfish`, which tells `pyenv` to use the project virtualenv while you are inside this folder.

## One-Time Setup

These steps assume `pyenv` is already installed and initialized in your shell.

From the repo root:

```bash
cd /Users/jparten/source/swordfish
```

Install the project Python with `pyenv` if you do not already have it:

```bash
pyenv install 3.11.9
```

Make sure `pyenv` sees the project version:

```bash
pyenv virtualenv 3.11.9 swordfish
pyenv local swordfish
python --version
```

You should see Python `3.11.9`.

Install the game into the active `pyenv virtualenv`:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

## Running the Game

Activate the virtual environment if it is not already active:

```bash
cd /Users/jparten/source/swordfish
pyenv local swordfish
```

Run the game:

```bash
python -m swordfish
```

You can also run it through the installed script:

```bash
swordfish
```

## Controls

- `W`, `A`, `S`, `D`: move
- `E`: interact; cast near the dock/lake, press again when the bobber bites, or buy the next fishing rod at the shop
- `I`: inspect the current weapon
- `Space`: attack nearby enemies with the current weapon
- `R`: reset the arena and restore health
- `M`: spawn a monster for testing
- `Esc`: quit

## What To Test First

1. Start the game.
2. Stand near the dock and press `E` to cast.
3. Watch the bobber, then press `E` again when the prompt says `Bite!`.
4. Inspect the new weapon card, rotate your attention to the weapon preview, and notice which traits are still hidden.
5. Walk down into the arena.
6. Attack rabbits until the combat log reveals one or more hidden weapon traits and awards gold.
7. Walk to the rod shop on the west side of the lake path and press `E` when you can afford the next rod.
8. Inspect the weapon again to see the newly discovered trait descriptions.
9. Fish again with the upgraded rod to unlock stronger weapons.
10. Every third successful catch spawns a larger monster.

The main thing to evaluate is whether the loop feels promising: fish up something mysterious, test it, earn coins, buy a better rod, and decide whether you want another weapon.

## Running Automated Tests

The tests cover pure Python game rules like weapon generation, repeatable random seeds, rod rarity odds, trait discovery, gold rewards, and combat effects.

```bash
cd /Users/jparten/source/swordfish
pyenv local swordfish
python -m unittest discover -s tests
```

These tests do not open a Panda3D window.

## Project Structure

- `src/swordfish/weapons.py`: weapon names, rarity, enchantments, and discovery helpers
- `src/swordfish/combat.py`: pure combat math and enemy gold rewards
- `src/swordfish/game.py`: Panda3D scene, player movement, enemies, UI, and input
- `tests/test_game_rules.py`: automated tests for non-rendering game logic
- `AGENTS.md`: project memory and instructions for future coding sessions

## Troubleshooting

If `python -m swordfish` says `No module named panda3d`, the virtual environment probably is not active or dependencies were not installed into it. Run:

```bash
pyenv local swordfish
python -m pip install -e .
```

If `python --version` does not show `3.11.9`, check that `pyenv` and `pyenv-virtualenv` are installed and initialized in the shell, then run:

```bash
pyenv local swordfish
```
