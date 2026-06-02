"""Panda3D vertical slice for Swordfish."""

from __future__ import annotations

import builtins
from dataclasses import dataclass, field
import math
from pathlib import Path
import random
import textwrap
from typing import List, Optional, Tuple

from direct.gui.DirectFrame import DirectFrame
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import (
    AmbientLight,
    DirectionalLight,
    Fog,
    Geom,
    GeomNode,
    GeomTriangles,
    GeomVertexData,
    GeomVertexFormat,
    GeomVertexWriter,
    TextNode,
    TransparencyAttrib,
    Vec3,
    WindowProperties,
)

from .combat import EnemyState, apply_damage, gold_reward_for_enemy, resolve_attack
from .weapons import (
    ARMOR_TIERS,
    FISHING_RODS,
    Weapon,
    ability_summary,
    armor_tier_for_index,
    discover_traits,
    fishing_rod_for_tier,
    generate_weapon,
    is_ranged_weapon,
    next_fishing_rod,
    trait_summary,
    weapon_ability,
)


WORLD_LIMIT = 220.0
FOREST_EDGE = 228.0
FOREST_GROUND = 680.0
WORLD_FIELD_BOUNDS = (-WORLD_LIMIT + 2.0, WORLD_LIMIT - 2.0, -WORLD_LIMIT + 2.0, WORLD_LIMIT - 2.0)
MOB_RESPAWN_INTERVAL = 240.0
FIELD_MOB_TARGETS = {
    "rabbit": 4,
    "bird": 5,
    "boar": 4,
    "snapper": 3,
    "wisp": 3,
}
PLAYER_SPEED = 7.0
SPRINT_SPEED_MULTIPLIER = 1.55
SPRINT_STAMINA_DRAIN = 24.0
SPRINT_MIN_STAMINA = 8.0
SPRINT_DUST_INTERVAL = 0.14
HP_REGEN_DELAY = 4.0
HP_REGEN_INTERVAL = 1.2
HP_REGEN_AMOUNT = 1
DODGE_SPEED = 20.0
DODGE_DURATION = 0.22
DODGE_COOLDOWN = 0.75
DODGE_STAMINA_COST = 25
ABILITY_STAMINA_COST = 35
STAMINA_REGEN_DELAY = 0.55
STAMINA_REGEN_RATE = 24.0
ENEMY_TURN_GAP = 0.6
ENEMY_TURN_MAX_HOLD = 1.6
ENEMY_WAIT_DISTANCE = 2.3
LEASH_RANGE = 22.0
ATTACK_RANGE = 2.6
RANGED_ATTACK_RANGE = 10.0
RANGED_ATTACK_CONE_DOT = 0.92
WEAPON_ABILITY_COOLDOWN = 6.0
ACTIVE_MELEE_RANGE = 5.4
ACTIVE_RANGED_RANGE = 14.0
ACTIVE_DAMAGE_BONUS = 8
PET_FOLLOW_DISTANCE = 1.65
PET_SPEED = 5.2
PET_SENSE_RANGE = 5.2
PET_ATTACK_RANGE = 1.35
PET_ATTACK_DAMAGE = 2
PET_ATTACK_COOLDOWN = 2.25
FISHING_RANGE = 4.5
SHOP_RANGE = 3.0
CHEST_RANGE = 2.5
CHEST_GUARD_RADIUS = 4.8
SHOP_SPOT = Vec3(-10.4, 1.7, 0)
FORGE_SPOT = Vec3(6.5, 4.5, 0)
FORGE_RANGE = 3.0
CAVE_POOL_SPOT = Vec3(-31.5, -36.2, 0)
CAVE_POOL_CENTER = Vec3(-32.4, -38.4, 0)
CAVE_BOUNDS = (-42.0, -21.0, -47.5, -27.0)
HOME_RAFT_SPOT = Vec3(2.7, 6.7, 0)
LEVEL2_RAFT_SPOT = Vec3(145.0, -103.0, 0)
LEVEL2_ARRIVAL_SPOT = Vec3(145.0, -99.0, 0)
LEVEL2_LAKE_SPOT = Vec3(166.0, -135.0, 0)
LEVEL2_LAKE_CENTER = Vec3(168.0, -141.0, 0)
LEVEL2_ZONE_BOUNDS = (126.0, 208.0, -190.0, -88.0)
LEVEL2_EMBER_BOUNDS = (130.0, 170.0, -188.0, -150.0)
LEVEL2_MOON_BOUNDS = (168.0, 208.0, -132.0, -92.0)
FROST_BIOME_CENTER = Vec3(78.0, 76.0, 0)
FROST_BIOME_BOUNDS = (42.0, 114.0, 36.0, 112.0)
SUNKEN_MEADOW_CENTER = Vec3(-92.0, 72.0, 0)
SUNKEN_MEADOW_BOUNDS = (-120.0, -66.0, 42.0, 104.0)
BOSS_ARENA_CENTER = Vec3(-38, 38, 0)
BOSS_ARENA_RADIUS = 7.0
ARENA_MIN_X = -8.2
ARENA_MAX_X = 8.2
ARENA_MIN_Y = -13.2
ARENA_MAX_Y = -4.6
TREASURE_MAP_BOUNDS = (11.5, 31.5, -33.0, -18.0)
WATER_BLOBS = (
    (0.0, 9.7, 12.2, 6.3),
    (-8.2, 9.5, 4.3, 3.7),
    (8.4, 10.2, 4.0, 3.3),
    (168.0, -141.0, 15.5, 10.5),
)
DOCK_SAFE_ZONE = (-1.9, 1.9, 2.4, 6.9)
DEFAULT_WEAPON_COLOR = (0.74, 0.78, 0.78, 1)
CEL_INK_ENABLED = False
CEL_INK_COLOR = (0.025, 0.02, 0.018, 1)
CEL_INK_THICKNESS = 2.0
IMPORTED_PLAYER_BASE_HPR = (180.0, 90.0, 0.0)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUATERNIUS_NATURE_ASSET_DIR = PROJECT_ROOT / "assets" / "models" / "Ultimate Nature Pack by Quaternius" / "OBJ"
QUATERNIUS_KNIGHT_ASSET_DIR = PROJECT_ROOT / "assets" / "models" / "Knight Character Animated by Quaternius" / "OBJ"
QUATERNIUS_WEAPON_ASSET_DIR = PROJECT_ROOT / "assets" / "models" / "Medieval Weapons Pack by Quaternius" / "OBJ"
ASSET_MODEL_CACHE = {}
COMMON_TREE_MODELS = (
    "CommonTree_1",
    "CommonTree_2",
    "CommonTree_3",
    "CommonTree_4",
    "CommonTree_5",
    "BirchTree_1",
    "BirchTree_2",
    "BirchTree_3",
    "BirchTree_4",
    "BirchTree_5",
)
TWISTED_TREE_MODELS = (
    "Willow_1",
    "Willow_2",
    "Willow_3",
    "Willow_4",
    "Willow_5",
    "CommonTree_Dead_1",
    "CommonTree_Dead_2",
    "CommonTree_Dead_3",
)
PINE_TREE_MODELS = ("PineTree_1", "PineTree_2", "PineTree_3", "PineTree_4", "PineTree_5")
SNOW_TREE_MODELS = (
    "PineTree_Snow_1",
    "PineTree_Snow_2",
    "PineTree_Snow_3",
    "CommonTree_Snow_1",
    "CommonTree_Snow_2",
)
WEAPON_ASSET_BY_TYPE = {
    "saber": "Sword",
    "falchion": "Sword_Big",
    "axe": "Axe",
    "mace": "Hammer_Double",
    "rapier": "Sword_2",
    "spear": "Spear",
    "cleaver": "Claymore",
    "bow": "Bow_Wooden",
}
ENCHANTMENT_GLOW_COLORS = {
    "flame": (1.0, 0.35, 0.08, 0.62),
    "frost": (0.45, 0.82, 1.0, 0.55),
    "shock": (1.0, 0.92, 0.25, 0.65),
    "leech": (0.24, 0.95, 0.45, 0.52),
    "curse": (0.75, 0.05, 0.12, 0.62),
    "rabbit_bane": (1.0, 0.72, 0.9, 0.5),
    "monster_bane": (0.72, 0.55, 1.0, 0.55),
}


@dataclass
class SceneEnemy:
    name: str
    kind: str
    hp: int
    max_hp: int
    node: object
    speed: float
    contact_damage: int
    visual_node: object = None
    body_node: object = None
    head_node: object = None
    left_detail_node: object = None
    right_detail_node: object = None
    left_foot_node: object = None
    right_foot_node: object = None
    tail_node: object = None
    animation_phase: float = 0.0
    attack_cooldown: float = 0.0
    flash_time: float = 0.0
    knockback_velocity: Vec3 = field(default_factory=Vec3)
    ai_state: str = "idle"
    state_timer: float = 0.0
    hop_duration: float = 0.0
    hop_start_pos: Vec3 = field(default_factory=Vec3)
    hop_target_pos: Vec3 = field(default_factory=Vec3)
    lunge_direction: Vec3 = field(default_factory=Vec3)
    attack_landed: bool = False
    bounds: Optional[Tuple[float, float, float, float]] = None
    home_pos: Vec3 = field(default_factory=Vec3)


@dataclass
class SceneChest:
    name: str
    node: object
    pos: Vec3
    reward_gold: int
    guard_kind: str
    guard_bounds: Optional[Tuple[float, float, float, float]] = None
    opened: bool = False


@dataclass
class HitEffect:
    node: object
    velocity: Vec3
    lifetime: float
    max_lifetime: float
    spin_rate: Vec3


@dataclass
class RangedShot:
    node: object
    velocity: Vec3
    lifetime: float
    max_lifetime: float
    spin_rate: Vec3
    impact_pos: Vec3
    impact_color: Tuple[float, float, float, float]


@dataclass
class AnimatedDetail:
    node: object
    base_pos: Vec3
    phase: float
    speed: float
    bob_amount: float
    sway_amount: float
    color: Tuple[float, float, float, float]


def _should_add_ink(color: Tuple[float, float, float, float], size_hint: Tuple[float, ...]) -> bool:
    if not CEL_INK_ENABLED:
        return False
    if color[3] < 0.95:
        return False
    if max(size_hint) < 0.16:
        return False
    return True


def _add_ink_wire(
    parent,
    name: str,
    geom: Geom,
    color: Tuple[float, float, float, float],
    size_hint: Tuple[float, ...],
    pos: Tuple[float, float, float],
    hpr: Tuple[float, float, float],
    scale: Optional[Tuple[float, float, float]] = None,
):
    if not _should_add_ink(color, size_hint):
        return

    ink_node = GeomNode(f"{name}-ink")
    ink_node.addGeom(geom)
    ink = parent.attachNewNode(ink_node)
    if scale is not None:
        ink.setScale(*scale)
    ink.setPos(*pos)
    ink.setHpr(*hpr)
    ink.setColor(*CEL_INK_COLOR)
    ink.setRenderModeWireframe()
    ink.setRenderModeThickness(CEL_INK_THICKNESS)
    ink.setDepthOffset(-1)
    ink.setLightOff(1)
    ink.setTwoSided(True)


def make_box(
    parent,
    name: str,
    size: Tuple[float, float, float],
    color: Tuple[float, float, float, float],
    pos: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    hpr: Tuple[float, float, float] = (0.0, 0.0, 0.0),
):
    """Create a colored box with per-face normals for proper shading."""

    face_data = (
        ((0, 0, -1), (-0.5, -0.5, -0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5)),
        ((0, 0, 1), (-0.5, -0.5, 0.5), (-0.5, 0.5, 0.5), (0.5, 0.5, 0.5), (0.5, -0.5, 0.5)),
        ((0, -1, 0), (-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, -0.5, -0.5)),
        ((0, 1, 0), (-0.5, 0.5, -0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5), (-0.5, 0.5, 0.5)),
        ((-1, 0, 0), (-0.5, -0.5, -0.5), (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (-0.5, -0.5, 0.5)),
        ((1, 0, 0), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5), (0.5, 0.5, -0.5)),
    )

    vdata = GeomVertexData(name, GeomVertexFormat.getV3n3(), Geom.UHStatic)
    vertex_writer = GeomVertexWriter(vdata, "vertex")
    normal_writer = GeomVertexWriter(vdata, "normal")

    for normal, v0, v1, v2, v3 in face_data:
        for v in (v0, v1, v2, v3):
            vertex_writer.addData3(*v)
            normal_writer.addData3(*normal)

    primitive = GeomTriangles(Geom.UHStatic)
    for face_index in range(6):
        base = face_index * 4
        primitive.addVertices(base, base + 1, base + 2)
        primitive.addVertices(base, base + 2, base + 3)
    primitive.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(primitive)

    node = GeomNode(name)
    node.addGeom(geom)

    node_path = parent.attachNewNode(node)
    node_path.setScale(*size)
    node_path.setPos(*pos)
    node_path.setHpr(*hpr)
    node_path.setColor(*color)
    node_path.setTwoSided(True)

    if color[3] < 1.0:
        node_path.setTransparency(TransparencyAttrib.MAlpha)

    _add_ink_wire(parent, name, geom, color, size, pos, hpr, size)
    return node_path


def make_ellipsoid(
    parent,
    name: str,
    radius: Tuple[float, float, float],
    color: Tuple[float, float, float, float],
    pos: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    hpr: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    segments: int = 10,
    rings: int = 5,
):
    """Create a simple low-poly rounded ellipsoid for softer silhouettes."""

    radius_x, radius_y, radius_z = radius
    vdata = GeomVertexData(name, GeomVertexFormat.getV3n3(), Geom.UHStatic)
    vertex_writer = GeomVertexWriter(vdata, "vertex")
    normal_writer = GeomVertexWriter(vdata, "normal")

    for ring in range(rings + 1):
        theta = math.pi * ring / rings
        z = math.cos(theta) * radius_z
        ring_radius = math.sin(theta)
        for segment in range(segments):
            phi = math.pi * 2.0 * segment / segments
            nx = math.cos(phi) * ring_radius
            ny = math.sin(phi) * ring_radius
            nz = math.cos(theta)
            vertex_writer.addData3(nx * radius_x, ny * radius_y, z)
            normal_writer.addData3(nx, ny, nz)

    primitive = GeomTriangles(Geom.UHStatic)
    for ring in range(rings):
        for segment in range(segments):
            current = ring * segments + segment
            next_current = ring * segments + ((segment + 1) % segments)
            below = (ring + 1) * segments + segment
            next_below = (ring + 1) * segments + ((segment + 1) % segments)
            primitive.addVertices(current, below, next_below)
            primitive.addVertices(current, next_below, next_current)
    primitive.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(primitive)

    node = GeomNode(name)
    node.addGeom(geom)
    node_path = parent.attachNewNode(node)
    node_path.setPos(*pos)
    node_path.setHpr(*hpr)
    node_path.setColor(*color)
    node_path.setTwoSided(True)
    if color[3] < 1.0:
        node_path.setTransparency(TransparencyAttrib.MAlpha)
    _add_ink_wire(parent, name, geom, color, radius, pos, hpr)
    return node_path


def make_cylinder(
    parent,
    name: str,
    radius: Tuple[float, float],
    height: float,
    color: Tuple[float, float, float, float],
    pos: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    hpr: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    segments: int = 8,
):
    """Create a low-poly elliptical cylinder along local Z."""

    radius_x, radius_y = radius
    half_height = height / 2.0
    vdata = GeomVertexData(name, GeomVertexFormat.getV3n3(), Geom.UHStatic)
    vertex_writer = GeomVertexWriter(vdata, "vertex")
    normal_writer = GeomVertexWriter(vdata, "normal")
    vertex_writer.addData3(0, 0, half_height)
    normal_writer.addData3(0, 0, 1)
    vertex_writer.addData3(0, 0, -half_height)
    normal_writer.addData3(0, 0, -1)

    for z in (half_height, -half_height):
        for segment in range(segments):
            angle = math.pi * 2.0 * segment / segments
            nx, ny = math.cos(angle), math.sin(angle)
            vertex_writer.addData3(nx * radius_x, ny * radius_y, z)
            normal_writer.addData3(nx, ny, 0)

    primitive = GeomTriangles(Geom.UHStatic)
    top_start = 2
    bottom_start = 2 + segments
    for segment in range(segments):
        next_segment = (segment + 1) % segments
        top_current = top_start + segment
        top_next = top_start + next_segment
        bottom_current = bottom_start + segment
        bottom_next = bottom_start + next_segment

        primitive.addVertices(0, top_current, top_next)
        primitive.addVertices(1, bottom_next, bottom_current)
        primitive.addVertices(top_current, bottom_current, bottom_next)
        primitive.addVertices(top_current, bottom_next, top_next)
    primitive.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(primitive)

    node = GeomNode(name)
    node.addGeom(geom)
    node_path = parent.attachNewNode(node)
    node_path.setPos(*pos)
    node_path.setHpr(*hpr)
    node_path.setColor(*color)
    node_path.setTwoSided(True)
    if color[3] < 1.0:
        node_path.setTransparency(TransparencyAttrib.MAlpha)
    _add_ink_wire(parent, name, geom, color, (radius_x, radius_y, height), pos, hpr)
    return node_path


def make_flat_blob(
    parent,
    name: str,
    center: Tuple[float, float, float],
    radius_x: float,
    radius_y: float,
    color: Tuple[float, float, float, float],
    points: int = 28,
    wobble: float = 0.14,
    rotation_degrees: float = 0.0,
    seed: int = 0,
):
    """Create a flat irregular oval, useful for natural water/shore shapes."""

    rng = random.Random(seed)
    vdata = GeomVertexData(name, GeomVertexFormat.getV3n3(), Geom.UHStatic)
    vertex_writer = GeomVertexWriter(vdata, "vertex")
    normal_writer = GeomVertexWriter(vdata, "normal")
    vertex_writer.addData3(0, 0, 0)
    normal_writer.addData3(0, 0, 1)

    rotation = math.radians(rotation_degrees)
    for index in range(points):
        angle = rotation + (math.pi * 2.0 * index) / points
        wave = 1.0 + math.sin(angle * 3.0 + seed) * wobble * 0.45
        jitter = 1.0 + rng.uniform(-wobble, wobble)
        radius_scale = wave * jitter
        vertex_writer.addData3(
            math.cos(angle) * radius_x * radius_scale,
            math.sin(angle) * radius_y * radius_scale,
            0,
        )
        normal_writer.addData3(0, 0, 1)

    primitive = GeomTriangles(Geom.UHStatic)
    for index in range(1, points + 1):
        next_index = 1 if index == points else index + 1
        primitive.addVertices(0, index, next_index)
    primitive.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(primitive)

    node = GeomNode(name)
    node.addGeom(geom)
    node_path = parent.attachNewNode(node)
    node_path.setPos(*center)
    node_path.setColor(*color)
    node_path.setTwoSided(True)
    if color[3] < 1.0:
        node_path.setTransparency(TransparencyAttrib.MAlpha)
    return node_path


def make_flat_prism(
    parent,
    name: str,
    points: Tuple[Tuple[float, float], ...],
    thickness: float,
    color: Tuple[float, float, float, float],
    pos: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    hpr: Tuple[float, float, float] = (0.0, 0.0, 0.0),
):
    """Create a low-poly extruded shape in local X/Y with thickness on Z."""

    if len(points) < 3:
        raise ValueError("A prism needs at least three outline points.")

    half_thickness = thickness / 2.0
    center_x = sum(point[0] for point in points) / len(points)
    center_y = sum(point[1] for point in points) / len(points)

    vdata = GeomVertexData(name, GeomVertexFormat.getV3n3(), Geom.UHStatic)
    vertex_writer = GeomVertexWriter(vdata, "vertex")
    normal_writer = GeomVertexWriter(vdata, "normal")
    vertex_writer.addData3(center_x, center_y, half_thickness)
    normal_writer.addData3(0, 0, 1)
    vertex_writer.addData3(center_x, center_y, -half_thickness)
    normal_writer.addData3(0, 0, -1)

    for x, y in points:
        vertex_writer.addData3(x, y, half_thickness)
        normal_writer.addData3(0, 0, 1)
    for x, y in points:
        vertex_writer.addData3(x, y, -half_thickness)
        normal_writer.addData3(0, 0, -1)

    primitive = GeomTriangles(Geom.UHStatic)
    count = len(points)
    for index in range(count):
        front_current = 2 + index
        front_next = 2 + ((index + 1) % count)
        back_current = 2 + count + index
        back_next = 2 + count + ((index + 1) % count)

        primitive.addVertices(0, front_current, front_next)
        primitive.addVertices(1, back_next, back_current)
        primitive.addVertices(front_current, back_current, back_next)
        primitive.addVertices(front_current, back_next, front_next)

    primitive.closePrimitive()
    geom = Geom(vdata)
    geom.addPrimitive(primitive)

    node = GeomNode(name)
    node.addGeom(geom)
    node_path = parent.attachNewNode(node)
    node_path.setPos(*pos)
    node_path.setHpr(*hpr)
    node_path.setColor(*color)
    node_path.setTwoSided(True)
    if color[3] < 1.0:
        node_path.setTransparency(TransparencyAttrib.MAlpha)
    width = max(x for x, _y in points) - min(x for x, _y in points)
    height = max(y for _x, y in points) - min(y for _x, y in points)
    _add_ink_wire(parent, name, geom, color, (width, height, thickness), pos, hpr)
    return node_path


def weapon_glow_color(weapon: Optional[Weapon]) -> Tuple[float, float, float, float]:
    if weapon is None:
        return DEFAULT_WEAPON_COLOR

    for enchantment in weapon.enchantments:
        if enchantment.key in ENCHANTMENT_GLOW_COLORS:
            return ENCHANTMENT_GLOW_COLORS[enchantment.key]

    return DEFAULT_WEAPON_COLOR


def _tree_asset_name(name: str) -> str:
    stable_index = sum(ord(char) for char in name)
    if "snow" in name or "frost" in name:
        models = SNOW_TREE_MODELS
    elif "treasure" in name or stable_index % 7 == 0:
        models = TWISTED_TREE_MODELS
    elif "border" in name and stable_index % 3 == 0:
        models = PINE_TREE_MODELS
    else:
        models = COMMON_TREE_MODELS
    return models[stable_index % len(models)]


def _tree_asset_scale(asset_name: str, scale: float) -> float:
    if asset_name.startswith("Willow"):
        return 0.72 * scale
    if "Dead" in asset_name:
        return 0.78 * scale
    if asset_name.startswith("PineTree"):
        return 0.7 * scale
    return 0.76 * scale


def _load_obj_asset(asset_dir: Path, asset_name: str):
    cache_key = (str(asset_dir), asset_name)
    if cache_key in ASSET_MODEL_CACHE:
        return ASSET_MODEL_CACHE[cache_key]
    loader = getattr(builtins, "loader", None)
    if loader is None:
        return None

    model_path = asset_dir / f"{asset_name}.obj"
    if not model_path.exists():
        ASSET_MODEL_CACHE[cache_key] = None
        return None

    try:
        model = loader.loadModel(str(model_path))
    except OSError:
        ASSET_MODEL_CACHE[cache_key] = None
        return None
    if model.isEmpty():
        ASSET_MODEL_CACHE[cache_key] = None
        return None

    ASSET_MODEL_CACHE[cache_key] = model
    return model


def _load_tree_asset(asset_name: str):
    return _load_obj_asset(QUATERNIUS_NATURE_ASSET_DIR, asset_name)


def _copy_imported_model(
    parent,
    name: str,
    asset_dir: Path,
    asset_name: str,
    scale: float,
    pos: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    hpr: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    color_scale: Optional[Tuple[float, float, float, float]] = None,
    ink: bool = True,
):
    template = _load_obj_asset(asset_dir, asset_name)
    if template is None:
        return None

    root = parent.attachNewNode(name)
    root.setPos(*pos)
    root.setHpr(*hpr)
    root.setScale(scale)
    model = template.copyTo(root)
    model.setTwoSided(True)
    if color_scale is not None:
        model.setColorScale(*color_scale)

    if ink and CEL_INK_ENABLED:
        ink_model = template.copyTo(root)
        ink_model.setTwoSided(True)
        ink_model.setColor(*CEL_INK_COLOR)
        ink_model.setColorScale(*CEL_INK_COLOR)
        ink_model.setRenderModeWireframe()
        ink_model.setRenderModeThickness(CEL_INK_THICKNESS)
        ink_model.setDepthOffset(-2)
        ink_model.setLightOff(1)
    return root


def make_tree(parent, name: str, pos: Tuple[float, float, float], scale: float = 1.0):
    root = parent.attachNewNode(name)
    root.setPos(*pos)
    root.setH((sum(ord(char) for char in name) * 13) % 360)
    asset_name = _tree_asset_name(name)
    asset_template = _load_tree_asset(asset_name)
    if asset_template is not None:
        make_box(
            root,
            "tree-shadow",
            (1.4 * scale, 0.92 * scale, 0.035),
            (0.02, 0.04, 0.02, 0.28),
            (0.08 * scale, -0.04 * scale, 0.01),
            (0, 0, 12),
        )
        tree = asset_template.copyTo(root)
        asset_scale = _tree_asset_scale(asset_name, scale)
        tree.setScale(asset_scale)
        tree.setP(90)
        tree.setZ(0.08 * scale)
        tree.setTwoSided(True)
        if CEL_INK_ENABLED:
            tree_ink = asset_template.copyTo(root)
            tree_ink.setScale(asset_scale)
            tree_ink.setP(90)
            tree_ink.setZ(0.08 * scale)
            tree_ink.setTwoSided(True)
            tree_ink.setColor(*CEL_INK_COLOR)
            tree_ink.setColorScale(*CEL_INK_COLOR)
            tree_ink.setRenderModeWireframe()
            tree_ink.setRenderModeThickness(1.35)
            tree_ink.setDepthOffset(-2)
            tree_ink.setLightOff(1)
        return root

    make_box(
        root,
        "tree-shadow",
        (1.25 * scale, 0.8 * scale, 0.035),
        (0.02, 0.04, 0.02, 0.28),
        (0.1 * scale, -0.06 * scale, 0.01),
        (0, 0, 12),
    )
    make_box(
        root,
        "trunk",
        (0.28 * scale, 0.28 * scale, 1.35 * scale),
        (0.26, 0.13, 0.06, 1),
        (0, 0, 0.68 * scale),
    )
    make_box(
        root,
        "canopy-low",
        (1.25 * scale, 1.05 * scale, 0.78 * scale),
        (0.08, 0.33, 0.13, 1),
        (0, 0, 1.58 * scale),
        (0, 0, -10),
    )
    make_box(
        root,
        "canopy-mid",
        (0.96 * scale, 0.9 * scale, 0.72 * scale),
        (0.11, 0.43, 0.18, 1),
        (-0.12 * scale, 0.08 * scale, 2.02 * scale),
        (0, 0, 18),
    )
    make_box(
        root,
        "canopy-top",
        (0.66 * scale, 0.62 * scale, 0.58 * scale),
        (0.16, 0.54, 0.22, 1),
        (0.08 * scale, -0.03 * scale, 2.42 * scale),
        (0, 0, -5),
    )
    return root


class SwordfishGame(ShowBase):
    def __init__(self):
        super().__init__()

        props = WindowProperties()
        props.setTitle("Swordfish - Panda3D Vertical Slice")
        if self.win is not None:
            self.win.requestProperties(props)

        self.disableMouse()
        self.setBackgroundColor(0.035, 0.08, 0.055, 1)

        self.rng = random.Random()
        self.keys = {"w": False, "a": False, "s": False, "d": False}
        self.sprint_held = False
        self.fishing_spot = Vec3(0, 7.0, 0)
        self.cave_fishing_spot = Vec3(CAVE_POOL_SPOT)
        self.level2_fishing_spot = Vec3(LEVEL2_LAKE_SPOT)
        self.active_fishing_spot_name = "lake"
        self.fishing_state = "idle"
        self.fishing_timer = 0.0
        self.fishing_phase = 0.0
        self.water_bump_cooldown = 0.0
        self.cast_start_pos = Vec3(0, 0, 0)
        self.cast_target_pos = Vec3(0, 0, 0)
        self.bobber_node = None
        self.cast_line_node = None
        self.cast_line_segment = None
        self.fishing_ripples = []
        self.current_weapon: Optional[Weapon] = None
        self.gold = 0
        self.rod_tier = 0
        self.shop_spot = Vec3(SHOP_SPOT)
        self.player_hp = 50
        self.player_max_hp = 50
        self.hp_regen_cooldown = 0.0
        self.hp_regen_timer = 0.0
        self.player_stamina = 100.0
        self.player_max_stamina = 100.0
        self.stamina_regen_cooldown = 0.0
        self.death_timer = 0.0
        self.death_duration = 2.25
        self.is_death_sequence = False
        self.attack_cooldown = 0.0
        self.weapon_ability_cooldown = 0.0
        self.dodge_time = 0.0
        self.dodge_cooldown = 0.0
        self.dodge_direction = Vec3(0, 1, 0)
        self.fish_count = 0
        self.enemies: List[SceneEnemy] = []
        self.attack_token_holder: Optional[SceneEnemy] = None
        self.attack_token_cooldown = 0.0
        self.attack_token_timer = 0.0
        self.mob_respawn_timer = MOB_RESPAWN_INTERVAL
        self.chests: List[SceneChest] = []
        self.hit_effects: List[HitEffect] = []
        self.ranged_shots: List[RangedShot] = []
        self.animated_details: List[AnimatedDetail] = []
        self.log_lines: List[str] = []
        self.swing_time = 0.0
        self.swing_duration = 0.34
        self.swing_is_powered = False
        self.swing_style = "horizontal"
        self.next_swing_vertical = False
        self.swing_spark_timer = 0.0
        self.swing_sparked = False
        self.walk_time = 0.0
        self.is_player_moving = False
        self.is_sprinting = False
        self.sprint_dust_timer = 0.0
        self.left_arm = None
        self.right_arm = None
        self.left_leg = None
        self.right_leg = None
        self.weapon_pivot = None
        self.weapon_root = None
        self.player_visual_model = None
        self.pet = None
        self.pet_visual = None
        self.pet_head = None
        self.pet_tail = None
        self.pet_left_foot = None
        self.pet_right_foot = None
        self.pet_attack_cooldown = 0.0
        self.pet_walk_time = 0.0
        self.slash_root = None
        self.slash_parts = []
        self.slash_part_base_positions = []
        self.catch_banner_timer = 0.0
        self.catch_banner_text = ""
        self.inspect_open = False
        self.inspect_frame = None
        self.inspect_title = None
        self.inspect_body = None
        self.inspect_preview_root = None
        self.inspect_preview_model = None
        self.inspect_preview_weapon = None
        self.health_bar_fill = None
        self.health_bar_text = None
        self.stamina_bar_fill = None
        self.stamina_bar_text = None
        self.shop_open = False
        self.shop_frame = None
        self.shop_title = None
        self.shop_body = None
        self.forge_open = False
        self.forge_frame = None
        self.forge_title = None
        self.forge_body = None
        self.player_armor_value = 0
        self.player_armor_tier = -1
        self.boss_alive = False

        self._bind_controls()
        self._build_world()
        self._build_player()
        self._build_pet()
        self._build_lights()
        self._build_ui()
        self.spawn_rabbits(4)
        self._spawn_field_mobs()
        self._log("You arrive at the old lake with an empty hand.")
        self._log("The rod shop buys courage with coins from the arena.")
        self._log("Fish up a weapon, then test it in the arena.")

        self.taskMgr.add(self._update, "update")

    def _bind_controls(self):
        for key in self.keys:
            self.accept(key, self._set_key, [key, True])
            self.accept(f"{key}-up", self._set_key, [key, False])

        self.accept("e", self.handle_interact)
        self.accept("i", self.toggle_inspection)
        self.accept("space", self.attack)
        self.accept("q", self.use_weapon_ability)
        self.accept("shift", self._set_sprint, [True])
        self.accept("shift-up", self._set_sprint, [False])
        self.accept("control", self.dodge)
        self.accept("lcontrol", self.dodge)
        self.accept("rcontrol", self.dodge)
        self.accept("m", self.spawn_monster)
        for index in range(1, 8):
            self.accept(str(index), self._select_menu_item, [index - 1])
        self.accept("escape", self.userExit)

    def _set_key(self, key: str, value: bool):
        self.keys[key] = value

    def _set_sprint(self, value: bool):
        self.sprint_held = value

    def _build_world(self):
        make_box(
            self.render,
            "distant-forest-ground",
            (FOREST_GROUND, FOREST_GROUND, 0.08),
            (0.025, 0.09, 0.045, 1),
            (0, 0, -0.16),
        )
        make_box(
            self.render,
            "ground",
            (FOREST_EDGE * 2 + 8, FOREST_EDGE * 2 + 8, 0.1),
            (0.14, 0.29, 0.16, 1),
            (0, 0, -0.08),
        )
        self._build_ground_layers()
        self._build_border_forest()
        self._build_shading_details()
        make_flat_blob(
            self.render,
            "muddy-lake-bank",
            (0, 9.6, -0.025),
            13.6,
            7.25,
            (0.23, 0.22, 0.13, 1),
            points=34,
            wobble=0.2,
            rotation_degrees=-4,
            seed=11,
        )
        make_flat_blob(
            self.render,
            "ancient-lake",
            (0, 9.7, 0.015),
            12.1,
            6.15,
            (0.08, 0.32, 0.64, 0.82),
            points=36,
            wobble=0.17,
            rotation_degrees=-5,
            seed=21,
        )
        make_flat_blob(
            self.render,
            "west-cove",
            (-8.2, 9.5, 0.025),
            4.3,
            3.45,
            (0.07, 0.26, 0.52, 0.72),
            points=24,
            wobble=0.22,
            rotation_degrees=-8,
            seed=31,
        )
        make_flat_blob(
            self.render,
            "east-cove",
            (8.4, 10.2, 0.026),
            3.85,
            3.05,
            (0.06, 0.29, 0.58, 0.68),
            points=24,
            wobble=0.2,
            rotation_degrees=10,
            seed=41,
        )
        make_flat_blob(
            self.render,
            "deep-water",
            (-1.4, 10.4, 0.055),
            4.8,
            2.65,
            (0.03, 0.13, 0.32, 0.74),
            points=24,
            wobble=0.12,
            rotation_degrees=-4,
            seed=51,
        )
        make_flat_blob(
            self.render,
            "shallow-water-south",
            (0.2, 4.7, 0.065),
            9.5,
            1.35,
            (0.16, 0.5, 0.74, 0.42),
            points=26,
            wobble=0.2,
            rotation_degrees=1,
            seed=61,
        )
        make_flat_blob(
            self.render,
            "shallow-water-north",
            (-1.0, 15.0, 0.066),
            7.5,
            1.25,
            (0.13, 0.45, 0.68, 0.38),
            points=24,
            wobble=0.18,
            rotation_degrees=5,
            seed=71,
        )
        for index, (x, y, sx, sy, shade) in enumerate(
            (
                (-6.4, 6.6, 4.8, 0.12, 0.58),
                (-0.8, 8.2, 6.2, 0.1, 0.66),
                (5.6, 9.7, 5.2, 0.12, 0.6),
                (-3.2, 12.6, 5.6, 0.1, 0.54),
                (4.2, 14.0, 4.4, 0.1, 0.62),
            )
        ):
            make_box(
                self.render,
                f"lake-ripple-{index}",
                (sx, sy, 0.04),
                (0.55, 0.82, 1.0, shade),
                (x, y, 0.1),
                (0, 0, self.rng.uniform(-12, 12)),
            )
        for index, (x, y, sx, sy) in enumerate(
            (
                (-10.8, 4.2, 4.2, 1.2),
                (-6.0, 3.2, 5.0, 1.0),
                (5.7, 3.2, 4.8, 1.0),
                (11.0, 5.1, 3.8, 1.4),
                (-11.7, 14.2, 3.2, 1.2),
                (10.4, 14.8, 4.4, 1.1),
            )
        ):
            make_flat_blob(
                self.render,
                f"muddy-shore-{index}",
                (x, y, -0.01),
                sx * 0.5,
                sy * 0.5,
                (0.25, 0.23, 0.13, 1),
                points=14,
                wobble=0.24,
                rotation_degrees=self.rng.uniform(-18, 18),
                seed=80 + index,
            )
        make_box(
            self.render,
            "dock",
            (3.2, 4.2, 0.18),
            (0.45, 0.28, 0.14, 1),
            (0, 4.8, 0.03),
        )
        for index, (x, y, height, lean) in enumerate(
            (
                (-7.0, 6.0, 1.2, -10),
                (-6.4, 10.8, 0.9, 8),
                (-3.4, 12.5, 1.1, -6),
                (3.2, 12.2, 1.0, 12),
                (6.8, 10.2, 1.3, -8),
                (7.3, 6.8, 0.95, 10),
            )
        ):
            make_box(
                self.render,
                f"lake-reed-{index}",
                (0.08, 0.08, height),
                (0.16, 0.43, 0.19, 1),
                (x, y, height / 2),
                (0, lean, 0),
            )
        for index, (x, y, sx, sy) in enumerate(
            (
                (-5.4, 3.7, 0.8, 0.55),
                (4.9, 4.1, 0.65, 0.45),
                (-8.2, 8.4, 0.55, 0.75),
                (8.0, 9.8, 0.7, 0.5),
            )
        ):
            make_box(
                self.render,
                f"lake-stone-{index}",
                (sx, sy, 0.24),
                (0.34, 0.36, 0.34, 1),
                (x, y, 0.09),
            )

        for index, (x, y, scale) in enumerate(
            (
                (-13.4, 5.0, 1.05),
                (-14.6, 9.1, 0.86),
                (-12.4, 13.6, 1.18),
                (-8.8, 16.2, 0.92),
                (-4.0, 17.2, 1.08),
                (1.4, 17.4, 0.95),
                (5.6, 16.8, 1.16),
                (10.0, 15.8, 0.9),
                (13.5, 12.2, 1.08),
                (14.4, 8.2, 0.88),
                (12.6, 4.4, 1.0),
                (-9.5, 2.2, 0.82),
                (8.6, 2.0, 0.84),
            )
        ):
            tree = make_tree(self.render, f"lake-tree-{index}", (x, y, 0), scale)
            tree.setH(self.rng.uniform(-18, 18))

        self._build_shop()
        self._build_forge()
        self._build_boss_arena()
        self._build_world_details()
        self._build_treasure_map()
        self._build_field_chests()
        self._build_cave_area()
        self._build_frost_biome()
        self._build_sunken_meadow_biome()
        self._build_level2_zone()
        self._build_extra_nature()

        fence_color = (0.36, 0.27, 0.18, 1)
        make_box(self.render, "arena-back", (18, 0.35, 0.55), fence_color, (0, -14, 0.2))
        make_box(self.render, "arena-front", (18, 0.35, 0.55), fence_color, (0, -3.8, 0.2))
        make_box(self.render, "arena-left", (0.35, 10.5, 0.55), fence_color, (-9, -8.9, 0.2))
        make_box(self.render, "arena-right", (0.35, 10.5, 0.55), fence_color, (9, -8.9, 0.2))
        make_box(
            self.render,
            "arena-floor",
            (17.2, 9.6, 0.06),
            (0.31, 0.25, 0.18, 1),
            (0, -8.9, 0.0),
        )

    def _build_ground_layers(self):
        make_flat_blob(
            self.render,
            "warm-grass-center",
            (0, -1.1, -0.045),
            13.5,
            8.0,
            (0.18, 0.36, 0.18, 1),
            points=24,
            wobble=0.17,
            rotation_degrees=-6,
            seed=120,
        )
        make_flat_blob(
            self.render,
            "dark-forest-edge-west",
            (-16.5, 4.5, -0.035),
            5.0,
            15.5,
            (0.08, 0.2, 0.11, 1),
            points=20,
            wobble=0.24,
            rotation_degrees=2,
            seed=121,
        )
        make_flat_blob(
            self.render,
            "dark-forest-edge-east",
            (16.3, 4.0, -0.034),
            5.4,
            15.5,
            (0.08, 0.21, 0.12, 1),
            points=20,
            wobble=0.24,
            rotation_degrees=-3,
            seed=122,
        )
        make_flat_blob(
            self.render,
            "dock-footpath",
            (0.0, 2.0, -0.015),
            2.25,
            5.2,
            (0.35, 0.29, 0.16, 1),
            points=18,
            wobble=0.12,
            rotation_degrees=2,
            seed=123,
        )
        make_flat_blob(
            self.render,
            "shop-footpath",
            (-6.0, 1.6, -0.012),
            5.6,
            1.05,
            (0.34, 0.27, 0.15, 1),
            points=18,
            wobble=0.16,
            rotation_degrees=-4,
            seed=124,
        )
        make_flat_blob(
            self.render,
            "arena-approach-path",
            (0.0, -3.05, -0.01),
            3.7,
            1.35,
            (0.33, 0.25, 0.14, 1),
            points=18,
            wobble=0.13,
            rotation_degrees=0,
            seed=125,
        )

    def _build_border_forest(self):
        rng = random.Random(260531)
        forest_floor = (0.045, 0.13, 0.07, 1)
        shadow_green = (0.035, 0.1, 0.05, 1)
        far_green = (0.025, 0.075, 0.04, 1)
        far_canopy = (0.04, 0.16, 0.075, 1)

        edge = FOREST_EDGE
        span = edge * 2.0 + 12.0
        floor_at = edge - 2.0
        wall_at = edge + 0.2

        for name, size, pos in (
            ("forest-floor-west", (5.4, span, 0.06), (-floor_at, 0.0, -0.035)),
            ("forest-floor-east", (5.4, span, 0.06), (floor_at, 0.0, -0.035)),
            ("forest-floor-north", (span, 5.4, 0.06), (0.0, floor_at, -0.034)),
            ("forest-floor-south", (span, 5.4, 0.06), (0.0, -floor_at, -0.034)),
        ):
            make_box(self.render, name, size, forest_floor, pos)

        for name, size, pos in (
            ("distant-forest-wall-north", (span + 2.0, 0.7, 5.4), (0.0, wall_at, 2.55)),
            ("distant-forest-wall-south", (span + 2.0, 0.7, 5.4), (0.0, -wall_at, 2.55)),
            ("distant-forest-wall-west", (0.7, span + 2.0, 5.4), (-wall_at, 0.0, 2.55)),
            ("distant-forest-wall-east", (0.7, span + 2.0, 5.4), (wall_at, 0.0, 2.55)),
        ):
            make_box(self.render, name, size, far_green, pos)

        canopy_count = int(span / 1.55)
        canopy_start = -span / 2.0
        canopy_at = edge - 0.15
        for index in range(canopy_count):
            offset = canopy_start + index * 1.55
            canopy_width = rng.uniform(1.0, 2.0)
            canopy_height = rng.uniform(1.5, 2.7)
            jitter = rng.uniform(-0.25, 0.25)
            lift = 4.0 + canopy_height * 0.18
            make_box(
                self.render,
                f"north-distant-canopy-{index}",
                (canopy_width, 0.8, canopy_height),
                far_canopy,
                (offset + jitter, canopy_at, lift),
                (0, 0, rng.uniform(-6, 6)),
            )
            make_box(
                self.render,
                f"south-distant-canopy-{index}",
                (canopy_width, 0.8, canopy_height),
                far_canopy,
                (offset + jitter, -canopy_at, lift),
                (0, 0, rng.uniform(-6, 6)),
            )
            make_box(
                self.render,
                f"west-distant-canopy-{index}",
                (0.8, canopy_width, canopy_height),
                far_canopy,
                (-canopy_at, offset + jitter, lift),
                (0, 0, rng.uniform(-6, 6)),
            )
            make_box(
                self.render,
                f"east-distant-canopy-{index}",
                (0.8, canopy_width, canopy_height),
                far_canopy,
                (canopy_at, offset + jitter, lift),
                (0, 0, rng.uniform(-6, 6)),
            )

        # Scatter trees and shrubs across the open field, skipping the central
        # region that already holds the lake, arena, shop, and treasure clearing.
        def in_central_keep_clear(px: float, py: float) -> bool:
            in_hub = -32.0 < px < 36.0 and -40.0 < py < 22.0
            in_frost = (
                FROST_BIOME_BOUNDS[0] - 5.0 < px < FROST_BIOME_BOUNDS[1] + 5.0
                and FROST_BIOME_BOUNDS[2] - 5.0 < py < FROST_BIOME_BOUNDS[3] + 5.0
            )
            in_sunken_meadow = (
                SUNKEN_MEADOW_BOUNDS[0] - 5.0 < px < SUNKEN_MEADOW_BOUNDS[1] + 5.0
                and SUNKEN_MEADOW_BOUNDS[2] - 5.0 < py < SUNKEN_MEADOW_BOUNDS[3] + 5.0
            )
            in_level2 = (
                LEVEL2_ZONE_BOUNDS[0] - 8.0 < px < LEVEL2_ZONE_BOUNDS[1] + 8.0
                and LEVEL2_ZONE_BOUNDS[2] - 8.0 < py < LEVEL2_ZONE_BOUNDS[3] + 8.0
            )
            return in_hub or in_frost or in_sunken_meadow or in_level2

        scatter_limit = edge - 4.0
        tree_index = 0
        for _ in range(520):
            x = rng.uniform(-scatter_limit, scatter_limit)
            y = rng.uniform(-scatter_limit, scatter_limit)
            if in_central_keep_clear(x, y):
                continue
            tree = make_tree(
                self.render, f"border-forest-tree-{tree_index}", (x, y, 0), rng.uniform(0.72, 1.5)
            )
            tree.setH(rng.uniform(-25, 25))
            tree_index += 1

        shrub_index = 0
        for _ in range(420):
            x = rng.uniform(-scatter_limit, scatter_limit)
            y = rng.uniform(-scatter_limit, scatter_limit)
            if in_central_keep_clear(x, y):
                continue
            width = rng.uniform(0.55, 1.1)
            height = rng.uniform(0.25, 0.48)
            color = forest_floor if shrub_index % 3 else shadow_green
            make_box(
                self.render,
                f"border-forest-shrub-{shrub_index}",
                (width, rng.uniform(0.4, 0.9), height),
                color,
                (x, y, height * 0.5),
                (0, 0, rng.uniform(-25, 25)),
            )
            shrub_index += 1

    def _build_shading_details(self):
        rng = random.Random(260533)

        for index, (x, y, sx, sy, rotation, alpha) in enumerate(
            (
                (-13.5, 5.0, 6.6, 12.8, -4, 0.22),
                (14.0, 3.8, 6.4, 12.0, 3, 0.2),
                (0.0, 18.0, 18.0, 2.6, 1, 0.18),
                (0.0, -18.2, 18.0, 2.8, -2, 0.18),
                (22.0, -27.0, 10.0, 6.4, 8, 0.12),
                (-38.0, 38.0, 8.2, 8.2, 0, 0.18),
            )
        ):
            make_flat_blob(
                self.render,
                f"broad-ground-shade-{index}",
                (x, y, 0.018),
                sx,
                sy,
                (0.01, 0.02, 0.012, alpha),
                points=22,
                wobble=0.18,
                rotation_degrees=rotation,
                seed=450 + index,
            )

        for index, (x, y, sx, sy, rotation) in enumerate(
            (
                (-10.4, 1.7, 3.6, 2.2, 8),
                (6.5, 4.5, 3.1, 2.0, -8),
                (0.0, 4.8, 2.8, 3.8, 0),
                (0.0, -8.9, 8.8, 5.0, 0),
                (16.8, -24.0, 2.0, 1.2, -10),
                (24.8, -25.8, 2.0, 1.2, 14),
                (21.5, -31.0, 2.0, 1.2, -6),
            )
        ):
            make_flat_blob(
                self.render,
                f"object-ground-shade-{index}",
                (x + 0.28, y - 0.22, 0.035),
                sx,
                sy,
                (0.0, 0.0, 0.0, 0.2),
                points=16,
                wobble=0.12,
                rotation_degrees=rotation,
                seed=500 + index,
            )

        for index in range(34):
            side = index % 4
            if side == 0:
                x = rng.uniform(-32.0, 32.0)
                y = rng.uniform(21.0, 34.0)
            elif side == 1:
                x = rng.uniform(-32.0, 32.0)
                y = rng.uniform(-34.0, -21.0)
            elif side == 2:
                x = rng.uniform(-34.0, -21.0)
                y = rng.uniform(-32.0, 32.0)
            else:
                x = rng.uniform(21.0, 34.0)
                y = rng.uniform(-32.0, 32.0)
            make_flat_blob(
                self.render,
                f"forest-canopy-shadow-{index}",
                (x, y, 0.025),
                rng.uniform(1.2, 2.6),
                rng.uniform(0.7, 1.6),
                (0.0, 0.015, 0.006, rng.uniform(0.14, 0.24)),
                points=12,
                wobble=0.25,
                rotation_degrees=rng.uniform(0, 180),
                seed=560 + index,
            )

    def _build_treasure_map(self):
        rng = random.Random(260532)
        path_color = (0.34, 0.25, 0.13, 1)
        clearing_color = (0.12, 0.25, 0.12, 1)

        make_flat_blob(
            self.render,
            "treasure-map-path-start",
            (7.6, -15.8, -0.006),
            4.8,
            1.15,
            path_color,
            points=18,
            wobble=0.16,
            rotation_degrees=-25,
            seed=190,
        )
        make_flat_blob(
            self.render,
            "treasure-map-path-bend",
            (13.6, -19.2, -0.005),
            6.3,
            1.25,
            path_color,
            points=18,
            wobble=0.17,
            rotation_degrees=-34,
            seed=191,
        )
        make_flat_blob(
            self.render,
            "treasure-map-path-deep",
            (18.4, -23.4, -0.004),
            5.6,
            1.35,
            path_color,
            points=18,
            wobble=0.15,
            rotation_degrees=-48,
            seed=192,
        )
        make_flat_blob(
            self.render,
            "treasure-map-clearing",
            (22.0, -27.0, -0.003),
            10.4,
            7.1,
            clearing_color,
            points=28,
            wobble=0.2,
            rotation_degrees=8,
            seed=193,
        )

        for index, (x, y, scale) in enumerate(
            (
                (13.2, -22.4, 0.86),
                (15.4, -18.4, 0.78),
                (17.0, -32.6, 0.92),
                (20.2, -19.2, 0.84),
                (23.9, -18.4, 1.05),
                (27.8, -20.2, 0.9),
                (30.4, -24.8, 1.12),
                (29.4, -30.2, 0.94),
                (25.6, -33.0, 1.08),
                (19.4, -34.0, 0.82),
                (12.2, -28.0, 0.9),
            )
        ):
            tree = make_tree(self.render, f"treasure-map-tree-{index}", (x, y, 0), scale)
            tree.setH(rng.uniform(-22, 22))

        for index in range(26):
            x = rng.uniform(12.2, 31.0)
            y = rng.uniform(-33.2, -18.6)
            if 17.0 < x < 27.8 and -31.6 < y < -22.0:
                continue
            make_box(
                self.render,
                f"treasure-map-brush-{index}",
                (rng.uniform(0.35, 0.8), rng.uniform(0.28, 0.72), rng.uniform(0.18, 0.38)),
                rng.choice(((0.08, 0.21, 0.09, 1), (0.11, 0.28, 0.12, 1), (0.18, 0.24, 0.1, 1))),
                (x, y, 0.16),
                (0, 0, rng.uniform(0, 360)),
            )

        make_box(self.render, "treasure-map-sign-post", (0.12, 0.12, 1.1), (0.19, 0.1, 0.04, 1), (8.8, -16.0, 0.55), (0, 0, -15))
        make_box(self.render, "treasure-map-sign-board", (1.2, 0.12, 0.42), (0.32, 0.18, 0.07, 1), (8.9, -16.2, 1.1), (0, 0, -15))
        make_box(self.render, "treasure-map-sign-arrow", (0.42, 0.1, 0.24), (0.8, 0.58, 0.24, 1), (9.52, -16.38, 1.1), (0, 0, -15))

        chest_specs = (
            ("Mossy Training Chest", Vec3(16.8, -24.0, 0), 12, "rabbit"),
            ("Sunken Captain's Chest", Vec3(24.8, -25.8, 0), 18, "mixed"),
            ("Old King Chest", Vec3(21.5, -31.0, 0), 26, "monster"),
        )
        for index, (name, pos, reward, guard_kind) in enumerate(chest_specs):
            chest = self._make_chest(index, name, pos, reward, guard_kind)
            self.chests.append(chest)
            self._spawn_chest_guards(index, pos, guard_kind)

    def _build_field_chests(self):
        field_chest_specs = (
            ("Windswept Chest", Vec3(-48, 36, 0), 14, "bird"),
            ("Boar Den Chest", Vec3(50, 40, 0), 22, "boar"),
            ("Overgrown Chest", Vec3(-44, -50, 0), 16, "rabbit"),
            ("Hollow Stump Cache", Vec3(46, -46, 0), 20, "mixed"),
            ("Forgotten Hoard", Vec3(-50, -10, 0), 28, "monster"),
            ("Far North Cache", Vec3(-72, 70, 0), 34, "wisp"),
            ("Old Ranger Chest", Vec3(80, -72, 0), 38, "bird"),
            ("Southern Root Hoard", Vec3(-76, -74, 0), 40, "boar"),
            ("Eastern Moss Lockbox", Vec3(78, 12, 0), 32, "snapper"),
            ("Far Western Lockbox", Vec3(-112, -18, 0), 44, "rabbit"),
            ("Northwatch Chest", Vec3(16, 116, 0), 48, "wisp"),
            ("Long Road Cache", Vec3(112, -104, 0), 52, "boar"),
            ("Old Orchard Chest", Vec3(-116, 116, 0), 56, "bird"),
        )
        for index, (name, pos, reward, guard_kind) in enumerate(field_chest_specs):
            chest_index = 10 + index
            bounds = (pos.getX() - 8, pos.getX() + 8, pos.getY() - 8, pos.getY() + 8)
            make_flat_blob(
                self.render, f"field-clearing-{index}", (pos.getX(), pos.getY(), -0.006),
                5.4, 4.2, (0.12, 0.25, 0.12, 1),
                points=18, wobble=0.2, rotation_degrees=index * 45, seed=300 + index,
            )
            chest = self._make_chest(chest_index, name, pos, reward, guard_kind, bounds)
            self.chests.append(chest)
            self._spawn_chest_guards(chest_index, pos, guard_kind, bounds=bounds)

    def _build_cave_area(self):
        rng = random.Random(260534)
        path_color = (0.22, 0.19, 0.17, 1)
        cave_floor = (0.075, 0.085, 0.088, 1)
        dark_rock = (0.06, 0.065, 0.07, 1)
        rock = (0.18, 0.18, 0.18, 1)
        glow_blue = (0.2, 0.75, 1.0, 0.58)

        make_flat_blob(
            self.render,
            "cave-path",
            (-23.5, -29.8, -0.004),
            7.0,
            1.35,
            path_color,
            points=18,
            wobble=0.2,
            rotation_degrees=-35,
            seed=610,
        )
        make_flat_blob(
            self.render,
            "cave-floor",
            (-31.6, -37.0, -0.003),
            11.2,
            9.0,
            cave_floor,
            points=30,
            wobble=0.24,
            rotation_degrees=12,
            seed=611,
        )
        make_flat_blob(
            self.render,
            "cave-pool-bank",
            (CAVE_POOL_CENTER.getX(), CAVE_POOL_CENTER.getY(), -0.001),
            5.6,
            3.6,
            (0.12, 0.11, 0.1, 1),
            points=22,
            wobble=0.22,
            rotation_degrees=-8,
            seed=612,
        )
        make_flat_blob(
            self.render,
            "cave-fishing-pool",
            (CAVE_POOL_CENTER.getX(), CAVE_POOL_CENTER.getY(), 0.025),
            4.5,
            2.75,
            (0.02, 0.2, 0.34, 0.82),
            points=28,
            wobble=0.18,
            rotation_degrees=-8,
            seed=613,
        )
        make_flat_blob(
            self.render,
            "cave-pool-glow",
            (CAVE_POOL_CENTER.getX(), CAVE_POOL_CENTER.getY(), 0.06),
            3.2,
            1.7,
            (0.24, 0.76, 1.0, 0.3),
            points=20,
            wobble=0.12,
            rotation_degrees=-10,
            seed=614,
        )

        for index, (x, y, sx, sy, height) in enumerate(
            (
                (-41.0, -32.5, 1.8, 1.2, 2.0),
                (-39.2, -42.8, 2.0, 1.1, 2.2),
                (-33.0, -47.0, 2.4, 1.1, 1.9),
                (-24.2, -44.2, 1.8, 1.3, 2.1),
                (-22.4, -35.0, 1.6, 1.4, 1.8),
                (-28.2, -28.0, 2.2, 1.0, 2.0),
            )
        ):
            make_box(
                self.render,
                f"cave-wall-rock-{index}",
                (sx, sy, height),
                dark_rock if index % 2 else rock,
                (x, y, height / 2),
                (0, 0, rng.uniform(-18, 18)),
            )

        make_box(self.render, "cave-mouth-left", (1.2, 1.1, 2.7), dark_rock, (-37.8, -30.4, 1.35), (0, 0, -12))
        make_box(self.render, "cave-mouth-right", (1.2, 1.1, 2.7), dark_rock, (-33.2, -30.1, 1.35), (0, 0, 10))
        make_box(self.render, "cave-mouth-top", (5.4, 1.0, 1.2), dark_rock, (-35.5, -30.0, 2.65), (0, 0, 2))
        make_box(self.render, "cave-mouth-dark", (3.4, 0.28, 1.8), (0.005, 0.006, 0.008, 1), (-35.5, -29.58, 1.18))

        for index, (x, y, h, color) in enumerate(
            (
                (-35.8, -35.4, 0.8, glow_blue),
                (-28.4, -39.8, 1.0, (0.42, 0.95, 0.68, 0.52)),
                (-38.2, -40.5, 0.7, (0.72, 0.55, 1.0, 0.5)),
                (-25.6, -32.4, 0.75, glow_blue),
            )
        ):
            crystal = make_box(
                self.render,
                f"cave-crystal-{index}",
                (0.24, 0.24, h),
                color,
                (x, y, h / 2),
                (0, 0, rng.uniform(0, 45)),
            )
            self._add_animated_detail(crystal, bob_amount=0.025, sway_amount=0.0, speed=1.9, phase=index)

        for index in range(18):
            x = rng.uniform(CAVE_BOUNDS[0], CAVE_BOUNDS[1])
            y = rng.uniform(CAVE_BOUNDS[2], CAVE_BOUNDS[3])
            if (Vec3(x, y, 0) - CAVE_POOL_CENTER).length() < 4.8:
                continue
            make_box(
                self.render,
                f"cave-small-rock-{index}",
                (rng.uniform(0.18, 0.5), rng.uniform(0.16, 0.44), rng.uniform(0.12, 0.32)),
                rng.choice((rock, dark_rock, (0.12, 0.13, 0.13, 1))),
                (x, y, 0.09),
                (0, 0, rng.uniform(0, 360)),
            )

        cave_chests = (
            ("Crystal Cave Chest", Vec3(-37.0, -36.2, 0), 30, "wisp"),
            ("Deep Pool Cache", Vec3(-28.0, -42.0, 0), 34, "snapper"),
            ("Buried Cave Hoard", Vec3(-24.8, -34.0, 0), 42, "mixed"),
        )
        for index, (name, pos, reward, guard_kind) in enumerate(cave_chests):
            chest_index = 30 + index
            chest = self._make_chest(chest_index, name, pos, reward, guard_kind, CAVE_BOUNDS)
            self.chests.append(chest)
            self._spawn_chest_guards(chest_index, pos, guard_kind, bounds=CAVE_BOUNDS)

    def _build_frost_biome(self):
        rng = random.Random(260535)
        path_color = (0.28, 0.31, 0.3, 1)
        snow = (0.72, 0.83, 0.86, 1)
        blue_snow = (0.55, 0.73, 0.82, 1)
        ice = (0.42, 0.72, 0.92, 0.62)
        dark_ice = (0.14, 0.28, 0.38, 0.72)
        dead_wood = (0.2, 0.18, 0.16, 1)

        for index, (x, y, sx, sy, rotation) in enumerate(
            (
                (29.0, 25.5, 8.4, 1.25, 38),
                (39.0, 34.0, 8.8, 1.25, 42),
                (49.0, 43.5, 9.2, 1.35, 45),
                (58.5, 53.0, 9.0, 1.35, 44),
                (70.0, 64.0, 10.0, 1.35, 42),
                (84.0, 77.0, 9.4, 1.3, 38),
            )
        ):
            make_flat_blob(
                self.render,
                f"frost-road-{index}",
                (x, y, -0.007),
                sx,
                sy,
                path_color,
                points=18,
                wobble=0.18,
                rotation_degrees=rotation,
                seed=700 + index,
            )

        make_flat_blob(
            self.render,
            "frost-biome-snowfield",
            (FROST_BIOME_CENTER.getX(), FROST_BIOME_CENTER.getY(), -0.006),
            36.0,
            38.0,
            snow,
            points=34,
            wobble=0.24,
            rotation_degrees=-8,
            seed=710,
        )
        make_flat_blob(
            self.render,
            "frost-biome-blue-shadow",
            (FROST_BIOME_CENTER.getX(), FROST_BIOME_CENTER.getY(), -0.002),
            26.5,
            24.0,
            blue_snow,
            points=28,
            wobble=0.22,
            rotation_degrees=12,
            seed=711,
        )
        make_flat_blob(
            self.render,
            "frost-ice-pond",
            (86.0, 82.5, 0.025),
            10.8,
            6.4,
            ice,
            points=28,
            wobble=0.18,
            rotation_degrees=-18,
            seed=712,
        )
        make_flat_blob(
            self.render,
            "frost-deep-ice",
            (87.0, 82.8, 0.04),
            6.5,
            3.3,
            dark_ice,
            points=20,
            wobble=0.12,
            rotation_degrees=-18,
            seed=713,
        )

        for index, (x, y, sx, sy, rotation) in enumerate(
            (
                (53.0, 50.0, 4.0, 2.0, -18),
                (60.5, 70.5, 5.4, 2.4, 22),
                (78.0, 56.5, 4.7, 2.0, -12),
                (81.5, 73.0, 4.5, 2.3, 18),
                (96.0, 91.0, 6.2, 2.6, -8),
                (54.0, 94.0, 5.6, 2.4, 26),
                (102.0, 54.0, 5.2, 2.2, -16),
            )
        ):
            make_flat_blob(
                self.render,
                f"frost-snow-drift-{index}",
                (x, y, 0.01),
                sx,
                sy,
                (0.86, 0.92, 0.9, 0.76),
                points=16,
                wobble=0.2,
                rotation_degrees=rotation,
                seed=720 + index,
            )

        for index, (x, y, height, color) in enumerate(
            (
                (58.2, 59.0, 1.2, (0.44, 0.9, 1.0, 0.56)),
                (63.2, 74.5, 1.65, (0.62, 0.98, 1.0, 0.6)),
                (74.4, 60.0, 1.35, (0.42, 0.72, 1.0, 0.58)),
                (80.0, 69.5, 1.1, (0.72, 0.9, 1.0, 0.52)),
                (55.0, 68.0, 0.9, (0.5, 0.78, 1.0, 0.5)),
            )
        ):
            crystal = make_box(
                self.render,
                f"frost-crystal-{index}",
                (0.32, 0.32, height),
                color,
                (x, y, height / 2),
                (0, 0, rng.uniform(0, 45)),
            )
            make_box(
                self.render,
                f"frost-crystal-tip-{index}",
                (0.2, 0.2, 0.28),
                color,
                (x, y, height + 0.1),
                (0, 0, rng.uniform(0, 45)),
            )
            self._add_animated_detail(crystal, bob_amount=0.018, sway_amount=0.0, speed=1.3, phase=index)

        for index, (x, y, scale, lean) in enumerate(
            (
                (50.0, 55.0, 0.95, -15),
                (55.5, 78.0, 1.1, 18),
                (67.0, 47.0, 0.85, -8),
                (84.0, 61.0, 1.0, 14),
                (79.0, 80.0, 0.9, -18),
                (46.5, 69.0, 0.82, 10),
            )
        ):
            root = self.render.attachNewNode(f"frost-dead-tree-{index}")
            root.setPos(x, y, 0)
            root.setH(rng.uniform(-18, 18))
            make_box(root, "trunk", (0.24 * scale, 0.24 * scale, 2.4 * scale), dead_wood, (0, 0, 1.2 * scale), (lean, 0, 0))
            make_box(root, "branch-a", (0.16 * scale, 1.25 * scale, 0.14 * scale), dead_wood, (0.42 * scale, 0.2 * scale, 1.65 * scale), (0, 0, 36))
            make_box(root, "branch-b", (0.14 * scale, 1.0 * scale, 0.12 * scale), dead_wood, (-0.36 * scale, -0.1 * scale, 1.95 * scale), (0, 0, -42))
            make_box(root, "snow-cap", (0.48 * scale, 0.36 * scale, 0.08 * scale), (0.9, 0.94, 0.9, 1), (0, 0, 2.42 * scale), (0, 0, rng.uniform(-12, 12)))

        for index in range(44):
            x = rng.uniform(FROST_BIOME_BOUNDS[0], FROST_BIOME_BOUNDS[1])
            y = rng.uniform(FROST_BIOME_BOUNDS[2], FROST_BIOME_BOUNDS[3])
            if (Vec3(x, y, 0) - Vec3(86.0, 82.5, 0)).length() < 8.2:
                continue
            make_box(
                self.render,
                f"frost-tuft-{index}",
                (rng.uniform(0.08, 0.18), rng.uniform(0.08, 0.18), rng.uniform(0.22, 0.55)),
                rng.choice(((0.38, 0.54, 0.48, 1), (0.48, 0.62, 0.62, 1), (0.78, 0.84, 0.78, 1))),
                (x, y, 0.16),
                (0, rng.uniform(-16, 16), rng.uniform(0, 360)),
            )

        make_box(self.render, "frost-sign-post", (0.12, 0.12, 1.15), dead_wood, (44.5, 39.5, 0.58), (0, 0, 20))
        make_box(self.render, "frost-sign-board", (1.35, 0.12, 0.42), (0.34, 0.28, 0.22, 1), (44.8, 39.9, 1.12), (0, 0, 20))
        make_box(self.render, "frost-sign-snow", (1.45, 0.14, 0.08), (0.88, 0.94, 0.92, 1), (44.8, 39.9, 1.36), (0, 0, 20))

        frost_chests = (
            ("Frozen Wayfarer Chest", Vec3(58.0, 57.0, 0), 36, "wisp"),
            ("Icebound Hunter Cache", Vec3(76.0, 63.5, 0), 44, "boar"),
            ("Aurora Hoard", Vec3(70.5, 77.0, 0), 58, "mixed"),
        )
        for index, (name, pos, reward, guard_kind) in enumerate(frost_chests):
            chest_index = 50 + index
            chest = self._make_chest(chest_index, name, pos, reward, guard_kind, FROST_BIOME_BOUNDS)
            self.chests.append(chest)
            self._spawn_chest_guards(chest_index, pos, guard_kind, bounds=FROST_BIOME_BOUNDS)

    def _build_sunken_meadow_biome(self):
        rng = random.Random(260537)
        meadow = (0.2, 0.34, 0.13, 1)
        wet_grass = (0.09, 0.27, 0.15, 1)
        flower_gold = (0.96, 0.72, 0.24, 1)
        moss = (0.12, 0.42, 0.2, 1)
        old_stone = (0.34, 0.35, 0.3, 1)
        water = (0.05, 0.28, 0.3, 0.62)
        dark_water = (0.03, 0.14, 0.18, 0.72)

        path_points = (
            (-34.0, 27.0, 8.2, 1.15, 134),
            (-46.0, 38.0, 9.0, 1.2, 132),
            (-60.0, 49.5, 10.0, 1.25, 128),
            (-74.0, 60.5, 10.5, 1.3, 126),
            (-88.0, 69.0, 9.5, 1.35, 112),
        )
        for index, (x, y, sx, sy, rotation) in enumerate(path_points):
            make_flat_blob(
                self.render,
                f"sunken-meadow-path-{index}",
                (x, y, -0.006),
                sx,
                sy,
                (0.31, 0.25, 0.14, 1),
                points=18,
                wobble=0.17,
                rotation_degrees=rotation,
                seed=800 + index,
            )

        make_flat_blob(
            self.render,
            "sunken-meadow-field",
            (SUNKEN_MEADOW_CENTER.getX(), SUNKEN_MEADOW_CENTER.getY(), -0.008),
            28.5,
            31.0,
            meadow,
            points=38,
            wobble=0.28,
            rotation_degrees=10,
            seed=810,
        )
        make_flat_blob(
            self.render,
            "sunken-meadow-lowland",
            (-94.0, 75.0, -0.004),
            20.0,
            18.5,
            wet_grass,
            points=30,
            wobble=0.27,
            rotation_degrees=-12,
            seed=811,
        )

        for index, (x, y, sx, sy, rotation) in enumerate(
            (
                (-105.0, 62.0, 5.0, 2.4, -18),
                (-91.0, 82.0, 6.4, 3.0, 20),
                (-78.0, 67.0, 4.7, 2.5, 8),
            )
        ):
            make_flat_blob(
                self.render,
                f"sunken-meadow-pool-{index}",
                (x, y, 0.02),
                sx,
                sy,
                water,
                points=24,
                wobble=0.2,
                rotation_degrees=rotation,
                seed=820 + index,
            )
            make_flat_blob(
                self.render,
                f"sunken-meadow-pool-depth-{index}",
                (x + 0.3, y - 0.2, 0.04),
                sx * 0.55,
                sy * 0.5,
                dark_water,
                points=18,
                wobble=0.14,
                rotation_degrees=rotation,
                seed=830 + index,
            )

        for index, (x, y, scale) in enumerate(
            (
                (-116.0, 51.0, 1.1),
                (-110.0, 74.0, 0.92),
                (-103.0, 96.0, 1.15),
                (-92.0, 46.0, 1.0),
                (-82.0, 101.0, 0.96),
                (-71.0, 55.0, 1.08),
                (-68.0, 87.0, 0.9),
                (-98.0, 58.0, 0.82),
                (-84.0, 78.0, 0.88),
            )
        ):
            tree = make_tree(self.render, f"sunken-meadow-willow-{index}", (x, y, 0), scale)
            tree.setH(rng.uniform(-35, 35))

        for index in range(80):
            x = rng.uniform(SUNKEN_MEADOW_BOUNDS[0] + 2.0, SUNKEN_MEADOW_BOUNDS[1] - 2.0)
            y = rng.uniform(SUNKEN_MEADOW_BOUNDS[2] + 2.0, SUNKEN_MEADOW_BOUNDS[3] - 2.0)
            height = rng.uniform(0.18, 0.54)
            color = rng.choice((moss, (0.16, 0.48, 0.18, 1), (0.18, 0.36, 0.1, 1)))
            make_box(
                self.render,
                f"sunken-meadow-tuft-{index}",
                (rng.uniform(0.04, 0.08), rng.uniform(0.05, 0.11), height),
                color,
                (x, y, height / 2),
                (0, rng.uniform(-18, 18), rng.uniform(0, 360)),
            )
            if index % 4 == 0:
                make_box(
                    self.render,
                    f"sunken-meadow-flower-{index}",
                    (0.14, 0.14, 0.08),
                    rng.choice((flower_gold, (0.82, 0.45, 0.88, 1), (0.72, 0.86, 0.95, 1))),
                    (x, y, height + 0.04),
                    (0, 0, rng.uniform(0, 360)),
                )

        for index, (x, y, h) in enumerate(
            (
                (-101.5, 72.0, 1.8),
                (-98.0, 72.4, 1.25),
                (-94.5, 72.2, 1.6),
                (-91.0, 71.8, 1.05),
                (-87.5, 72.1, 1.4),
            )
        ):
            make_box(self.render, f"sunken-ruin-pillar-{index}", (0.55, 0.55, h), old_stone, (x, y, h / 2), (0, 0, rng.uniform(-8, 8)))
            make_box(self.render, f"sunken-ruin-moss-{index}", (0.6, 0.16, 0.08), moss, (x, y - 0.22, h + 0.04), (0, 0, rng.uniform(-8, 8)))

        for index in range(12):
            firefly = self.render.attachNewNode(f"sunken-meadow-firefly-{index}")
            firefly.setPos(
                rng.uniform(SUNKEN_MEADOW_BOUNDS[0] + 8.0, SUNKEN_MEADOW_BOUNDS[1] - 8.0),
                rng.uniform(SUNKEN_MEADOW_BOUNDS[2] + 8.0, SUNKEN_MEADOW_BOUNDS[3] - 8.0),
                rng.uniform(0.72, 1.65),
            )
            glow = make_box(firefly, "glow", (0.14, 0.14, 0.14), (1.0, 0.85, 0.34, 0.58), (0, 0, 0))
            self._add_animated_detail(
                firefly,
                bob_amount=rng.uniform(0.1, 0.24),
                sway_amount=rng.uniform(6.0, 13.0),
                speed=rng.uniform(1.0, 1.9),
                phase=rng.uniform(0, math.pi * 2),
            )
            self._add_animated_detail(glow, bob_amount=0.0, sway_amount=0.0, speed=3.2, phase=index)

        make_box(self.render, "sunken-meadow-sign-post", (0.12, 0.12, 1.2), (0.24, 0.14, 0.06, 1), (-65.5, 45.5, 0.6), (0, 0, -20))
        make_box(self.render, "sunken-meadow-sign-board", (1.5, 0.12, 0.42), (0.36, 0.22, 0.1, 1), (-65.8, 45.8, 1.08), (0, 0, -20))
        make_box(self.render, "sunken-meadow-sign-flower", (0.18, 0.04, 0.18), flower_gold, (-66.22, 45.68, 1.12), (0, 0, -20))

        meadow_chests = (
            ("Sunken Meadow Chest", Vec3(-103.5, 69.5, 0), 46, "snapper"),
            ("Goldpetal Cache", Vec3(-80.0, 87.5, 0), 52, "bird"),
            ("Moss-Crowned Hoard", Vec3(-111.0, 91.0, 0), 64, "mixed"),
        )
        for index, (name, pos, reward, guard_kind) in enumerate(meadow_chests):
            chest_index = 70 + index
            chest = self._make_chest(chest_index, name, pos, reward, guard_kind, SUNKEN_MEADOW_BOUNDS)
            self.chests.append(chest)
            self._spawn_chest_guards(chest_index, pos, guard_kind, bounds=SUNKEN_MEADOW_BOUNDS)

    def _make_chest(
        self,
        index: int,
        name: str,
        pos: Vec3,
        reward_gold: int,
        guard_kind: str,
        guard_bounds: Optional[Tuple[float, float, float, float]] = None,
    ) -> SceneChest:
        root = self.render.attachNewNode(f"treasure-chest-{index}")
        root.setPos(pos)
        make_box(root, "chest-shadow", (1.35, 0.85, 0.035), (0.02, 0.018, 0.01, 0.34), (0, 0.04, 0.03))
        make_box(root, "chest-base", (0.94, 0.58, 0.42), (0.38, 0.2, 0.08, 1), (0, 0, 0.34))
        make_box(root, "chest-lid", (1.02, 0.64, 0.24), (0.46, 0.24, 0.1, 1), (0, 0, 0.68))
        make_box(root, "chest-front-band", (1.08, 0.08, 0.52), (0.86, 0.63, 0.18, 1), (0, -0.34, 0.44))
        make_box(root, "chest-lock", (0.18, 0.08, 0.22), (0.98, 0.78, 0.24, 1), (0, -0.39, 0.45))
        glow = make_box(root, "chest-glow", (1.16, 0.72, 0.08), (1.0, 0.82, 0.32, 0.35), (0, 0, 0.78))
        self._add_animated_detail(glow, bob_amount=0.025, sway_amount=0.0, speed=2.2, phase=index * 0.7)
        return SceneChest(
            name=name,
            node=root,
            pos=Vec3(pos),
            reward_gold=reward_gold,
            guard_kind=guard_kind,
            guard_bounds=guard_bounds,
        )

    def _spawn_chest_guards(self, chest_index: int, chest_pos: Vec3, guard_kind: str,
                             bounds: Optional[Tuple[float, float, float, float]] = None):
        offsets = {
            "rabbit": (Vec3(-1.6, -0.6, 0), Vec3(1.5, 0.7, 0)),
            "mixed": (Vec3(-1.8, 0.9, 0), Vec3(1.8, -0.9, 0), Vec3(0.0, 1.9, 0)),
            "monster": (Vec3(-1.5, 1.0, 0), Vec3(1.5, -1.0, 0), Vec3(0.0, 2.2, 0)),
            "boar": (Vec3(-2.0, 0.0, 0), Vec3(2.0, 0.0, 0)),
            "bird": (Vec3(-1.6, -0.8, 0), Vec3(1.6, 0.8, 0)),
            "snapper": (Vec3(-1.8, -0.7, 0), Vec3(1.8, 0.7, 0)),
            "wisp": (Vec3(-1.7, 0.9, 0), Vec3(1.7, -0.9, 0), Vec3(0.0, 1.9, 0)),
            "level2_mixed": (Vec3(-2.2, 1.0, 0), Vec3(2.2, -1.0, 0), Vec3(0.0, 2.5, 0)),
            "level2_boar": (Vec3(-2.2, 0.8, 0), Vec3(2.2, -0.8, 0), Vec3(0.0, 2.5, 0)),
            "level2_wisp": (Vec3(-2.0, 1.0, 0), Vec3(2.0, -1.0, 0), Vec3(0.0, 2.3, 0)),
            "level2_snapper": (Vec3(-2.0, -0.9, 0), Vec3(2.0, 0.9, 0), Vec3(0.0, 2.2, 0)),
        }[guard_kind]

        guard_bounds = bounds or TREASURE_MAP_BOUNDS
        for guard_index, offset in enumerate(offsets):
            pos = chest_pos + offset
            if guard_kind == "monster" and guard_index == 2:
                guard = self._make_monster(pos)
            elif guard_kind == "mixed" and guard_index == 2:
                guard = self._make_monster(pos)
            elif guard_kind == "boar":
                guard = self._make_boar(100 + chest_index * 10 + guard_index, pos)
            elif guard_kind == "bird":
                guard = self._make_bird(100 + chest_index * 10 + guard_index, pos)
            elif guard_kind == "snapper":
                guard = self._make_snapper(100 + chest_index * 10 + guard_index, pos)
            elif guard_kind == "wisp":
                guard = self._make_wisp(100 + chest_index * 10 + guard_index, pos)
            elif guard_kind.startswith("level2"):
                guard = self._make_level2_guard(guard_kind, 100 + chest_index * 10 + guard_index, pos, guard_index)
            else:
                guard = self._make_rabbit(100 + chest_index * 10 + guard_index, pos)
            guard.bounds = guard_bounds
            self.enemies.append(guard)

    def _make_level2_guard(self, guard_kind: str, number: int, pos: Vec3, guard_index: int) -> SceneEnemy:
        if guard_kind == "level2_boar":
            enemy = self._make_boar(number, pos)
        elif guard_kind == "level2_wisp":
            enemy = self._make_wisp(number, pos)
        elif guard_kind == "level2_snapper":
            enemy = self._make_snapper(number, pos)
        elif guard_index == 2:
            enemy = self._make_monster(pos)
        elif guard_index == 1:
            enemy = self._make_boar(number, pos)
        else:
            enemy = self._make_snapper(number, pos)
        return self._toughen_level2_enemy(enemy)

    def _toughen_level2_enemy(self, enemy: SceneEnemy) -> SceneEnemy:
        enemy.name = f"Level 2 {enemy.name}"
        enemy.hp = max(enemy.hp + 14, int(enemy.hp * 1.55))
        enemy.max_hp = enemy.hp
        enemy.contact_damage += 3
        enemy.speed *= 1.08
        enemy.bounds = LEVEL2_ZONE_BOUNDS
        enemy.home_pos = Vec3(enemy.node.getPos())
        enemy.node.setScale(enemy.node.getScale() * 1.12)
        enemy.node.setColorScale(1.12, 0.9, 0.78, 1)
        return enemy

    def _spawn_level2_patrols(self):
        specs = (
            ("boar", Vec3(139.0, -158.0, 0)),
            ("boar", Vec3(154.0, -181.0, 0)),
            ("snapper", Vec3(176.0, -151.0, 0)),
            ("snapper", Vec3(187.0, -139.0, 0)),
            ("wisp", Vec3(188.0, -108.0, 0)),
            ("wisp", Vec3(202.0, -121.0, 0)),
            ("monster", Vec3(163.0, -126.0, 0)),
            ("monster", Vec3(180.0, -165.0, 0)),
        )
        for index, (kind, pos) in enumerate(specs):
            if kind == "boar":
                enemy = self._make_boar(900 + index, pos)
            elif kind == "snapper":
                enemy = self._make_snapper(900 + index, pos)
            elif kind == "wisp":
                enemy = self._make_wisp(900 + index, pos)
            else:
                enemy = self._make_monster(pos)
            self.enemies.append(self._toughen_level2_enemy(enemy))

    def _build_world_details(self):
        rng = random.Random(260530)

        for index, (x, y, heading) in enumerate(
            (
                (-1.25, 3.0, 0),
                (0.0, 3.0, 0),
                (1.25, 3.0, 0),
                (-1.25, 4.15, 0),
                (0.0, 4.15, 0),
                (1.25, 4.15, 0),
                (-1.25, 5.3, 0),
                (0.0, 5.3, 0),
                (1.25, 5.3, 0),
                (-1.25, 6.45, 0),
                (0.0, 6.45, 0),
                (1.25, 6.45, 0),
            )
        ):
            make_box(
                self.render,
                f"dock-plank-line-{index}",
                (0.08, 0.95, 0.04),
                (0.24, 0.13, 0.06, 1),
                (x, y, 0.16),
                (0, 0, heading),
            )

        for index, x in enumerate((-1.72, 1.72)):
            for y in (3.0, 6.55):
                make_box(
                    self.render,
                    f"dock-post-{index}-{y}",
                    (0.18, 0.18, 1.0),
                    (0.2, 0.11, 0.05, 1),
                    (x, y, 0.55),
                )
        make_box(
            self.render,
            "dock-rope-left",
            (0.07, 3.7, 0.07),
            (0.62, 0.47, 0.27, 1),
            (-1.72, 4.78, 0.93),
        )
        make_box(
            self.render,
            "dock-rope-right",
            (0.07, 3.7, 0.07),
            (0.62, 0.47, 0.27, 1),
            (1.72, 4.78, 0.93),
        )

        for index, (x, y) in enumerate(((-1.85, 6.7), (1.85, 6.7), (-10.9, 0.0))):
            lantern = self.render.attachNewNode(f"lantern-{index}")
            lantern.setPos(x, y, 0)
            make_box(lantern, "lantern-post", (0.08, 0.08, 1.4), (0.16, 0.08, 0.04, 1), (0, 0, 0.7))
            make_box(lantern, "lantern-arm", (0.48, 0.06, 0.06), (0.16, 0.08, 0.04, 1), (0.2, 0, 1.3))
            glow = make_box(lantern, "lantern-glow", (0.34, 0.34, 0.34), (1.0, 0.72, 0.25, 0.38), (0.48, 0, 1.08))
            make_box(lantern, "lantern-core", (0.16, 0.16, 0.22), (1.0, 0.54, 0.12, 0.82), (0.48, 0, 1.08))
            self._add_animated_detail(glow, bob_amount=0.02, sway_amount=0.0, speed=2.8, phase=index)

        for index, (x, y, length, heading) in enumerate(
            (
                (-5.8, 8.4, 1.2, -8),
                (-1.8, 11.0, 1.7, 12),
                (2.9, 8.8, 1.35, 4),
                (6.2, 11.2, 1.05, -18),
                (-3.6, 14.0, 1.25, 18),
                (3.7, 14.5, 1.4, -10),
            )
        ):
            shimmer = make_box(
                self.render,
                f"lake-shimmer-{index}",
                (length, 0.055, 0.025),
                (0.78, 0.95, 1.0, 0.42),
                (x, y, 0.14 + index * 0.006),
                (0, 0, heading),
            )
            self._add_animated_detail(
                shimmer,
                bob_amount=0.015,
                sway_amount=5.0,
                speed=1.4 + index * 0.22,
                phase=index * 0.7,
                color=(0.78, 0.95, 1.0, 0.42),
            )

        lily_colors = (
            (0.12, 0.42, 0.22, 1),
            (0.16, 0.5, 0.25, 1),
            (0.1, 0.34, 0.2, 1),
        )
        for index, (x, y, sx, sy, heading) in enumerate(
            (
                (-7.2, 8.0, 0.52, 0.36, -12),
                (-5.8, 11.3, 0.42, 0.32, 18),
                (-1.4, 13.3, 0.55, 0.38, 8),
                (3.5, 12.2, 0.46, 0.34, -22),
                (6.5, 9.0, 0.5, 0.35, 14),
                (8.3, 11.8, 0.38, 0.28, -8),
            )
        ):
            pad = make_flat_blob(
                self.render,
                f"lily-pad-{index}",
                (x, y, 0.16 + index * 0.004),
                sx,
                sy,
                lily_colors[index % len(lily_colors)],
                points=13,
                wobble=0.2,
                rotation_degrees=heading,
                seed=520 + index,
            )
            self._add_animated_detail(
                pad,
                bob_amount=0.012,
                sway_amount=2.5,
                speed=1.0 + index * 0.14,
                phase=index * 0.5,
            )
            if index in (1, 4):
                flower = make_box(
                    self.render,
                    f"lily-flower-{index}",
                    (0.16, 0.16, 0.08),
                    (0.95, 0.72, 0.92, 1),
                    (x + 0.08, y - 0.04, 0.2 + index * 0.004),
                    (0, 0, heading),
                )
                self._add_animated_detail(
                    flower,
                    bob_amount=0.012,
                    sway_amount=2.5,
                    speed=1.0 + index * 0.14,
                    phase=index * 0.5,
                )

        for index in range(14):
            x = rng.uniform(-8.0, 8.0)
            y = rng.uniform(7.2, 14.8)
            petal = make_box(
                self.render,
                f"lake-petal-{index}",
                (0.16, 0.05, 0.025),
                rng.choice(((0.9, 0.72, 0.86, 0.72), (0.88, 0.92, 0.72, 0.68), (0.75, 0.86, 1.0, 0.58))),
                (x, y, 0.19 + index * 0.002),
                (0, 0, rng.uniform(0, 360)),
            )
            self._add_animated_detail(
                petal,
                bob_amount=rng.uniform(0.006, 0.018),
                sway_amount=rng.uniform(2.0, 5.5),
                speed=rng.uniform(0.7, 1.4),
                phase=rng.uniform(0, math.pi * 2.0),
                color=(1, 1, 1, 0.7),
            )

        for index in range(44):
            angle = rng.uniform(0, math.pi * 2.0)
            radius_x = rng.uniform(8.4, 13.8)
            radius_y = rng.uniform(4.3, 7.7)
            x = math.cos(angle) * radius_x + rng.uniform(-0.4, 0.4)
            y = 9.7 + math.sin(angle) * radius_y + rng.uniform(-0.4, 0.4)
            if -1.9 <= x <= 1.9 and 2.6 <= y <= 7.0:
                continue
            height = rng.uniform(0.22, 0.55)
            color = rng.choice(
                (
                    (0.12, 0.38, 0.14, 1),
                    (0.16, 0.48, 0.18, 1),
                    (0.2, 0.36, 0.12, 1),
                )
            )
            make_box(
                self.render,
                f"shore-grass-{index}",
                (0.055, 0.08, height),
                color,
                (x, y, height / 2),
                (0, rng.uniform(-16, 16), rng.uniform(0, 360)),
            )

        flower_colors = (
            (0.86, 0.28, 0.42, 1),
            (0.95, 0.84, 0.3, 1),
            (0.56, 0.68, 1.0, 1),
            (0.95, 0.62, 0.92, 1),
        )
        for index in range(22):
            x = rng.uniform(-14.5, 14.5)
            y = rng.choice((rng.uniform(-2.7, 2.1), rng.uniform(13.8, 17.0)))
            make_box(
                self.render,
                f"wildflower-stem-{index}",
                (0.035, 0.035, 0.22),
                (0.14, 0.42, 0.12, 1),
                (x, y, 0.12),
            )
            make_box(
                self.render,
                f"wildflower-head-{index}",
                (0.13, 0.13, 0.08),
                rng.choice(flower_colors),
                (x, y, 0.26),
                (0, 0, rng.uniform(0, 360)),
            )

        for index, (x, y, sx, sy) in enumerate(
            (
                (-1.0, 2.05, 0.56, 0.36),
                (0.18, 1.34, 0.48, 0.32),
                (1.18, 0.68, 0.52, 0.34),
                (-4.0, 1.58, 0.62, 0.34),
                (-6.2, 1.44, 0.5, 0.3),
                (-8.05, 1.36, 0.56, 0.32),
            )
        ):
            make_flat_blob(
                self.render,
                f"path-stepping-stone-{index}",
                (x, y, 0.02),
                sx,
                sy,
                (0.42, 0.42, 0.34, 1),
                points=12,
                wobble=0.18,
                rotation_degrees=rng.uniform(-20, 20),
                seed=610 + index,
            )

        signpost = self.render.attachNewNode("crossroads-signpost")
        signpost.setPos(-2.7, 1.35, 0)
        signpost.setH(-8)
        make_box(signpost, "signpost-pole", (0.12, 0.12, 1.25), (0.26, 0.13, 0.06, 1), (0, 0, 0.62))
        make_box(signpost, "signpost-lake-arrow", (0.9, 0.12, 0.28), (0.48, 0.3, 0.13, 1), (0.28, 0, 1.05), (0, 0, -5))
        make_box(signpost, "signpost-shop-arrow", (0.75, 0.12, 0.25), (0.48, 0.3, 0.13, 1), (-0.25, 0, 0.78), (0, 0, 185))
        make_box(signpost, "signpost-lake-mark", (0.24, 0.04, 0.05), (0.55, 0.82, 1.0, 1), (0.48, -0.08, 1.08), (0, 0, -5))
        make_box(signpost, "signpost-shop-mark", (0.2, 0.04, 0.05), (0.95, 0.72, 0.22, 1), (-0.43, -0.08, 0.8), (0, 0, 185))

        for index, (x, y, heading) in enumerate(
            (
                (-1.35, 5.55, -8),
                (1.42, 5.35, 10),
                (-0.85, 3.75, 16),
            )
        ):
            basket = self.render.attachNewNode(f"dock-basket-{index}")
            basket.setPos(x, y, 0.22)
            basket.setH(heading)
            make_box(basket, "basket-bottom", (0.48, 0.34, 0.22), (0.42, 0.25, 0.1, 1), (0, 0, 0.1))
            make_box(basket, "basket-rim", (0.54, 0.08, 0.08), (0.58, 0.38, 0.16, 1), (0, -0.16, 0.24))
            make_box(basket, "basket-net", (0.06, 0.42, 0.06), (0.78, 0.68, 0.48, 1), (-0.12, 0.02, 0.28), (0, 0, 20))

        for index, (x, y, color) in enumerate(
            (
                (-10.8, 2.2, (0.88, 0.64, 0.22, 1)),
                (-9.7, 2.7, (0.54, 0.82, 0.92, 1)),
                (-8.8, 2.1, (0.95, 0.52, 0.68, 1)),
                (-12.4, 0.4, (0.84, 0.76, 0.42, 1)),
                (9.4, 1.8, (0.78, 0.55, 0.95, 1)),
            )
        ):
            butterfly = self.render.attachNewNode(f"butterfly-{index}")
            butterfly.setPos(x, y, 0.86 + index * 0.04)
            make_box(butterfly, "butterfly-body", (0.045, 0.09, 0.05), (0.08, 0.06, 0.04, 1), (0, 0, 0))
            make_box(butterfly, "butterfly-left-wing", (0.16, 0.035, 0.1), color, (-0.1, 0, 0.02), (0, 0, 18))
            make_box(butterfly, "butterfly-right-wing", (0.16, 0.035, 0.1), color, (0.1, 0, 0.02), (0, 0, -18))
            self._add_animated_detail(
                butterfly,
                bob_amount=0.16,
                sway_amount=18.0,
                speed=1.7 + index * 0.25,
                phase=index * 0.9,
            )

        for index, (x, y, h) in enumerate(
            (
                (-4.8, 2.15, -16),
                (-3.9, 1.62, 14),
                (5.2, 2.0, 20),
                (6.1, 1.5, -10),
                (-7.8, 5.0, 32),
                (7.6, 5.15, -28),
            )
        ):
            make_box(self.render, f"old-relic-blade-{index}", (0.14, 0.72, 0.08), (0.45, 0.48, 0.47, 1), (x, y, 0.16), (0, 0, h))
            make_box(self.render, f"old-relic-hilt-{index}", (0.38, 0.08, 0.08), (0.35, 0.22, 0.1, 1), (x, y - 0.3, 0.17), (0, 0, h))

        for index, (x, y, scale) in enumerate(((-12.5, -0.7, 1.0), (-11.7, -1.35, 0.75), (11.7, 0.4, 0.9))):
            make_box(self.render, f"mushroom-stem-{index}", (0.12 * scale, 0.12 * scale, 0.22 * scale), (0.78, 0.7, 0.56, 1), (x, y, 0.12 * scale))
            make_box(self.render, f"mushroom-cap-{index}", (0.36 * scale, 0.3 * scale, 0.13 * scale), (0.74, 0.12, 0.16, 1), (x, y, 0.28 * scale))
            make_box(self.render, f"mushroom-dot-{index}", (0.08 * scale, 0.06 * scale, 0.035 * scale), (0.96, 0.86, 0.72, 1), (x + 0.05 * scale, y - 0.02 * scale, 0.36 * scale))

        for index, (x, y) in enumerate(((-7.4, -4.45), (-5.8, -4.45), (5.8, -4.45), (7.4, -4.45))):
            flag = self.render.attachNewNode(f"arena-flag-{index}")
            flag.setPos(x, y, 0)
            make_box(flag, "flag-pole", (0.07, 0.07, 1.15), (0.17, 0.1, 0.05, 1), (0, 0, 0.55))
            cloth = make_box(flag, "flag-cloth", (0.48, 0.08, 0.34), (0.68, 0.08, 0.1, 1), (0.24, 0, 0.95), (0, 0, 4))
            self._add_animated_detail(cloth, bob_amount=0.0, sway_amount=6.0, speed=2.2, phase=index * 0.8)

        for index, (x, y) in enumerate(((-6.8, -12.6), (6.8, -12.3))):
            make_box(self.render, f"arena-dummy-post-{index}", (0.16, 0.16, 1.1), (0.25, 0.13, 0.06, 1), (x, y, 0.55))
            make_box(self.render, f"arena-dummy-body-{index}", (0.7, 0.28, 0.55), (0.55, 0.42, 0.22, 1), (x, y, 0.92))
            make_box(self.render, f"arena-dummy-mark-{index}", (0.38, 0.04, 0.06), (0.75, 0.12, 0.08, 1), (x, y - 0.17, 0.96))

        for index in range(9):
            firefly = self.render.attachNewNode(f"firefly-{index}")
            x = rng.uniform(-8.8, 8.8)
            y = rng.uniform(6.4, 14.2)
            z = rng.uniform(0.72, 1.35)
            firefly.setPos(x, y, z)
            glow = make_box(firefly, "firefly-glow", (0.13, 0.13, 0.13), (1.0, 0.92, 0.32, 0.58), (0, 0, 0))
            self._add_animated_detail(
                firefly,
                bob_amount=rng.uniform(0.08, 0.18),
                sway_amount=rng.uniform(4.0, 9.0),
                speed=rng.uniform(1.1, 2.1),
                phase=rng.uniform(0, math.pi * 2.0),
                color=(1.0, 0.92, 0.32, 0.58),
            )
            self._add_animated_detail(glow, bob_amount=0.0, sway_amount=0.0, speed=3.5, phase=index)

    def _build_raft(self, name: str, pos: Vec3, heading: float):
        raft = self.render.attachNewNode(name)
        raft.setPos(pos)
        raft.setH(heading)
        wood = (0.38, 0.22, 0.1, 1)
        rope = (0.68, 0.54, 0.32, 1)
        sail = (0.78, 0.72, 0.56, 1)
        make_box(raft, "raft-shadow", (2.9, 1.75, 0.035), (0.02, 0.018, 0.01, 0.28), (0, 0, 0.035))
        for index, x in enumerate((-0.9, -0.3, 0.3, 0.9)):
            make_box(raft, f"log-{index}", (0.42, 1.85, 0.24), wood, (x, 0, 0.18), (0, 0, self.rng.uniform(-2, 2)))
        make_box(raft, "front-rope", (2.25, 0.08, 0.08), rope, (0, 0.74, 0.34))
        make_box(raft, "back-rope", (2.25, 0.08, 0.08), rope, (0, -0.74, 0.34))
        make_box(raft, "mast", (0.12, 0.12, 1.9), (0.22, 0.12, 0.05, 1), (0, 0.08, 1.05))
        make_box(raft, "small-sail", (0.08, 1.0, 0.86), sail, (0, 0.1, 1.35), (0, 0, 4))
        lantern = make_box(raft, "raft-lantern", (0.18, 0.18, 0.24), (1.0, 0.72, 0.22, 0.5), (-0.78, 0.58, 0.66))
        self._add_animated_detail(lantern, bob_amount=0.018, sway_amount=0.0, speed=2.6, phase=heading * 0.1)
        return raft

    def _build_level2_zone(self):
        rng = random.Random(260538)
        old_path = (0.31, 0.24, 0.14, 1)
        shore = (0.25, 0.24, 0.15, 1)
        deep_green = (0.08, 0.22, 0.12, 1)
        ember_ground = (0.24, 0.14, 0.1, 1)
        ash = (0.18, 0.17, 0.16, 1)
        moon_grass = (0.12, 0.28, 0.28, 1)
        moon_blue = (0.28, 0.62, 0.78, 0.62)
        ruin = (0.32, 0.32, 0.3, 1)

        self._build_raft("home-raft", HOME_RAFT_SPOT, -12)
        self._build_raft("level2-raft", LEVEL2_RAFT_SPOT, 168)

        make_flat_blob(
            self.render,
            "level2-island",
            (166.0, -139.0, -0.012),
            43.0,
            54.0,
            deep_green,
            points=42,
            wobble=0.26,
            rotation_degrees=-8,
            seed=900,
        )
        make_flat_blob(
            self.render,
            "level2-lake-bank",
            (LEVEL2_LAKE_CENTER.getX(), LEVEL2_LAKE_CENTER.getY(), -0.004),
            18.0,
            12.5,
            shore,
            points=34,
            wobble=0.22,
            rotation_degrees=-12,
            seed=901,
        )
        make_flat_blob(
            self.render,
            "level2-ancient-lake",
            (LEVEL2_LAKE_CENTER.getX(), LEVEL2_LAKE_CENTER.getY(), 0.024),
            15.5,
            10.5,
            (0.04, 0.28, 0.5, 0.82),
            points=38,
            wobble=0.18,
            rotation_degrees=-12,
            seed=902,
        )
        make_flat_blob(
            self.render,
            "level2-lake-glow",
            (LEVEL2_LAKE_CENTER.getX() + 1.2, LEVEL2_LAKE_CENTER.getY() - 0.8, 0.055),
            8.5,
            4.8,
            (0.36, 0.82, 1.0, 0.32),
            points=24,
            wobble=0.12,
            rotation_degrees=-8,
            seed=903,
        )

        for index, (x, y, sx, sy, heading) in enumerate(
            (
                (148.0, -104.0, 5.8, 1.2, -34),
                (154.0, -114.0, 8.0, 1.25, -50),
                (160.5, -126.0, 8.2, 1.25, -62),
                (164.5, -153.0, 9.0, 1.35, -82),
                (156.0, -171.0, 10.0, 1.35, -128),
                (180.0, -128.0, 10.0, 1.2, 32),
                (190.0, -113.0, 8.5, 1.2, 42),
            )
        ):
            make_flat_blob(
                self.render,
                f"level2-path-{index}",
                (x, y, -0.003),
                sx,
                sy,
                old_path,
                points=18,
                wobble=0.16,
                rotation_degrees=heading,
                seed=910 + index,
            )

        make_flat_blob(
            self.render,
            "level2-ember-grove",
            (148.0, -169.0, -0.002),
            20.0,
            18.0,
            ember_ground,
            points=28,
            wobble=0.25,
            rotation_degrees=14,
            seed=930,
        )
        make_flat_blob(
            self.render,
            "level2-ash-bed",
            (146.0, -174.0, 0.002),
            11.0,
            8.0,
            ash,
            points=22,
            wobble=0.22,
            rotation_degrees=-4,
            seed=931,
        )
        for index, (x, y, scale) in enumerate(
            ((132, -158, 1.0), (137, -183, 1.2), (151, -188, 0.92), (162, -166, 1.08), (145, -152, 0.86))
        ):
            root = self.render.attachNewNode(f"ember-tree-{index}")
            root.setPos(x, y, 0)
            root.setH(rng.uniform(0, 360))
            make_box(root, "trunk", (0.28 * scale, 0.28 * scale, 2.2 * scale), (0.13, 0.08, 0.05, 1), (0, 0, 1.1 * scale), (rng.uniform(-8, 8), 0, 0))
            make_box(root, "ember-canopy-low", (1.25 * scale, 1.0 * scale, 0.72 * scale), (0.48, 0.16, 0.08, 1), (0, 0, 2.25 * scale), (0, 0, rng.uniform(-12, 12)))
            glow = make_box(root, "ember-canopy-glow", (0.78 * scale, 0.62 * scale, 0.46 * scale), (1.0, 0.42, 0.08, 0.28), (0.18 * scale, 0, 2.35 * scale))
            self._add_animated_detail(glow, bob_amount=0.014, sway_amount=0.0, speed=2.2, phase=index)

        make_flat_blob(
            self.render,
            "level2-moon-marsh",
            (188.0, -112.0, -0.002),
            20.0,
            19.0,
            moon_grass,
            points=30,
            wobble=0.25,
            rotation_degrees=-18,
            seed=940,
        )
        for index, (x, y, sx, sy) in enumerate(((184, -104, 4.5, 2.8), (197, -118, 5.2, 3.0), (180, -123, 3.9, 2.4))):
            make_flat_blob(
                self.render,
                f"moon-marsh-pool-{index}",
                (x, y, 0.025),
                sx,
                sy,
                moon_blue,
                points=22,
                wobble=0.19,
                rotation_degrees=rng.uniform(-20, 20),
                seed=950 + index,
            )
        for index in range(34):
            x = rng.uniform(LEVEL2_MOON_BOUNDS[0], LEVEL2_MOON_BOUNDS[1])
            y = rng.uniform(LEVEL2_MOON_BOUNDS[2], LEVEL2_MOON_BOUNDS[3])
            height = rng.uniform(0.25, 0.8)
            reed = make_box(
                self.render,
                f"moon-reed-{index}",
                (0.055, 0.07, height),
                rng.choice(((0.16, 0.48, 0.44, 1), (0.22, 0.58, 0.54, 1), (0.42, 0.72, 0.74, 1))),
                (x, y, height / 2),
                (0, rng.uniform(-14, 14), rng.uniform(0, 360)),
            )
            if index % 6 == 0:
                self._add_animated_detail(reed, bob_amount=0.01, sway_amount=3.0, speed=1.4, phase=index)

        for index, (x, y, h) in enumerate(((170, -121, 2.2), (174, -119, 1.5), (178, -122, 2.6), (182, -120, 1.7), (186, -123, 2.0))):
            make_box(self.render, f"level2-ruin-pillar-{index}", (0.55, 0.55, h), ruin, (x, y, h / 2), (0, 0, rng.uniform(-8, 8)))
            make_box(self.render, f"level2-ruin-cap-{index}", (0.72, 0.72, 0.18), (0.22, 0.22, 0.2, 1), (x, y, h + 0.09))
        make_box(self.render, "level2-ruin-arch-left", (0.55, 0.55, 2.8), ruin, (158.5, -139.0, 1.4))
        make_box(self.render, "level2-ruin-arch-right", (0.55, 0.55, 2.8), ruin, (162.2, -139.0, 1.4))
        make_box(self.render, "level2-ruin-arch-top", (4.2, 0.55, 0.5), ruin, (160.35, -139.0, 2.95))
        make_box(self.render, "level2-fishing-shack-floor", (3.8, 2.4, 0.16), (0.28, 0.18, 0.08, 1), (158.0, -132.0, 0.05), (0, 0, -10))
        make_box(self.render, "level2-fishing-shack-wall", (3.5, 0.2, 1.6), (0.34, 0.2, 0.09, 1), (158.0, -131.1, 0.9), (0, 0, -10))
        make_box(self.render, "level2-fishing-shack-roof", (4.2, 2.8, 0.22), (0.18, 0.09, 0.05, 1), (158.0, -132.0, 1.82), (0, 8, -10))
        make_box(self.render, "level2-fishing-sign", (1.4, 0.12, 0.4), (0.1, 0.06, 0.03, 1), (156.0, -130.1, 1.45), (0, 0, -10))
        make_box(self.render, "level2-fishing-sign-glow", (0.8, 0.04, 0.08), (0.42, 0.82, 1.0, 0.68), (156.0, -130.18, 1.46), (0, 0, -10))

        for index, (x, y, color) in enumerate(((166, -134, (0.6, 0.9, 1.0, 0.42)), (172, -145, (0.96, 0.62, 0.2, 0.38)), (160, -147, (0.6, 0.9, 1.0, 0.36)))):
            shimmer = make_box(self.render, f"level2-lake-shimmer-{index}", (2.4, 0.06, 0.03), color, (x, y, 0.15), (0, 0, rng.uniform(-20, 20)))
            self._add_animated_detail(shimmer, bob_amount=0.018, sway_amount=5.0, speed=1.2 + index * 0.25, phase=index)

        level2_chests = (
            ("Level 2 Shore Chest", Vec3(151.0, -121.0, 0), 72, "level2_mixed"),
            ("Ember Grove Vault", Vec3(143.0, -177.0, 0), 88, "level2_boar"),
            ("Moon Marsh Reliquary", Vec3(195.0, -111.0, 0), 94, "level2_wisp"),
            ("Old Ferry Strongbox", Vec3(188.0, -157.0, 0), 105, "level2_snapper"),
        )
        for index, (name, pos, reward, guard_kind) in enumerate(level2_chests):
            chest_index = 90 + index
            chest = self._make_chest(chest_index, name, pos, reward, guard_kind, LEVEL2_ZONE_BOUNDS)
            self.chests.append(chest)
            self._spawn_chest_guards(chest_index, pos, guard_kind, bounds=LEVEL2_ZONE_BOUNDS)

        self._spawn_level2_patrols()

    def _build_extra_nature(self):
        rng = random.Random(260536)
        flower_colors = (
            (0.9, 0.3, 0.44, 1),
            (0.98, 0.82, 0.28, 1),
            (0.58, 0.72, 1.0, 1),
            (0.95, 0.62, 0.88, 1),
            (0.86, 0.94, 0.68, 1),
        )
        grass_colors = (
            (0.12, 0.38, 0.12, 1),
            (0.16, 0.48, 0.17, 1),
            (0.2, 0.42, 0.14, 1),
            (0.09, 0.3, 0.12, 1),
        )

        def in_busy_center(px: float, py: float) -> bool:
            return -18.0 < px < 18.0 and -16.0 < py < 18.0

        def in_frost(px: float, py: float) -> bool:
            return (
                FROST_BIOME_BOUNDS[0] <= px <= FROST_BIOME_BOUNDS[1]
                and FROST_BIOME_BOUNDS[2] <= py <= FROST_BIOME_BOUNDS[3]
            )

        def in_sunken_meadow(px: float, py: float) -> bool:
            return (
                SUNKEN_MEADOW_BOUNDS[0] <= px <= SUNKEN_MEADOW_BOUNDS[1]
                and SUNKEN_MEADOW_BOUNDS[2] <= py <= SUNKEN_MEADOW_BOUNDS[3]
            )

        meadow_index = 0
        for _ in range(190):
            x = rng.uniform(-WORLD_LIMIT + 10.0, WORLD_LIMIT - 10.0)
            y = rng.uniform(-WORLD_LIMIT + 10.0, WORLD_LIMIT - 10.0)
            pos = Vec3(x, y, 0)
            if in_busy_center(x, y) or in_frost(x, y) or in_sunken_meadow(x, y) or self._is_water_position(pos):
                continue
            height = rng.uniform(0.16, 0.42)
            make_box(
                self.render,
                f"field-grass-blade-{meadow_index}",
                (0.04, 0.05, height),
                rng.choice(grass_colors),
                (x, y, height / 2),
                (0, rng.uniform(-18, 18), rng.uniform(0, 360)),
            )
            if meadow_index % 3 == 0:
                make_box(
                    self.render,
                    f"field-flower-head-{meadow_index}",
                    (0.11, 0.11, 0.07),
                    rng.choice(flower_colors),
                    (x, y, height + 0.035),
                    (0, 0, rng.uniform(0, 360)),
                )
            meadow_index += 1

        fern_color = (0.1, 0.34, 0.14, 1)
        for index in range(48):
            x = rng.choice((rng.uniform(-WORLD_LIMIT + 18, -34), rng.uniform(34, WORLD_LIMIT - 18)))
            y = rng.uniform(-WORLD_LIMIT + 18, WORLD_LIMIT - 18)
            if in_frost(x, y) or in_sunken_meadow(x, y):
                continue
            root = self.render.attachNewNode(f"forest-fern-{index}")
            root.setPos(x, y, 0)
            root.setH(rng.uniform(0, 360))
            for frond in range(5):
                angle = frond * 72 + rng.uniform(-10, 10)
                make_box(
                    root,
                    f"frond-{frond}",
                    (0.08, rng.uniform(0.5, 0.86), 0.055),
                    fern_color,
                    (0, 0.26, 0.18),
                    (0, rng.uniform(-16, 8), angle),
                )

        for index in range(28):
            x = rng.uniform(-WORLD_LIMIT + 14, WORLD_LIMIT - 14)
            y = rng.choice((rng.uniform(-WORLD_LIMIT + 14, -26), rng.uniform(26, WORLD_LIMIT - 14)))
            if in_frost(x, y) or in_sunken_meadow(x, y):
                continue
            heading = rng.uniform(0, 180)
            root = self.render.attachNewNode(f"fallen-log-{index}")
            root.setPos(x, y, 0.13)
            root.setH(heading)
            make_box(root, "log-body", (rng.uniform(0.38, 0.58), rng.uniform(1.25, 2.1), 0.26), (0.26, 0.15, 0.07, 1))
            make_box(root, "log-cut-a", (0.42, 0.06, 0.22), (0.54, 0.38, 0.2, 1), (0, -0.64, 0))
            make_box(root, "log-moss", (0.34, 0.9, 0.05), (0.1, 0.32, 0.12, 1), (0, 0.08, 0.16))

        for index in range(42):
            x = rng.uniform(-WORLD_LIMIT + 16, WORLD_LIMIT - 16)
            y = rng.uniform(-WORLD_LIMIT + 16, WORLD_LIMIT - 16)
            if in_busy_center(x, y) or in_frost(x, y) or in_sunken_meadow(x, y):
                continue
            scale = rng.uniform(0.55, 1.35)
            make_box(self.render, f"field-mushroom-stem-{index}", (0.09 * scale, 0.09 * scale, 0.2 * scale), (0.74, 0.68, 0.54, 1), (x, y, 0.1 * scale))
            make_box(self.render, f"field-mushroom-cap-{index}", (0.28 * scale, 0.24 * scale, 0.11 * scale), rng.choice(((0.66, 0.12, 0.18, 1), (0.82, 0.48, 0.18, 1), (0.44, 0.24, 0.16, 1))), (x, y, 0.24 * scale))

        for index in range(26):
            x = rng.uniform(-12.5, 12.5)
            y = rng.uniform(5.0, 15.8)
            if -1.9 <= x <= 1.9 and 2.6 <= y <= 7.0:
                continue
            height = rng.uniform(0.75, 1.35)
            make_box(
                self.render,
                f"extra-cattail-stem-{index}",
                (0.04, 0.04, height),
                (0.12, 0.36, 0.14, 1),
                (x, y, height / 2),
                (0, rng.uniform(-14, 14), rng.uniform(0, 360)),
            )
            make_box(
                self.render,
                f"extra-cattail-head-{index}",
                (0.09, 0.09, 0.26),
                (0.32, 0.18, 0.08, 1),
                (x, y, height + 0.12),
            )

        for index in range(22):
            x = rng.uniform(FROST_BIOME_BOUNDS[0] + 2.0, FROST_BIOME_BOUNDS[1] - 2.0)
            y = rng.uniform(FROST_BIOME_BOUNDS[2] + 2.0, FROST_BIOME_BOUNDS[3] - 2.0)
            spike_height = rng.uniform(0.28, 0.7)
            make_box(
                self.render,
                f"frost-reed-{index}",
                (0.07, 0.07, spike_height),
                rng.choice(((0.62, 0.78, 0.78, 1), (0.82, 0.9, 0.86, 1), (0.45, 0.64, 0.72, 1))),
                (x, y, spike_height / 2),
                (0, rng.uniform(-12, 12), rng.uniform(0, 360)),
            )
            if index % 4 == 0:
                bloom = make_box(
                    self.render,
                    f"frost-bloom-{index}",
                    (0.16, 0.16, 0.08),
                    (0.72, 0.92, 1.0, 0.68),
                    (x, y, spike_height + 0.05),
                    (0, 0, rng.uniform(0, 360)),
                )
                self._add_animated_detail(bloom, bob_amount=0.012, sway_amount=1.8, speed=1.2, phase=index)

        for index in range(16):
            butterfly = self.render.attachNewNode(f"field-butterfly-{index}")
            x = rng.uniform(-WORLD_LIMIT + 26, WORLD_LIMIT - 26)
            y = rng.uniform(-WORLD_LIMIT + 26, WORLD_LIMIT - 26)
            if in_busy_center(x, y) or in_frost(x, y) or in_sunken_meadow(x, y):
                y += 24.0
            butterfly.setPos(x, y, rng.uniform(0.72, 1.35))
            color = rng.choice(flower_colors)
            make_box(butterfly, "body", (0.04, 0.08, 0.045), (0.08, 0.06, 0.04, 1), (0, 0, 0))
            make_box(butterfly, "left-wing", (0.15, 0.035, 0.09), color, (-0.095, 0, 0.02), (0, 0, 18))
            make_box(butterfly, "right-wing", (0.15, 0.035, 0.09), color, (0.095, 0, 0.02), (0, 0, -18))
            self._add_animated_detail(
                butterfly,
                bob_amount=rng.uniform(0.12, 0.22),
                sway_amount=rng.uniform(10.0, 18.0),
                speed=rng.uniform(1.2, 2.0),
                phase=index * 0.8,
            )

    def _add_animated_detail(
        self,
        node,
        bob_amount: float,
        sway_amount: float,
        speed: float,
        phase: float,
        color: Tuple[float, float, float, float] = (1, 1, 1, 1),
    ):
        self.animated_details.append(
            AnimatedDetail(
                node=node,
                base_pos=Vec3(node.getPos()),
                phase=phase,
                speed=speed,
                bob_amount=bob_amount,
                sway_amount=sway_amount,
                color=color,
            )
        )

    def _build_shop(self):
        shop = self.render.attachNewNode("rod-shop")
        shop.setPos(self.shop_spot)
        shop.setH(18)

        wood = (0.42, 0.25, 0.12, 1)
        dark_wood = (0.22, 0.12, 0.06, 1)
        red_canvas = (0.58, 0.08, 0.1, 1)
        gold = (0.95, 0.72, 0.22, 1)
        blue_cloth = (0.12, 0.34, 0.58, 1)

        make_box(shop, "shop-platform", (4.2, 2.8, 0.18), (0.28, 0.2, 0.12, 1), (0, 0, 0.02))
        make_box(shop, "shop-counter", (3.8, 0.55, 0.65), wood, (0, -0.75, 0.38))
        make_box(shop, "shop-back-wall", (4.0, 0.24, 1.75), dark_wood, (0, 0.92, 0.95))
        make_box(shop, "shop-left-post", (0.18, 0.18, 2.35), dark_wood, (-1.85, -0.9, 1.1))
        make_box(shop, "shop-right-post", (0.18, 0.18, 2.35), dark_wood, (1.85, -0.9, 1.1))
        make_box(shop, "shop-back-left-post", (0.18, 0.18, 2.35), dark_wood, (-1.85, 0.95, 1.1))
        make_box(shop, "shop-back-right-post", (0.18, 0.18, 2.35), dark_wood, (1.85, 0.95, 1.1))
        make_box(shop, "shop-awning-red", (4.3, 1.05, 0.18), red_canvas, (0, -0.18, 2.35), (0, 7, 0))
        make_box(shop, "shop-awning-stripe", (1.05, 1.12, 0.2), (0.95, 0.88, 0.55, 1), (0, -0.18, 2.39), (0, 7, 0))
        make_box(shop, "shop-sign-board", (2.0, 0.2, 0.55), (0.12, 0.08, 0.04, 1), (0, -1.15, 1.85))
        make_box(shop, "shop-sign-rod", (1.55, 0.08, 0.08), gold, (0, -1.28, 1.88), (0, 0, -16))
        make_box(shop, "shop-sign-hook", (0.18, 0.08, 0.32), gold, (0.62, -1.28, 1.68), (0, 0, 16))
        for index, x in enumerate((-1.25, -0.55, 0.15, 0.85, 1.55)):
            charm_color = (
                (0.95, 0.74, 0.24, 1),
                (0.35, 0.68, 0.76, 1),
                (0.72, 0.22, 0.28, 1),
                (0.92, 0.88, 0.6, 1),
                (0.44, 0.62, 0.35, 1),
            )[index]
            charm = make_box(
                shop,
                f"awning-charm-{index}",
                (0.22, 0.055, 0.2),
                charm_color,
                (x, -0.76, 2.08),
                (0, 0, -8 + index * 4),
            )
            self._add_animated_detail(
                charm,
                bob_amount=0.018,
                sway_amount=5.0,
                speed=2.0 + index * 0.2,
                phase=index * 0.55,
            )

        make_box(shop, "shopkeeper-body", (0.52, 0.42, 0.82), blue_cloth, (-0.92, -0.35, 0.82))
        make_box(shop, "shopkeeper-head", (0.42, 0.38, 0.4), (0.78, 0.52, 0.36, 1), (-0.92, -0.36, 1.42))
        make_box(shop, "shopkeeper-hat", (0.62, 0.5, 0.16), (0.1, 0.08, 0.06, 1), (-0.92, -0.36, 1.7))
        make_box(shop, "shopkeeper-eye-left", (0.07, 0.035, 0.07), (0.03, 0.03, 0.03, 1), (-1.02, -0.58, 1.45))
        make_box(shop, "shopkeeper-eye-right", (0.07, 0.035, 0.07), (0.03, 0.03, 0.03, 1), (-0.82, -0.58, 1.45))

        for index, (x, height, color) in enumerate(
            (
                (-0.05, 1.25, (0.48, 0.24, 0.1, 1)),
                (0.45, 1.45, (0.74, 0.42, 0.18, 1)),
                (0.95, 1.62, (0.35, 0.56, 0.52, 1)),
                (1.45, 1.82, (0.84, 0.82, 0.66, 1)),
            )
        ):
            make_box(shop, f"sale-rod-{index}", (0.08, height, 0.08), color, (x, -0.5, 0.95), (0, 0, -24))
            make_box(shop, f"sale-rod-hook-{index}", (0.18, 0.04, 0.18), gold, (x + 0.28, -0.93, 0.42 + index * 0.06))

        make_box(shop, "coin-chest", (0.6, 0.42, 0.32), (0.24, 0.12, 0.06, 1), (-1.55, -0.72, 0.72))
        make_box(shop, "coin-chest-band", (0.66, 0.08, 0.36), gold, (-1.55, -0.72, 0.74))
        make_box(shop, "tackle-crate", (0.56, 0.46, 0.34), (0.36, 0.2, 0.08, 1), (1.55, -0.72, 0.74), (0, 0, 6))
        make_box(shop, "tackle-crate-slat-a", (0.6, 0.06, 0.38), (0.22, 0.12, 0.05, 1), (1.55, -0.96, 0.76), (0, 0, 6))
        make_box(shop, "blue-bait-jar", (0.18, 0.18, 0.28), (0.34, 0.72, 0.95, 0.68), (1.1, -0.95, 0.88))
        make_box(shop, "red-bait-jar", (0.16, 0.16, 0.24), (0.88, 0.24, 0.22, 0.66), (1.32, -1.02, 0.86))
        make_box(shop, "coiled-line-a", (0.46, 0.06, 0.06), (0.8, 0.72, 0.52, 1), (0.84, -1.08, 0.78), (0, 0, 18))
        make_box(shop, "coiled-line-b", (0.06, 0.38, 0.06), (0.8, 0.72, 0.52, 1), (0.84, -1.08, 0.78), (0, 0, 18))
        for index in range(3):
            make_box(
                shop,
                f"counter-coin-{index}",
                (0.16, 0.16, 0.035),
                gold,
                (-0.35 + index * 0.18, -1.05, 0.75),
                (0, 0, self.rng.uniform(-20, 20)),
            )

    def _build_forge(self):
        forge = self.render.attachNewNode("forge")
        forge.setPos(FORGE_SPOT)

        stone = (0.38, 0.35, 0.32, 1)
        dark_iron = (0.18, 0.16, 0.14, 1)
        ember = (1.0, 0.42, 0.08, 0.72)
        wood = (0.42, 0.25, 0.12, 1)

        make_box(forge, "forge-platform", (3.6, 2.8, 0.14), (0.28, 0.24, 0.18, 1), (0, 0, 0.02))
        make_box(forge, "anvil-base", (0.7, 0.5, 0.45), dark_iron, (0, -0.3, 0.32))
        make_box(forge, "anvil-top", (0.9, 0.55, 0.12), dark_iron, (0, -0.3, 0.6))
        make_box(forge, "anvil-horn", (0.22, 0.18, 0.18), dark_iron, (0.55, -0.3, 0.52), (0, 0, -15))
        make_box(forge, "furnace-body", (0.9, 0.8, 1.1), stone, (-0.05, 0.55, 0.62))
        make_box(forge, "furnace-chimney", (0.35, 0.35, 0.7), stone, (-0.05, 0.55, 1.52))
        make_box(forge, "furnace-mouth", (0.45, 0.12, 0.38), (0.06, 0.04, 0.03, 1), (-0.05, 0.12, 0.45))
        ember_node = make_box(forge, "furnace-ember", (0.38, 0.08, 0.3), ember, (-0.05, 0.1, 0.45))
        self._add_animated_detail(ember_node, bob_amount=0.01, sway_amount=0, speed=4.0, phase=0)
        make_box(forge, "forge-hammer", (0.12, 0.12, 0.55), wood, (0.65, 0.2, 0.42), (0, -18, 12))
        make_box(forge, "forge-hammer-head", (0.22, 0.18, 0.14), dark_iron, (0.65, 0.18, 0.72), (0, -18, 12))
        make_box(forge, "forge-tongs", (0.08, 0.08, 0.48), dark_iron, (0.45, -0.65, 0.32), (0, 24, 0))
        make_box(forge, "forge-bucket", (0.32, 0.32, 0.28), wood, (-0.75, -0.55, 0.22))
        make_box(forge, "forge-bucket-water", (0.26, 0.26, 0.04), (0.2, 0.42, 0.58, 0.7), (-0.75, -0.55, 0.38))
        make_box(forge, "forge-sign-post", (0.12, 0.12, 1.5), wood, (1.45, -0.6, 0.75))
        make_box(forge, "forge-sign-board", (1.2, 0.14, 0.42), (0.12, 0.08, 0.04, 1), (1.45, -0.7, 1.65))

    def _build_boss_arena(self):
        arena = self.render.attachNewNode("boss-arena")
        arena.setPos(BOSS_ARENA_CENTER)

        stone = (0.32, 0.3, 0.28, 1)
        dark_stone = (0.18, 0.16, 0.14, 1)
        torch_color = (1.0, 0.65, 0.18, 0.8)

        make_flat_blob(
            arena, "boss-floor", (0, 0, 0.01), BOSS_ARENA_RADIUS, BOSS_ARENA_RADIUS,
            (0.26, 0.22, 0.18, 1), points=24, wobble=0.06, rotation_degrees=0, seed=901,
        )

        pillar_count = 8
        for i in range(pillar_count):
            angle = math.pi * 2.0 * i / pillar_count
            px = math.cos(angle) * (BOSS_ARENA_RADIUS - 0.6)
            py = math.sin(angle) * (BOSS_ARENA_RADIUS - 0.6)
            make_box(arena, f"boss-pillar-{i}", (0.5, 0.5, 2.8), stone, (px, py, 1.4))
            make_box(arena, f"boss-pillar-cap-{i}", (0.65, 0.65, 0.2), dark_stone, (px, py, 2.9))

        for i in range(0, pillar_count, 2):
            angle = math.pi * 2.0 * i / pillar_count
            tx = math.cos(angle) * (BOSS_ARENA_RADIUS - 0.3)
            ty = math.sin(angle) * (BOSS_ARENA_RADIUS - 0.3)
            make_box(arena, f"boss-torch-post-{i}", (0.12, 0.12, 0.65), dark_stone, (tx, ty, 3.15))
            torch = make_box(arena, f"boss-torch-flame-{i}", (0.18, 0.18, 0.22), torch_color, (tx, ty, 3.55))
            self._add_animated_detail(torch, bob_amount=0.03, sway_amount=0, speed=5.0, phase=i * 0.7)

        make_box(arena, "boss-throne-base", (1.8, 1.2, 0.55), dark_stone, (0, BOSS_ARENA_RADIUS - 1.8, 0.28))
        make_box(arena, "boss-throne-back", (1.4, 0.35, 2.2), stone, (0, BOSS_ARENA_RADIUS - 1.4, 1.38))
        make_box(arena, "boss-throne-left", (0.3, 0.8, 1.2), stone, (-0.7, BOSS_ARENA_RADIUS - 1.8, 0.88))
        make_box(arena, "boss-throne-right", (0.3, 0.8, 1.2), stone, (0.7, BOSS_ARENA_RADIUS - 1.8, 0.88))
        make_box(arena, "boss-throne-crown-l", (0.22, 0.22, 0.35), (0.85, 0.72, 0.22, 1), (-0.45, BOSS_ARENA_RADIUS - 1.3, 2.65))
        make_box(arena, "boss-throne-crown-r", (0.22, 0.22, 0.35), (0.85, 0.72, 0.22, 1), (0.45, BOSS_ARENA_RADIUS - 1.3, 2.65))

        gate_color = (0.52, 0.35, 0.15, 1)
        make_box(arena, "boss-gate-left", (0.4, 0.4, 2.4), gate_color, (-2.2, -(BOSS_ARENA_RADIUS - 0.6), 1.2))
        make_box(arena, "boss-gate-right", (0.4, 0.4, 2.4), gate_color, (2.2, -(BOSS_ARENA_RADIUS - 0.6), 1.2))
        make_box(arena, "boss-gate-beam", (4.8, 0.35, 0.4), gate_color, (0, -(BOSS_ARENA_RADIUS - 0.6), 2.5))

    def _build_imported_player(self) -> bool:
        self.player = self.render.attachNewNode("player")
        knight = _load_obj_asset(QUATERNIUS_KNIGHT_ASSET_DIR, "KnightCharacter")
        if knight is None:
            self.player.removeNode()
            self.player = None
            return False

        make_box(
            self.player,
            "player-ground-shadow",
            (0.82, 0.52, 0.035),
            (0.02, 0.025, 0.02, 0.28),
            (0, 0.06, 0.03),
        )
        self.player_visual_model = _copy_imported_model(
            self.player,
            "player-knight-model",
            QUATERNIUS_KNIGHT_ASSET_DIR,
            "KnightCharacter",
            0.34,
            (0, 0.0, 0.0),
            IMPORTED_PLAYER_BASE_HPR,
            ink=True,
        )
        self.left_leg = self.player.attachNewNode("left-leg")
        self.left_leg.setPos(-0.18, 0.02, 0.5)
        self.right_leg = self.player.attachNewNode("right-leg")
        self.right_leg.setPos(0.18, 0.02, 0.5)
        self.left_arm = self.player.attachNewNode("left-arm")
        self.left_arm.setPos(-0.37, 0.1, 1.12)
        self.left_arm.setHpr(8, -9, -8)
        self.right_arm = self.player.attachNewNode("right-arm")
        self.right_arm.setPos(0.38, 0.14, 1.12)
        self.right_arm.setHpr(-10, -12, 8)
        make_box(
            self.right_arm,
            "right-grip-gauntlet",
            (0.16, 0.16, 0.15),
            (0.45, 0.46, 0.48, 1),
            (0, 0.12, -0.2),
        )
        self.weapon_pivot = self.right_arm.attachNewNode("weapon-pivot")
        self.weapon_pivot.setPos(0.0, 0.24, -0.22)
        self.weapon_pivot.setHpr(4, 18, -8)
        self.weapon_root = self.weapon_pivot.attachNewNode("weapon-root")
        self._build_weapon_model(None)
        self._build_slash_trail()
        self.player.setPos(0, 3.0, 0)

        if self.camera is not None:
            self.camera.setPos(0, -17, 14)
            self.camera.lookAt(self.player)
        return True

    def _set_imported_player_pose(
        self,
        heading_offset: float = 0.0,
        pitch_offset: float = 0.0,
        roll_offset: float = 0.0,
        z_offset: float = 0.0,
    ):
        if self.player_visual_model is None:
            return

        base_h, base_p, base_r = IMPORTED_PLAYER_BASE_HPR
        self.player_visual_model.setHpr(
            base_h + heading_offset,
            base_p + pitch_offset,
            base_r + roll_offset,
        )
        self.player_visual_model.setZ(z_offset)

    def _build_player(self):
        self.player = self.render.attachNewNode("player")
        self.player_visual_model = None
        make_box(
            self.player,
            "player-ground-shadow",
            (0.82, 0.52, 0.035),
            (0.02, 0.025, 0.02, 0.28),
            (0, 0.06, 0.03),
        )
        make_box(
            self.player,
            "player-tunic",
            (0.72, 0.5, 0.95),
            (0.12, 0.36, 0.45, 1),
            (0, 0, 0.82),
        )
        make_ellipsoid(
            self.player,
            "player-chest-shape",
            (0.38, 0.26, 0.43),
            (0.14, 0.42, 0.52, 1),
            (0, 0.03, 0.96),
            segments=10,
            rings=5,
        )
        make_box(
            self.player,
            "player-tunic-front-panel",
            (0.28, 0.04, 0.58),
            (0.09, 0.27, 0.36, 1),
            (0, 0.29, 0.86),
        )
        make_box(
            self.player,
            "player-tunic-hem",
            (0.8, 0.54, 0.08),
            (0.07, 0.22, 0.3, 1),
            (0, 0.03, 0.36),
        )
        make_box(
            self.player,
            "player-belt",
            (0.78, 0.54, 0.14),
            (0.18, 0.1, 0.06, 1),
            (0, 0.01, 0.58),
        )
        make_box(
            self.player,
            "player-belt-buckle",
            (0.16, 0.06, 0.16),
            (0.95, 0.74, 0.28, 1),
            (0, 0.3, 0.59),
        )
        make_box(
            self.player,
            "player-satchel",
            (0.34, 0.16, 0.36),
            (0.34, 0.18, 0.08, 1),
            (-0.48, -0.03, 0.72),
            (0, 0, -8),
        )
        make_box(
            self.player,
            "player-satchel-flap",
            (0.3, 0.18, 0.08),
            (0.24, 0.12, 0.05, 1),
            (-0.48, 0.05, 0.82),
            (0, 0, -8),
        )
        make_box(
            self.player,
            "player-head",
            (0.52, 0.48, 0.52),
            (0.9, 0.64, 0.44, 1),
            (0, 0.02, 1.48),
        )
        make_box(
            self.player,
            "player-hair",
            (0.58, 0.52, 0.18),
            (0.18, 0.1, 0.05, 1),
            (0, 0.0, 1.79),
        )
        make_box(
            self.player,
            "player-left-eye",
            (0.08, 0.04, 0.08),
            (0.05, 0.06, 0.07, 1),
            (-0.13, 0.27, 1.53),
        )
        make_box(
            self.player,
            "player-right-eye",
            (0.08, 0.04, 0.08),
            (0.05, 0.06, 0.07, 1),
            (0.13, 0.27, 1.53),
        )
        make_box(
            self.player,
            "player-nose",
            (0.08, 0.08, 0.1),
            (0.8, 0.52, 0.36, 1),
            (0, 0.3, 1.43),
        )
        make_box(
            self.player,
            "player-mouth",
            (0.18, 0.035, 0.04),
            (0.28, 0.08, 0.08, 1),
            (0, 0.3, 1.33),
        )
        self.left_leg = self.player.attachNewNode("left-leg")
        self.left_leg.setPos(-0.19, 0, 0.52)
        make_box(
            self.left_leg,
            "player-left-leg",
            (0.22, 0.24, 0.55),
            (0.12, 0.15, 0.18, 1),
            (0, 0, -0.27),
        )
        make_box(
            self.left_leg,
            "player-left-boot",
            (0.28, 0.36, 0.16),
            (0.07, 0.05, 0.04, 1),
            (0, 0.05, -0.5),
        )
        make_box(
            self.left_leg,
            "player-left-boot-cuff",
            (0.3, 0.28, 0.07),
            (0.16, 0.1, 0.06, 1),
            (0, 0, -0.37),
        )
        make_box(
            self.left_leg,
            "player-left-boot-toe",
            (0.24, 0.18, 0.08),
            (0.05, 0.035, 0.03, 1),
            (0, 0.19, -0.53),
        )

        self.right_leg = self.player.attachNewNode("right-leg")
        self.right_leg.setPos(0.19, 0, 0.52)
        make_box(
            self.right_leg,
            "player-right-leg",
            (0.22, 0.24, 0.55),
            (0.12, 0.15, 0.18, 1),
            (0, 0, -0.27),
        )
        make_box(
            self.right_leg,
            "player-right-boot",
            (0.28, 0.36, 0.16),
            (0.07, 0.05, 0.04, 1),
            (0, 0.05, -0.5),
        )
        make_box(
            self.right_leg,
            "player-right-boot-cuff",
            (0.3, 0.28, 0.07),
            (0.16, 0.1, 0.06, 1),
            (0, 0, -0.37),
        )
        make_box(
            self.right_leg,
            "player-right-boot-toe",
            (0.24, 0.18, 0.08),
            (0.05, 0.035, 0.03, 1),
            (0, 0.19, -0.53),
        )

        self.left_arm = self.player.attachNewNode("left-arm")
        self.left_arm.setPos(-0.39, 0.03, 1.08)
        self.left_arm.setHpr(8, -9, -8)
        make_box(
            self.left_arm,
            "left-sleeve",
            (0.19, 0.2, 0.66),
            (0.1, 0.31, 0.39, 1),
            (0, 0.1, -0.28),
            (0, 0, -7),
        )
        make_box(
            self.left_arm,
            "left-cuff",
            (0.2, 0.22, 0.1),
            (0.07, 0.22, 0.3, 1),
            (0, 0.18, -0.56),
            (0, 0, -7),
        )
        make_box(
            self.left_arm,
            "left-hand",
            (0.18, 0.17, 0.15),
            (0.9, 0.64, 0.44, 1),
            (0, 0.24, -0.65),
        )

        self.right_arm = self.player.attachNewNode("right-arm")
        self.right_arm.setPos(0.39, 0.03, 1.08)
        self.right_arm.setHpr(-10, -12, 8)
        make_box(
            self.right_arm,
            "right-sleeve",
            (0.19, 0.2, 0.66),
            (0.1, 0.31, 0.39, 1),
            (0, 0.12, -0.28),
            (0, 0, 7),
        )
        make_box(
            self.right_arm,
            "right-cuff",
            (0.2, 0.22, 0.1),
            (0.07, 0.22, 0.3, 1),
            (0, 0.2, -0.56),
            (0, 0, 7),
        )
        make_box(
            self.right_arm,
            "right-hand",
            (0.19, 0.18, 0.16),
            (0.9, 0.64, 0.44, 1),
            (0, 0.28, -0.65),
        )
        self.weapon_pivot = self.right_arm.attachNewNode("weapon-pivot")
        self.weapon_pivot.setPos(0, 0.28, -0.5)
        self.weapon_pivot.setHpr(4, 18, -8)
        self.weapon_root = self.weapon_pivot.attachNewNode("weapon-root")
        self._build_weapon_model(None)
        self._build_slash_trail()
        self.player.setPos(0, 3.0, 0)

        if self.camera is not None:
            self.camera.setPos(0, -17, 14)
            self.camera.lookAt(self.player)

    def _build_pet(self):
        self.pet = self.render.attachNewNode("pet-tiger-cub")
        self.pet.setPos(-0.9, 2.15, 0)
        self.pet_visual = self.pet.attachNewNode("pet-tiger-visual")

        orange = (0.98, 0.52, 0.14, 1)
        light_orange = (1.0, 0.62, 0.22, 1)
        dark = (0.08, 0.055, 0.035, 1)
        cream = (1.0, 0.86, 0.58, 1)
        white = (1.0, 0.96, 0.86, 1)
        pink = (0.92, 0.48, 0.44, 1)
        make_box(self.pet, "pet-shadow", (0.9, 0.58, 0.03), (0.02, 0.02, 0.018, 0.26), (0, 0.02, 0.035))
        make_ellipsoid(self.pet_visual, "pet-body", (0.45, 0.66, 0.28), orange, (0, 0, 0.36), segments=12, rings=6)
        make_ellipsoid(self.pet_visual, "pet-chest-belly", (0.26, 0.36, 0.12), cream, (0, 0.26, 0.25), segments=8, rings=4)
        make_box(self.pet_visual, "pet-back-stripe", (0.09, 0.84, 0.085), dark, (0, -0.06, 0.64))
        for index, y in enumerate((-0.44, -0.24, -0.04, 0.17, 0.38)):
            make_box(self.pet_visual, f"pet-side-stripe-left-{index}", (0.075, 0.22, 0.08), dark, (-0.36, y, 0.5), (0, 0, -25 + index * 5))
            make_box(self.pet_visual, f"pet-side-stripe-right-{index}", (0.075, 0.22, 0.08), dark, (0.36, y, 0.5), (0, 0, 25 - index * 5))
        for index, y in enumerate((-0.38, -0.1, 0.2)):
            make_box(self.pet_visual, f"pet-rib-stripe-left-{index}", (0.055, 0.16, 0.06), dark, (-0.43, y, 0.36), (0, 0, 48))
            make_box(self.pet_visual, f"pet-rib-stripe-right-{index}", (0.055, 0.16, 0.06), dark, (0.43, y, 0.36), (0, 0, -48))

        self.pet_head = self.pet_visual.attachNewNode("pet-head-pivot")
        self.pet_head.setPos(0, 0.66, 0.52)
        make_ellipsoid(self.pet_head, "pet-head", (0.29, 0.27, 0.24), orange, segments=10, rings=5)
        make_ellipsoid(self.pet_head, "pet-left-cheek", (0.11, 0.08, 0.08), white, (-0.1, 0.2, -0.08), segments=7, rings=4)
        make_ellipsoid(self.pet_head, "pet-right-cheek", (0.11, 0.08, 0.08), white, (0.1, 0.2, -0.08), segments=7, rings=4)
        make_box(self.pet_head, "pet-muzzle", (0.2, 0.17, 0.1), cream, (0, 0.23, -0.08))
        make_box(self.pet_head, "pet-nose", (0.075, 0.045, 0.05), dark, (0, 0.34, -0.02))
        make_box(self.pet_head, "pet-mouth", (0.11, 0.025, 0.025), dark, (0, 0.36, -0.09))
        make_box(self.pet_head, "pet-eye-patch-left", (0.1, 0.035, 0.09), white, (-0.1, 0.2, 0.075), (0, 0, 5))
        make_box(self.pet_head, "pet-eye-patch-right", (0.1, 0.035, 0.09), white, (0.1, 0.2, 0.075), (0, 0, -5))
        make_box(self.pet_head, "pet-eye-left", (0.045, 0.035, 0.045), (0.02, 0.03, 0.025, 1), (-0.1, 0.225, 0.085))
        make_box(self.pet_head, "pet-eye-right", (0.045, 0.035, 0.045), (0.02, 0.03, 0.025, 1), (0.1, 0.225, 0.085))
        make_box(self.pet_head, "pet-eye-glint-left", (0.015, 0.012, 0.015), white, (-0.112, 0.25, 0.096))
        make_box(self.pet_head, "pet-eye-glint-right", (0.015, 0.012, 0.015), white, (0.088, 0.25, 0.096))
        make_box(self.pet_head, "pet-forehead-stripe-center", (0.055, 0.07, 0.13), dark, (0, 0.16, 0.18))
        make_box(self.pet_head, "pet-forehead-stripe-left", (0.045, 0.07, 0.12), dark, (-0.11, 0.14, 0.16), (0, 0, 32))
        make_box(self.pet_head, "pet-forehead-stripe-right", (0.045, 0.07, 0.12), dark, (0.11, 0.14, 0.16), (0, 0, -32))
        make_box(self.pet_head, "pet-cheek-stripe-left-a", (0.035, 0.12, 0.03), dark, (-0.24, 0.17, 0.02), (0, 0, -24))
        make_box(self.pet_head, "pet-cheek-stripe-left-b", (0.035, 0.12, 0.03), dark, (-0.24, 0.17, -0.07), (0, 0, -34))
        make_box(self.pet_head, "pet-cheek-stripe-right-a", (0.035, 0.12, 0.03), dark, (0.24, 0.17, 0.02), (0, 0, 24))
        make_box(self.pet_head, "pet-cheek-stripe-right-b", (0.035, 0.12, 0.03), dark, (0.24, 0.17, -0.07), (0, 0, 34))
        make_box(self.pet_head, "pet-whisker-left-a", (0.2, 0.018, 0.018), dark, (-0.23, 0.3, -0.055), (0, 0, -10))
        make_box(self.pet_head, "pet-whisker-left-b", (0.18, 0.018, 0.018), dark, (-0.22, 0.3, -0.105), (0, 0, -24))
        make_box(self.pet_head, "pet-whisker-right-a", (0.2, 0.018, 0.018), dark, (0.23, 0.3, -0.055), (0, 0, 10))
        make_box(self.pet_head, "pet-whisker-right-b", (0.18, 0.018, 0.018), dark, (0.22, 0.3, -0.105), (0, 0, 24))
        make_ellipsoid(self.pet_head, "pet-ear-left", (0.09, 0.055, 0.14), orange, (-0.18, 0.0, 0.22), hpr=(0, 0, -15), segments=7, rings=4)
        make_ellipsoid(self.pet_head, "pet-ear-right", (0.09, 0.055, 0.14), orange, (0.18, 0.0, 0.22), hpr=(0, 0, 15), segments=7, rings=4)
        make_ellipsoid(self.pet_head, "pet-ear-left-inner", (0.045, 0.03, 0.08), pink, (-0.18, 0.03, 0.22), hpr=(0, 0, -15), segments=6, rings=3)
        make_ellipsoid(self.pet_head, "pet-ear-right-inner", (0.045, 0.03, 0.08), pink, (0.18, 0.03, 0.22), hpr=(0, 0, 15), segments=6, rings=3)

        self.pet_tail = self.pet_visual.attachNewNode("pet-tail-pivot")
        self.pet_tail.setPos(0, -0.56, 0.42)
        make_box(self.pet_tail, "pet-tail", (0.11, 0.62, 0.11), light_orange, (0, -0.28, 0.02), (34, 0, 0))
        for index, y in enumerate((-0.12, -0.28, -0.44)):
            make_box(self.pet_tail, f"pet-tail-ring-{index}", (0.13, 0.055, 0.13), dark, (0, y, 0.02), (34, 0, 0))
        make_box(self.pet_tail, "pet-tail-tip", (0.13, 0.16, 0.13), dark, (0, -0.59, 0.02), (34, 0, 0))

        self.pet_left_foot = self.pet_visual.attachNewNode("pet-left-foot-pivot")
        self.pet_left_foot.setPos(-0.22, 0.22, 0.18)
        make_box(self.pet_left_foot, "pet-left-paw", (0.16, 0.2, 0.1), cream, (0, 0, -0.05))
        make_box(self.pet_left_foot, "pet-left-paw-stripe", (0.15, 0.03, 0.035), dark, (0, 0.02, 0.02))
        self.pet_right_foot = self.pet_visual.attachNewNode("pet-right-foot-pivot")
        self.pet_right_foot.setPos(0.22, 0.22, 0.18)
        make_box(self.pet_right_foot, "pet-right-paw", (0.16, 0.2, 0.1), cream, (0, 0, -0.05))
        make_box(self.pet_right_foot, "pet-right-paw-stripe", (0.15, 0.03, 0.035), dark, (0, 0.02, 0.02))
        for index, x in enumerate((-0.24, 0.24)):
            make_box(self.pet_visual, f"pet-back-paw-{index}", (0.17, 0.2, 0.1), cream, (x, -0.32, 0.12))
            make_box(self.pet_visual, f"pet-back-paw-stripe-{index}", (0.14, 0.035, 0.035), dark, (x, -0.29, 0.18))

    def _build_weapon_model(self, weapon: Optional[Weapon]):
        if self.weapon_root is not None:
            self.weapon_root.removeNode()

        self.weapon_root = self.weapon_pivot.attachNewNode("weapon-root")
        self._populate_weapon_model(self.weapon_root, weapon, preview=False)

    def _imported_weapon_asset(self, weapon: Weapon) -> Optional[str]:
        weapon_type = weapon.weapon_type
        if weapon_type == "bow":
            if weapon.rarity == "mythic":
                return "Bow_Golden"
            if weapon.rarity == "relic":
                return "Bow_Evil"
            return "Bow_Wooden"
        if weapon_type == "saber" and weapon.rarity == "mythic":
            return "Sword_Golden"
        if weapon_type == "axe" and weapon.rarity in {"relic", "mythic"}:
            return "Axe_Double"
        return WEAPON_ASSET_BY_TYPE.get(weapon_type)

    def _imported_weapon_scale(self, asset_name: str, preview: bool) -> float:
        scale_by_asset = {
            "Spear": 0.2,
            "Claymore": 0.28,
            "Sword_Big": 0.3,
            "Hammer_Double": 0.31,
            "Axe": 0.33,
            "Axe_Double": 0.31,
            "Bow_Wooden": 0.34,
            "Bow_Evil": 0.34,
            "Bow_Golden": 0.34,
        }
        base_scale = scale_by_asset.get(asset_name, 0.35)
        return base_scale * (1.08 if preview else 1.0)

    def _populate_imported_weapon_model(self, parent, weapon: Weapon, preview: bool) -> bool:
        asset_name = self._imported_weapon_asset(weapon)
        if asset_name is None:
            return False

        weapon_model = _copy_imported_model(
            parent,
            f"weapon-{asset_name.lower()}",
            QUATERNIUS_WEAPON_ASSET_DIR,
            asset_name,
            self._imported_weapon_scale(asset_name, preview),
            (0, 0.03, 0.02),
            ink=True,
        )
        if weapon_model is None:
            return False

        glow = weapon_glow_color(weapon)
        weapon_type = weapon.weapon_type
        if weapon_type == "bow":
            make_box(parent, "bow-ready-arrow", (0.045, 1.25, 0.045), glow, (0.18, 0.42, 0.08))
            make_flat_prism(parent, "bow-ready-arrow-head", ((0.18, 1.12), (0.3, 0.92), (0.06, 0.92)), 0.09, glow, (0, 0, 0.08))
            make_box(parent, "bow-magic-string", (0.03, 1.65, 0.03), glow, (0.32, 0.0, 0.02))
        elif weapon_type == "axe":
            make_box(parent, "axe-rune-one", (0.12, 0.04, 0.42), glow, (0.38, 1.3, 0.34), (0, 0, 22))
            make_box(parent, "axe-rune-two", (0.12, 0.04, 0.42), glow, (0.52, 1.08, 0.34), (0, 0, -22))
        elif weapon_type == "mace":
            make_box(parent, "mace-halo-east", (0.82, 0.06, 0.06), glow, (0, 1.18, 0.08), (0, 0, 0))
            make_box(parent, "mace-halo-north", (0.06, 0.82, 0.06), glow, (0, 1.18, 0.08), (0, 0, 0))
        elif weapon_type == "spear":
            make_box(parent, "spear-banner", (0.42, 0.08, 0.32), glow, (0.22, 1.16, -0.14), (0, 0, -14))
            make_box(parent, "spear-tip-star", (0.42, 0.05, 0.05), glow, (0, 1.54, 0.08), (0, 0, 35))
        else:
            make_box(parent, "blade-rune-line", (0.045, 1.12, 0.045), glow, (0.02, 1.05, 0.13))
            make_box(parent, "blade-rune-cross", (0.34, 0.045, 0.045), glow, (0.02, 1.44, 0.13), (0, 0, 28))

        if preview:
            make_box(parent, "preview-shadow", (1.12, 0.22, 0.035), (0, 0, 0, 0.24), (0, 0.82, -0.58))
        return True

    def _populate_weapon_model(self, parent, weapon: Optional[Weapon], preview: bool):
        wood = (0.23, 0.13, 0.06, 1)
        leather = (0.12, 0.07, 0.04, 1)
        metal = (0.7, 0.74, 0.76, 1)
        brass = (0.88, 0.62, 0.24, 1)
        glow = weapon_glow_color(weapon)
        shine = (0.88, 0.96, 1.0, 0.66)

        if weapon is None:
            rod_colors = (
                ((0.23, 0.13, 0.06, 1), (0.32, 0.18, 0.08, 1), (0.85, 0.92, 1.0, 0.45)),
                ((0.34, 0.16, 0.07, 1), (0.9, 0.48, 0.16, 1), (0.9, 0.82, 0.62, 0.52)),
                ((0.16, 0.36, 0.34, 1), (0.55, 0.82, 0.88, 1), (0.48, 0.9, 1.0, 0.58)),
                ((0.72, 0.68, 0.52, 1), (0.95, 0.86, 0.38, 1), (1.0, 0.9, 0.45, 0.68)),
            )
            clamped_rod_tier = min(self.rod_tier, len(rod_colors) - 1)
            rod_color, wrap_color, line_color = rod_colors[clamped_rod_tier]
            rod_length = 1.7 + clamped_rod_tier * 0.12
            make_box(
                parent,
                "fishing-rod",
                (0.07, rod_length, 0.07),
                rod_color,
                (0, rod_length * 0.5, 0.06),
                (0, -8, 0),
            )
            make_box(
                parent,
                "fishing-rod-wrap",
                (0.1, 0.34, 0.1),
                wrap_color,
                (0, 0.46, 0.04),
                (0, -8, 0),
            )
            if clamped_rod_tier >= 1:
                make_box(
                    parent,
                    "fishing-rod-tip-band",
                    (0.12, 0.1, 0.12),
                    wrap_color,
                    (0, rod_length - 0.04, -0.08),
                    (0, -8, 0),
                )
            if clamped_rod_tier >= 2:
                make_box(
                    parent,
                    "fishing-rod-rune",
                    (0.18, 0.05, 0.18),
                    line_color,
                    (0, 1.05, 0.16),
                    (0, -8, 35),
                )
            make_box(
                parent,
                "fishing-line",
                (0.025, 1.05, 0.025),
                line_color,
                (0.0, 1.72, -0.38),
                (0, -34, 0),
            )
            make_box(
                parent,
                "bobber",
                (0.16, 0.16, 0.16),
                wrap_color if clamped_rod_tier >= 3 else (0.95, 0.14, 0.12, 1),
                (0, 2.18, -0.78),
            )
            return

        weapon_type = weapon.weapon_type
        if self._populate_imported_weapon_model(parent, weapon, preview):
            return

        make_box(parent, "grip", (0.13, 0.58, 0.13), leather, (0, 0.27, 0))

        if weapon_type == "staff":
            make_box(parent, "staff-shaft", (0.11, 1.7, 0.11), wood, (0, 1.02, 0))
            make_box(parent, "staff-wrap-low", (0.15, 0.18, 0.15), leather, (0, 0.48, 0))
            make_box(parent, "staff-wrap-high", (0.15, 0.18, 0.15), leather, (0, 1.22, 0))
            make_ellipsoid(parent, "staff-orb", (0.2, 0.2, 0.2), glow, (0, 1.88, 0.0), segments=10, rings=5)
            make_box(parent, "staff-prong-left", (0.08, 0.42, 0.08), brass, (-0.18, 1.72, 0.0), (0, 0, -20))
            make_box(parent, "staff-prong-right", (0.08, 0.42, 0.08), brass, (0.18, 1.72, 0.0), (0, 0, 20))
            make_box(parent, "staff-star-a", (0.5, 0.05, 0.05), glow, (0, 1.88, 0), (0, 0, 35))
            make_box(parent, "staff-star-b", (0.05, 0.5, 0.05), glow, (0, 1.88, 0), (0, 0, 35))
        elif weapon_type == "bow":
            make_box(parent, "bow-grip", (0.16, 0.42, 0.14), leather, (0, 0.86, 0))
            make_box(parent, "bow-upper-limb", (0.12, 0.96, 0.1), wood, (-0.28, 1.26, 0.0), (0, 0, -18))
            make_box(parent, "bow-lower-limb", (0.12, 0.96, 0.1), wood, (0.28, 0.58, 0.0), (0, 0, -18))
            make_box(parent, "bow-string", (0.035, 1.76, 0.035), glow, (0.3, 0.94, 0.04), (0, 0, 0))
            make_box(parent, "bow-arrow-shaft", (0.06, 1.18, 0.06), metal, (0, 1.05, 0.12), (0, 0, 0))
            make_flat_prism(parent, "bow-arrow-head", ((0, 1.78), (0.12, 1.58), (-0.12, 1.58)), 0.12, glow, (0, 0, 0.12))
            make_box(parent, "bow-fletching-left", (0.16, 0.05, 0.06), brass, (-0.08, 0.48, 0.12), (0, 0, -25))
            make_box(parent, "bow-fletching-right", (0.16, 0.05, 0.06), brass, (0.08, 0.48, 0.12), (0, 0, 25))
        elif weapon_type == "crossbow":
            make_box(parent, "crossbow-stock", (0.16, 1.32, 0.14), wood, (0, 0.9, 0.0))
            make_box(parent, "crossbow-arms", (1.05, 0.1, 0.1), wood, (0, 1.26, 0.02))
            make_box(parent, "crossbow-string-left", (0.48, 0.035, 0.035), glow, (-0.27, 1.08, 0.08), (0, 0, -22))
            make_box(parent, "crossbow-string-right", (0.48, 0.035, 0.035), glow, (0.27, 1.08, 0.08), (0, 0, 22))
            make_box(parent, "crossbow-trigger", (0.22, 0.08, 0.12), brass, (0, 0.56, -0.08))
            make_box(parent, "crossbow-bolt", (0.07, 1.02, 0.07), metal, (0, 1.18, 0.16))
            make_flat_prism(parent, "crossbow-bolt-head", ((0, 1.78), (0.13, 1.58), (-0.13, 1.58)), 0.14, glow, (0, 0, 0.16))
        elif weapon_type in {"saber", "falchion"}:
            make_box(parent, "guard", (0.58, 0.08, 0.11), brass, (0, 0.58, 0))
            if weapon_type == "saber":
                blade_points = (
                    (-0.08, 0.58),
                    (0.08, 0.58),
                    (0.11, 1.42),
                    (0.0, 1.88),
                    (-0.09, 1.42),
                )
                glow_points = (
                    (-0.13, 0.56),
                    (0.13, 0.56),
                    (0.17, 1.45),
                    (0.0, 1.98),
                    (-0.15, 1.45),
                )
                shine_x = -0.04
            else:
                blade_points = (
                    (-0.08, 0.58),
                    (0.14, 0.58),
                    (0.28, 1.18),
                    (0.22, 1.68),
                    (0.02, 1.94),
                    (-0.13, 1.12),
                )
                glow_points = (
                    (-0.13, 0.56),
                    (0.2, 0.56),
                    (0.36, 1.2),
                    (0.28, 1.74),
                    (0.02, 2.04),
                    (-0.2, 1.12),
                )
                shine_x = 0.04
            make_flat_prism(
                parent,
                "blade",
                blade_points,
                0.1,
                metal,
                (0, 0, 0.04),
            )
            make_flat_prism(
                parent,
                "blade-glow",
                glow_points,
                0.13,
                glow,
                (0, 0, 0.035),
            )
            make_box(parent, "blade-shine", (0.035, 0.82, 0.035), shine, (shine_x, 1.16, 0.12))
            if weapon_type == "saber":
                make_box(parent, "saber-moon-arc", (0.62, 0.08, 0.035), glow, (0.0, 1.45, 0.22), (0, 0, 28))
            else:
                make_box(parent, "falchion-back-spine", (0.09, 0.82, 0.1), brass, (0.22, 1.18, 0.11), (0, 0, 10))
                make_box(parent, "falchion-heavy-tip", (0.34, 0.22, 0.12), glow, (0.22, 1.68, 0.08), (0, 0, 18))
        elif weapon_type == "axe":
            make_box(parent, "axe-shaft", (0.12, 1.28, 0.12), wood, (0, 0.86, 0))
            axe_points = (
                (-0.44, 1.42),
                (-0.1, 1.2),
                (0.38, 1.18),
                (0.66, 1.38),
                (0.56, 1.72),
                (0.18, 1.86),
                (-0.12, 1.72),
            )
            make_flat_prism(parent, "axe-head", axe_points, 0.28, metal, (0, 0, 0.08))
            make_flat_prism(parent, "axe-glow", axe_points, 0.34, glow, (0, 0, 0.07))
            make_flat_prism(
                parent,
                "axe-cutting-edge",
                ((0.42, 1.22), (0.7, 1.38), (0.58, 1.72), (0.32, 1.82)),
                0.32,
                shine,
                (0, 0, 0.13),
            )
            make_box(parent, "axe-rune-one", (0.11, 0.04, 0.42), glow, (0.22, 1.62, 0.42), (0, 0, 22))
            make_box(parent, "axe-rune-two", (0.11, 0.04, 0.42), glow, (0.38, 1.44, 0.42), (0, 0, -22))
        elif weapon_type == "mace":
            make_box(parent, "mace-shaft", (0.13, 1.0, 0.13), wood, (0, 0.75, 0))
            mace_points = (
                (-0.25, 1.18),
                (0.0, 1.06),
                (0.25, 1.18),
                (0.38, 1.36),
                (0.25, 1.56),
                (0.0, 1.68),
                (-0.25, 1.56),
                (-0.38, 1.36),
            )
            make_flat_prism(parent, "mace-head", mace_points, 0.5, metal)
            make_box(parent, "mace-spike-left", (0.22, 0.16, 0.16), metal, (-0.36, 1.36, 0))
            make_box(parent, "mace-spike-right", (0.22, 0.16, 0.16), metal, (0.36, 1.36, 0))
            make_box(parent, "mace-spike-front", (0.16, 0.22, 0.16), metal, (0, 1.72, 0))
            make_box(parent, "mace-spike-top", (0.16, 0.16, 0.22), metal, (0, 1.36, 0.36))
            make_box(parent, "mace-halo-east", (0.92, 0.06, 0.06), glow, (0, 1.36, 0), (0, 0, 0))
            make_box(parent, "mace-halo-north", (0.06, 0.92, 0.06), glow, (0, 1.36, 0), (0, 0, 0))
            make_flat_prism(parent, "mace-glow", mace_points, 0.58, glow)
        elif weapon_type == "rapier":
            make_box(parent, "rapier-guard", (0.62, 0.08, 0.12), brass, (0, 0.56, 0))
            make_box(parent, "rapier-basket", (0.38, 0.14, 0.38), brass, (0, 0.5, 0.02))
            make_box(parent, "rapier-basket-cross", (0.14, 0.38, 0.14), brass, (0, 0.5, 0.02))
            make_flat_prism(
                parent,
                "rapier-blade",
                ((-0.035, 0.58), (0.035, 0.58), (0.018, 1.92), (0.0, 2.08), (-0.018, 1.92)),
                0.06,
                metal,
                (0, 0, 0.02),
            )
            make_box(parent, "rapier-tip-star-a", (0.32, 0.035, 0.035), glow, (0, 1.95, 0.02), (0, 0, 45))
            make_box(parent, "rapier-tip-star-b", (0.035, 0.32, 0.035), glow, (0, 1.95, 0.02), (0, 0, 45))
            make_flat_prism(
                parent,
                "rapier-glow",
                ((-0.07, 0.56), (0.07, 0.56), (0.04, 1.92), (0.0, 2.18), (-0.04, 1.92)),
                0.1,
                glow,
                (0, 0, 0.02),
            )
        elif weapon_type == "spear":
            make_box(parent, "spear-shaft", (0.1, 1.52, 0.1), wood, (0, 0.92, 0))
            spear_tip = ((0.0, 2.06), (0.24, 1.72), (0.1, 1.48), (-0.1, 1.48), (-0.24, 1.72))
            make_flat_prism(parent, "spear-tip", spear_tip, 0.22, metal, (0, 0, 0.02))
            make_box(parent, "spear-crossguard", (0.54, 0.08, 0.1), brass, (0, 1.47, 0.0))
            make_box(parent, "spear-banner", (0.42, 0.08, 0.32), glow, (0.28, 1.25, -0.13), (0, 0, -14))
            make_box(parent, "spear-tip-star", (0.42, 0.06, 0.06), glow, (0, 1.98, 0.02), (0, 0, 35))
            make_flat_prism(parent, "spear-glow", spear_tip, 0.32, glow, (0, 0, 0.02))
        elif weapon_type == "cleaver":
            make_box(parent, "cleaver-guard", (0.44, 0.08, 0.12), brass, (0, 0.55, 0))
            cleaver_points = (
                (-0.1, 0.62),
                (0.46, 0.72),
                (0.52, 1.36),
                (0.34, 1.66),
                (-0.16, 1.48),
                (-0.22, 0.86),
            )
            make_flat_prism(parent, "cleaver-blade", cleaver_points, 0.16, metal, (0, 0, 0.08))
            make_flat_prism(
                parent,
                "cleaver-edge",
                ((0.28, 0.78), (0.54, 0.9), (0.5, 1.38), (0.32, 1.62), (0.24, 1.28)),
                0.18,
                (0.86, 0.9, 0.9, 1),
                (0, 0, 0.13),
            )
            make_box(parent, "cleaver-rune-hole", (0.16, 0.08, 0.16), (0.03, 0.04, 0.05, 1), (0.28, 1.15, 0.16))
            make_box(parent, "cleaver-top-notch", (0.2, 0.14, 0.13), (0.08, 0.09, 0.1, 1), (-0.08, 1.45, 0.14), (0, 0, -18))
            make_flat_prism(parent, "cleaver-glow", cleaver_points, 0.22, glow, (0, 0, 0.06))
        else:
            make_flat_prism(
                parent,
                "old-blade",
                ((-0.08, 0.58), (0.08, 0.58), (0.04, 1.62), (0.0, 1.82), (-0.06, 1.62)),
                0.1,
                metal,
                (0, 0, 0.04),
            )
            make_flat_prism(
                parent,
                "old-blade-glow",
                ((-0.13, 0.56), (0.13, 0.56), (0.07, 1.66), (0.0, 1.94), (-0.09, 1.66)),
                0.13,
                glow,
                (0, 0, 0.035),
            )

        if preview:
            make_box(parent, "preview-shadow", (1.12, 0.22, 0.035), (0, 0, 0, 0.24), (0, 0.82, -0.58))

    def _build_slash_trail(self):
        self.slash_root = self.player.attachNewNode("slash-trail")
        self.slash_root.setPos(0, 1.25, 0.96)
        self.slash_parts = [
            make_box(
                self.slash_root,
                "slash-aura-back",
                (0.16, 2.0, 0.06),
                (0.8, 0.95, 1.0, 0.14),
                (-0.48, 0.12, -0.14),
                (-48, 0, 0),
            ),
            make_box(
                self.slash_root,
                "slash-aura-mid",
                (0.18, 2.35, 0.07),
                (0.85, 0.98, 1.0, 0.26),
                (-0.12, 0.24, 0),
                (-16, 0, 0),
            ),
            make_box(
                self.slash_root,
                "slash-cutting-edge",
                (0.08, 2.55, 0.045),
                (1.0, 1.0, 0.88, 0.62),
                (0.18, 0.36, 0.08),
                (12, 0, 0),
            ),
            make_box(
                self.slash_root,
                "slash-aura-front",
                (0.12, 1.82, 0.06),
                (0.8, 0.95, 1.0, 0.2),
                (0.5, 0.18, 0.16),
                (48, 0, 0),
            ),
            make_box(
                self.slash_root,
                "slash-tail-one",
                (0.06, 0.72, 0.04),
                (1.0, 0.95, 0.65, 0.34),
                (-0.72, -0.18, -0.18),
                (-56, 0, 0),
            ),
            make_box(
                self.slash_root,
                "slash-tail-two",
                (0.05, 0.62, 0.035),
                (1.0, 0.95, 0.65, 0.26),
                (0.72, -0.12, 0.18),
                (56, 0, 0),
            ),
        ]
        self.slash_part_base_positions = [Vec3(part.getPos()) for part in self.slash_parts]
        self.slash_root.hide()

    def _start_swing(self, powered: bool = False):
        if self.right_arm is None or self.weapon_pivot is None:
            return

        self.swing_duration = 0.52 if powered else 0.28
        self.swing_time = self.swing_duration
        self.swing_is_powered = powered
        if powered:
            self.swing_style = "powered"
        elif self.next_swing_vertical:
            self.swing_style = "vertical"
            self.next_swing_vertical = False
        else:
            self.swing_style = "horizontal"
            self.next_swing_vertical = True
        self.swing_spark_timer = 0.0
        self.swing_sparked = False
        if self.left_arm is not None:
            self.left_arm.setHpr(20 if powered else 14, -18, -12)
        color = weapon_glow_color(self.current_weapon)
        red, green, blue, alpha = color
        if self.current_weapon is None:
            red, green, blue, alpha = (0.85, 0.94, 1.0, 0.35)

        for index, part in enumerate(self.slash_parts):
            part_alpha = alpha * (0.36 + index * 0.12)
            if index == 2:
                part_alpha = max(part_alpha, 0.68)
            part.setColor(red, green, blue, min(part_alpha, 0.72))

        if self.slash_root is not None:
            self.slash_root.setScale(0.7 if powered else 0.45)
            if self.swing_style == "vertical":
                self.slash_root.setH(-10)
                self.slash_root.setP(-72)
                self.slash_root.setR(0)
            else:
                self.slash_root.setH(-110 if powered else -65)
                self.slash_root.setP(0)
                self.slash_root.setR(0)
            self.slash_root.show()

    def _update_swing(self, dt: float):
        if self.right_arm is None or self.weapon_pivot is None:
            return

        if self.swing_time <= 0.0:
            self.swing_is_powered = False
            self.swing_style = "horizontal"
            if self.is_player_moving:
                stride = math.sin(self.walk_time)
                self.right_arm.setHpr(-10 + stride * 7.0, -12, 8)
            else:
                self.right_arm.setHpr(-10, -12, 8)
            self.weapon_pivot.setHpr(4, 18, -8)
            if self.slash_root is not None:
                self.slash_root.setColorScale(1, 1, 1, 1)
                self.slash_root.hide()
            return

        self.swing_time = max(0.0, self.swing_time - dt)
        progress = 1.0 - (self.swing_time / self.swing_duration)
        if self.swing_style == "vertical":
            if progress < 0.3:
                windup = progress / 0.3
                arm_heading = -8 + 18 * windup
                arm_pitch = -8 + 72 * windup
                arm_roll = 8 + 16 * windup
                weapon_roll = -8 - 10 * windup
                slash_alpha_scale = 0.32
            elif progress < 0.68:
                slash = (progress - 0.3) / 0.38
                snap = math.sin(slash * math.pi * 0.5)
                arm_heading = 10 - 18 * snap
                arm_pitch = 64 - 104 * snap
                arm_roll = 24 - 30 * snap
                weapon_roll = -18 + 28 * snap
                slash_alpha_scale = 1.0
            else:
                recover = (progress - 0.68) / 0.32
                ease = 1.0 - (1.0 - recover) * (1.0 - recover)
                arm_heading = -8 - 2 * ease
                arm_pitch = -40 + 28 * ease
                arm_roll = -6 + 14 * ease
                weapon_roll = 10 - 18 * ease
                slash_alpha_scale = max(0.0, 1.0 - recover)
        else:
            if progress < 0.28:
                windup = progress / 0.28
                arm_heading = -10 + 58 * windup
                arm_pitch = -12 - 14 * windup
                arm_roll = 8 + 20 * windup
                weapon_roll = -8 - 34 * windup
                slash_alpha_scale = 0.35
            elif progress < 0.64:
                slash = (progress - 0.28) / 0.36
                snap = math.sin(slash * math.pi * 0.5)
                arm_heading = 48 - 102 * snap
                arm_pitch = -26 + 8 * slash
                arm_roll = 28 - 38 * snap
                weapon_roll = -42 + 88 * snap
                slash_alpha_scale = 1.0
            else:
                recover = (progress - 0.64) / 0.36
                ease = 1.0 - (1.0 - recover) * (1.0 - recover)
                arm_heading = -54 + 44 * ease
                arm_pitch = -18 + 6 * ease
                arm_roll = -10 + 18 * ease
                weapon_roll = 46 - 54 * ease
                slash_alpha_scale = max(0.0, 1.0 - recover)

        power_scale = 1.35 if self.swing_is_powered else 1.0
        body_twist = math.sin(progress * math.pi) * (11.0 if self.swing_is_powered else 7.0)
        self.player.setR(self.player.getR() + body_twist * 0.08)
        self._set_imported_player_pose(
            heading_offset=body_twist * 0.65,
            pitch_offset=-2.5 - abs(body_twist) * 0.22,
            roll_offset=-body_twist * 0.42,
            z_offset=math.sin(progress * math.pi) * 0.025,
        )
        self.right_arm.setHpr(arm_heading, arm_pitch, arm_roll)
        if self.swing_style == "vertical":
            self.weapon_pivot.setHpr(
                4,
                66 - 112 * progress,
                weapon_roll,
            )
        else:
            self.weapon_pivot.setHpr(4, 18 - 8 * math.sin(progress * math.pi) * power_scale, weapon_roll * power_scale)
        if self.left_arm is not None:
            self.left_arm.setHpr(10 + body_twist * 0.5, -16, -10 - body_twist * 0.25)

        if self.slash_root is not None:
            slash_curve = math.sin(min(1.0, progress / 0.68) * math.pi)
            stretch = (0.55 + slash_curve * 1.08) * power_scale
            self.slash_root.setScale(stretch, stretch * (0.82 + slash_curve * 0.28), 1.0)
            if self.swing_style == "vertical":
                self.slash_root.setH(-10 + math.sin(progress * math.pi) * 18)
                self.slash_root.setP(-86 + 172 * progress)
                self.slash_root.setR(math.sin(progress * math.pi * 2.0) * 4.0)
            else:
                self.slash_root.setH((-110 if self.swing_is_powered else -82) + (220 if self.swing_is_powered else 168) * progress)
                self.slash_root.setP(-18 + 34 * slash_curve)
                self.slash_root.setR(math.sin(progress * math.pi * 2.0) * (9.0 if self.swing_is_powered else 5.0))
            self.slash_root.setColorScale(1, 1, 1, slash_alpha_scale)

            for index, (part, base_pos) in enumerate(
                zip(self.slash_parts, self.slash_part_base_positions)
            ):
                tail_wave = math.sin(progress * math.pi + index * 0.7)
                part.setY(base_pos.getY() + tail_wave * 0.08 - index * 0.012)

        if 0.33 <= progress <= 0.58:
            self.swing_spark_timer -= dt
            if self.swing_spark_timer <= 0.0:
                self.swing_spark_timer = 0.03 if self.swing_is_powered else 0.045
                self._spawn_slash_sparks(progress, big=self.swing_is_powered or not self.swing_sparked)
                self.swing_sparked = True

        if self.swing_time == 0.0:
            self.swing_style = "horizontal"
            if self.is_player_moving:
                stride = math.sin(self.walk_time)
                self.right_arm.setHpr(-10 + stride * 7.0, -12, 8)
            else:
                self.right_arm.setHpr(-10, -12, 8)
            self.weapon_pivot.setHpr(4, 18, -8)
            if self.left_arm is not None:
                self.left_arm.setHpr(8, -9, -8)
            if self.slash_root is not None:
                self.slash_root.setColorScale(1, 1, 1, 1)
                self.slash_root.hide()

    def _spawn_slash_sparks(self, progress: float, big: bool):
        color = weapon_glow_color(self.current_weapon)
        red, green, blue, alpha = color
        if self.current_weapon is None:
            red, green, blue, alpha = (0.85, 0.94, 1.0, 0.45)

        player_pos = self.player.getPos()
        heading = math.radians(self.player.getH())
        forward = Vec3(-math.sin(heading), math.cos(heading), 0)
        right = Vec3(math.cos(heading), math.sin(heading), 0)
        impact_side = -0.45 + progress * 1.4
        origin = player_pos + forward * 1.28 + right * impact_side + Vec3(0, 0, 1.05)
        count = 7 if big else 3
        for index in range(count):
            spread = (index - (count - 1) * 0.5) * 0.22
            velocity = (
                forward * self.rng.uniform(0.8, 1.9)
                + right * (spread + self.rng.uniform(-0.25, 0.25))
                + Vec3(0, 0, self.rng.uniform(1.4, 2.8))
            )
            self._spawn_hit_piece(
                name=f"slash-spark-{index}",
                size=(
                    self.rng.uniform(0.05, 0.1),
                    self.rng.uniform(0.12, 0.24),
                    self.rng.uniform(0.035, 0.07),
                ),
                color=(red, green, blue, min(0.78, max(alpha, 0.48))),
                pos=origin + right * self.rng.uniform(-0.2, 0.2),
                velocity=velocity,
                lifetime=self.rng.uniform(0.18, 0.34),
            )

    def _build_lights(self):
        self.render.setShaderAuto()

        ambient = AmbientLight("soft-ambient")
        ambient.setColor((0.18, 0.2, 0.22, 1))
        self.render.setLight(self.render.attachNewNode(ambient))

        sun = DirectionalLight("low-sun")
        sun.setColor((1.55, 1.18, 0.72, 1))
        sun_path = self.render.attachNewNode(sun)
        sun_path.setHpr(-42, -48, 0)
        self.render.setLight(sun_path)

        fill = DirectionalLight("cool-fill")
        fill.setColor((0.05, 0.09, 0.14, 1))
        fill_path = self.render.attachNewNode(fill)
        fill_path.setHpr(130, -28, 0)
        self.render.setLight(fill_path)

        rim = DirectionalLight("forest-rim")
        rim.setColor((0.08, 0.16, 0.1, 1))
        rim_path = self.render.attachNewNode(rim)
        rim_path.setHpr(55, -18, 0)
        self.render.setLight(rim_path)

        fog = Fog("distance-fog")
        fog.setColor(0.035, 0.08, 0.055)
        fog.setLinearRange(35.0, 90.0)
        self.render.setFog(fog)

    def _build_ui(self):
        self.status_frame = DirectFrame(
            frameColor=(0.025, 0.035, 0.032, 0.58),
            frameSize=(0.14, 1.36, 0.67, 0.98),
            pos=(0, 0, 0),
        )
        self.weapon_frame = DirectFrame(
            frameColor=(0.025, 0.04, 0.05, 0.54),
            frameSize=(-1.36, -0.08, 0.34, 0.72),
            pos=(0, 0, 0),
        )
        self.prompt_frame = DirectFrame(
            frameColor=(0.04, 0.035, 0.025, 0.58),
            frameSize=(-0.72, 0.72, -0.92, -0.8),
            pos=(0, 0, 0),
        )
        self.log_frame = DirectFrame(
            frameColor=(0.025, 0.025, 0.028, 0.48),
            frameSize=(0.04, 1.36, -0.92, -0.51),
            pos=(0, 0, 0),
        )
        self.health_bar_text = OnscreenText(
            text="Health",
            pos=(0.18, 0.93),
            scale=0.032,
            align=TextNode.ALeft,
            fg=(0.95, 0.96, 0.88, 1),
            mayChange=False,
        )
        DirectFrame(
            frameColor=(0.06, 0.025, 0.025, 0.84),
            frameSize=(0.34, 1.24, 0.885, 0.94),
            pos=(0, 0, 0),
        )
        self.health_bar_fill = DirectFrame(
            frameColor=(0.9, 0.16, 0.13, 0.92),
            frameSize=(0.345, 1.235, 0.89, 0.935),
            pos=(0, 0, 0),
        )
        DirectFrame(
            frameColor=(0.92, 0.96, 0.88, 0.28),
            frameSize=(0.33, 1.25, 0.875, 0.95),
            pos=(0, 0, 0),
        )
        self.stamina_bar_text = OnscreenText(
            text="Stamina",
            pos=(0.18, 0.84),
            scale=0.032,
            align=TextNode.ALeft,
            fg=(0.95, 0.96, 0.88, 1),
            mayChange=False,
        )
        DirectFrame(
            frameColor=(0.025, 0.055, 0.025, 0.84),
            frameSize=(0.34, 1.24, 0.795, 0.85),
            pos=(0, 0, 0),
        )
        self.stamina_bar_fill = DirectFrame(
            frameColor=(0.22, 0.82, 0.28, 0.92),
            frameSize=(0.345, 1.235, 0.8, 0.845),
            pos=(0, 0, 0),
        )
        DirectFrame(
            frameColor=(0.92, 0.96, 0.88, 0.22),
            frameSize=(0.33, 1.25, 0.785, 0.86),
            pos=(0, 0, 0),
        )
        self.status_text = OnscreenText(
            text="",
            pos=(0.18, 0.73),
            scale=0.039,
            align=TextNode.ALeft,
            fg=(0.95, 0.96, 0.88, 1),
            mayChange=True,
        )
        self.weapon_text = OnscreenText(
            text="",
            pos=(-1.32, 0.68),
            scale=0.039,
            align=TextNode.ALeft,
            fg=(0.86, 0.92, 1.0, 1),
            mayChange=True,
        )
        self.prompt_text = OnscreenText(
            text="",
            pos=(0, -0.86),
            scale=0.048,
            align=TextNode.ACenter,
            fg=(1.0, 0.92, 0.72, 1),
            mayChange=True,
        )
        self.catch_text = OnscreenText(
            text="",
            pos=(0, 0.38),
            scale=0.068,
            align=TextNode.ACenter,
            fg=(0.95, 0.98, 1.0, 1),
            mayChange=True,
        )
        self.log_text = OnscreenText(
            text="",
            pos=(0.08, -0.55),
            scale=0.036,
            align=TextNode.ALeft,
            fg=(0.92, 0.92, 0.92, 1),
            mayChange=True,
        )
        self._build_inspection_ui()
        self._build_shop_ui()
        self._build_forge_ui()
        self._update_ui()

    def _build_inspection_ui(self):
        self.inspect_frame = DirectFrame(
            frameColor=(0.035, 0.045, 0.055, 0.88),
            frameSize=(-0.58, 0.58, -0.5, 0.5),
            pos=(0.67, 0, 0.18),
        )
        self.inspect_title = OnscreenText(
            text="",
            parent=self.inspect_frame,
            pos=(-0.52, 0.39),
            scale=0.055,
            align=TextNode.ALeft,
            fg=(1.0, 0.94, 0.72, 1),
            mayChange=True,
        )
        self.inspect_body = OnscreenText(
            text="",
            parent=self.inspect_frame,
            pos=(-0.52, 0.18),
            scale=0.033,
            align=TextNode.ALeft,
            fg=(0.9, 0.95, 1.0, 1),
            mayChange=True,
        )
        self.inspect_preview_root = self.inspect_frame.attachNewNode("inspection-weapon-preview")
        self.inspect_preview_root.setPos(0.26, 0, 0.13)
        self.inspect_preview_root.setScale(0.24)
        self.inspect_preview_root.setHpr(-28, 0, -34)
        self.inspect_frame.hide()

    def _build_shop_ui(self):
        self.shop_frame = DirectFrame(
            frameColor=(0.035, 0.03, 0.02, 0.9),
            frameSize=(-0.58, 0.58, -0.48, 0.48),
            pos=(-0.68, 0, 0.15),
        )
        self.shop_title = OnscreenText(
            text="",
            parent=self.shop_frame,
            pos=(-0.52, 0.37),
            scale=0.052,
            align=TextNode.ALeft,
            fg=(1.0, 0.86, 0.42, 1),
            mayChange=True,
        )
        self.shop_body = OnscreenText(
            text="",
            parent=self.shop_frame,
            pos=(-0.52, 0.22),
            scale=0.032,
            align=TextNode.ALeft,
            fg=(0.94, 0.9, 0.78, 1),
            mayChange=True,
        )
        self.shop_frame.hide()

    def _build_forge_ui(self):
        self.forge_frame = DirectFrame(
            frameColor=(0.04, 0.028, 0.02, 0.9),
            frameSize=(-0.62, 0.62, -0.66, 0.52),
            pos=(0.68, 0, 0.15),
        )
        self.forge_title = OnscreenText(
            text="",
            parent=self.forge_frame,
            pos=(-0.56, 0.42),
            scale=0.048,
            align=TextNode.ALeft,
            fg=(1.0, 0.62, 0.28, 1),
            mayChange=True,
        )
        self.forge_body = OnscreenText(
            text="",
            parent=self.forge_frame,
            pos=(-0.56, 0.27),
            scale=0.026,
            align=TextNode.ALeft,
            fg=(0.94, 0.88, 0.78, 1),
            mayChange=True,
        )
        self.forge_frame.hide()

    def _update(self, task):
        dt = min(globalClock.getDt(), 0.05)
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        self.weapon_ability_cooldown = max(0.0, self.weapon_ability_cooldown - dt)
        self.dodge_cooldown = max(0.0, self.dodge_cooldown - dt)
        self._update_stamina(dt)
        self.catch_banner_timer = max(0.0, self.catch_banner_timer - dt)
        self.water_bump_cooldown = max(0.0, self.water_bump_cooldown - dt)
        if self.shop_open and self._distance_to_shop() > SHOP_RANGE + 0.45:
            self.shop_open = False
        if self.forge_open and self._distance_to_forge() > FORGE_RANGE + 0.45:
            self.forge_open = False
        self._move_player(dt)
        self._update_player_walk(dt)
        self._update_death_sequence(dt)
        self._update_fishing(dt)
        self._update_world_details()
        self._update_enemies(dt)
        self._update_mob_respawns(dt)
        self._update_pet(dt)
        self._update_hp_regen(dt)
        self._update_ranged_shots(dt)
        self._update_hit_effects(dt)
        self._update_swing(dt)
        self._update_camera()
        self._update_ui()
        return task.cont

    def _pause_hp_regen(self):
        self.hp_regen_cooldown = HP_REGEN_DELAY
        self.hp_regen_timer = 0.0

    def _update_hp_regen(self, dt: float):
        if self.player_hp <= 0 or self.is_death_sequence:
            self.hp_regen_timer = 0.0
            return

        if self.player_hp >= self.player_max_hp:
            self.hp_regen_cooldown = 0.0
            self.hp_regen_timer = 0.0
            return

        if self.hp_regen_cooldown > 0.0:
            self.hp_regen_cooldown = max(0.0, self.hp_regen_cooldown - dt)
            return

        self.hp_regen_timer += dt
        while self.hp_regen_timer >= HP_REGEN_INTERVAL and self.player_hp < self.player_max_hp:
            self.hp_regen_timer -= HP_REGEN_INTERVAL
            self.player_hp = min(self.player_max_hp, self.player_hp + HP_REGEN_AMOUNT)

    def _spend_stamina(self, amount: float) -> bool:
        if self.player_stamina < amount:
            return False
        self.player_stamina = max(0.0, self.player_stamina - amount)
        self.stamina_regen_cooldown = STAMINA_REGEN_DELAY
        return True

    def _update_stamina(self, dt: float):
        if self.player_hp <= 0 or self.is_death_sequence:
            return
        if self.stamina_regen_cooldown > 0.0:
            self.stamina_regen_cooldown = max(0.0, self.stamina_regen_cooldown - dt)
            return
        if self.player_stamina < self.player_max_stamina:
            self.player_stamina = min(
                self.player_max_stamina,
                self.player_stamina + STAMINA_REGEN_RATE * dt,
            )

    def _move_player(self, dt: float):
        self.is_player_moving = False
        self.is_sprinting = False
        if self.player_hp <= 0:
            return

        if self.dodge_time > 0.0:
            self.dodge_time = max(0.0, self.dodge_time - dt)
            movement = Vec3(self.dodge_direction)
            speed = DODGE_SPEED
        else:
            move_x = 0.0
            move_y = 0.0
            if self.keys["w"]:
                move_y += 1.0
            if self.keys["s"]:
                move_y -= 1.0
            if self.keys["a"]:
                move_x -= 1.0
            if self.keys["d"]:
                move_x += 1.0

            movement = Vec3(move_x, move_y, 0)
            if movement.length() == 0:
                return

            movement.normalize()
            speed = PLAYER_SPEED
            if (
                self.sprint_held
                and self.player_stamina >= SPRINT_MIN_STAMINA
                and self.fishing_state == "idle"
            ):
                speed *= SPRINT_SPEED_MULTIPLIER
                self.player_stamina = max(
                    0.0,
                    self.player_stamina - SPRINT_STAMINA_DRAIN * dt,
                )
                self.stamina_regen_cooldown = STAMINA_REGEN_DELAY
                self.is_sprinting = True

        old_pos = self.player.getPos()
        new_pos = old_pos + movement * speed * dt
        new_pos.setX(max(-WORLD_LIMIT, min(WORLD_LIMIT, new_pos.getX())))
        new_pos.setY(max(-WORLD_LIMIT, min(WORLD_LIMIT, new_pos.getY())))
        new_pos.setZ(0)
        if self._is_water_position(new_pos):
            blocked_by_water = True
            slide_x = Vec3(new_pos.getX(), old_pos.getY(), 0)
            slide_y = Vec3(old_pos.getX(), new_pos.getY(), 0)
            if not self._is_water_position(slide_x):
                new_pos = slide_x
            elif not self._is_water_position(slide_y):
                new_pos = slide_y
            else:
                new_pos = Vec3(old_pos.getX(), old_pos.getY(), 0)
            if blocked_by_water and self.water_bump_cooldown == 0.0:
                self.water_bump_cooldown = 1.2
                self._log("The lake is too deep to walk into.")
        self.player.setPos(new_pos)
        self.is_player_moving = (new_pos - old_pos).length() > 0.01
        if self.is_sprinting and self.is_player_moving:
            self.sprint_dust_timer = max(0.0, self.sprint_dust_timer - dt)
            if self.sprint_dust_timer == 0.0:
                self.sprint_dust_timer = SPRINT_DUST_INTERVAL
                self._spawn_sprint_dust(movement)
        else:
            self.sprint_dust_timer = 0.0

        heading = math.degrees(math.atan2(-movement.getX(), movement.getY()))
        self.player.setH(heading)

    def _update_player_walk(self, dt: float):
        if self.left_leg is None or self.right_leg is None or self.left_arm is None:
            return
        if self.is_death_sequence:
            return

        if self.dodge_time > 0.0:
            progress = 1.0 - self.dodge_time / DODGE_DURATION
            self.player.setP(-360.0 * progress)
            self.player.setR(0)
            self.player.setZ(math.sin(progress * math.pi) * 0.35)
            self.left_leg.setP(52.0)
            self.right_leg.setP(52.0)
            self.left_arm.setHpr(24, -18, -12)
            if self.right_arm is not None:
                self.right_arm.setHpr(-26, -18, 12)
            return

        if self.is_player_moving and self.player_hp > 0:
            stride_speed = 14.0 if self.is_sprinting else 9.5
            stride_power = 1.25 if self.is_sprinting else 1.0
            self.walk_time += dt * stride_speed
            stride = math.sin(self.walk_time)
            counter_stride = math.sin(self.walk_time + math.pi)
            bounce = abs(math.sin(self.walk_time)) * (0.075 if self.is_sprinting else 0.055)
            lean = math.sin(self.walk_time * 0.5) * (2.5 if self.is_sprinting else 1.5)
            self.player.setZ(bounce)
            self.player.setP((-4.0 if self.is_sprinting else -2.0) - bounce * 10.0)
            self.player.setR(lean)
            self.left_leg.setP(stride * 21.0 * stride_power)
            self.right_leg.setP(counter_stride * 21.0 * stride_power)
            self.left_leg.setR(counter_stride * 4.0 * stride_power)
            self.right_leg.setR(stride * 4.0 * stride_power)
            self.left_arm.setHpr(8 + counter_stride * 8.0 * stride_power, -9, -8)
            if self.swing_time <= 0.0 and self.right_arm is not None:
                self.right_arm.setHpr(-10 + stride * 7.0 * stride_power, -12, 8)
            visual_step = abs(stride)
            self._set_imported_player_pose(
                heading_offset=stride * (3.5 if self.is_sprinting else 2.5),
                pitch_offset=(-4.0 if self.is_sprinting else -2.4) + visual_step * 2.0,
                roll_offset=counter_stride * (4.0 if self.is_sprinting else 2.8),
                z_offset=visual_step * (0.055 if self.is_sprinting else 0.038),
            )
        else:
            self.player.setZ(0)
            self.player.setP(0)
            self.player.setR(0)
            self.left_leg.setHpr(0, 0, 0)
            self.right_leg.setHpr(0, 0, 0)
            self.left_arm.setHpr(8, -9, -8)
            if self.swing_time <= 0.0 and self.right_arm is not None:
                self.right_arm.setHpr(-10, -12, 8)
            idle_breath = math.sin(self.fishing_phase * 1.8) * 0.7
            self._set_imported_player_pose(
                pitch_offset=idle_breath,
                z_offset=(idle_breath + 0.7) * 0.008,
            )

    def _update_pet(self, dt: float):
        if self.pet is None:
            return

        self.pet_attack_cooldown = max(0.0, self.pet_attack_cooldown - dt)
        player_pos = self.player.getPos()
        pet_pos = self.pet.getPos()
        target = self._nearest_pet_target()

        if self.player_hp <= 0:
            desired = player_pos + Vec3(-0.8, -0.85, 0)
        elif target is not None and (target.node.getPos() - pet_pos).length() <= PET_SENSE_RANGE:
            desired = target.node.getPos()
        else:
            heading = math.radians(self.player.getH())
            backward = Vec3(math.sin(heading), -math.cos(heading), 0)
            right = Vec3(math.cos(heading), math.sin(heading), 0)
            desired = player_pos + backward * PET_FOLLOW_DISTANCE + right * -0.75

        to_goal = desired - pet_pos
        to_goal.setZ(0)
        distance = to_goal.length()
        moving = False
        if distance > 0.15:
            direction = Vec3(to_goal)
            direction.normalize()
            step = min(distance, PET_SPEED * dt)
            self.pet.setPos(pet_pos + direction * step)
            self.pet.setH(math.degrees(math.atan2(-direction.getX(), direction.getY())))
            moving = True

        self._animate_pet(dt, moving)

        if (
            target is not None
            and self.player_hp > 0
            and self.pet_attack_cooldown == 0.0
            and (target.node.getPos() - self.pet.getPos()).length() <= PET_ATTACK_RANGE
        ):
            self._pet_attack(target)

    def _nearest_pet_target(self) -> Optional[SceneEnemy]:
        if not self.enemies or self.pet is None:
            return None
        pet_pos = self.pet.getPos()
        candidates = [
            ((enemy.node.getPos() - pet_pos).length(), enemy)
            for enemy in self.enemies
            if (enemy.node.getPos() - pet_pos).length() <= PET_SENSE_RANGE
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]

    def _animate_pet(self, dt: float, moving: bool):
        self.pet_walk_time += dt * (9.0 if moving else 3.0)
        wave = math.sin(self.pet_walk_time)
        bounce = abs(wave) * 0.055 if moving else math.sin(self.pet_walk_time) * 0.015
        if self.pet_visual is not None:
            self.pet_visual.setZ(bounce)
            self.pet_visual.setP(wave * 2.5 if moving else 0)
        if self.pet_head is not None:
            self.pet_head.setP(-4.0 + wave * (4.0 if moving else 2.0))
        if self.pet_tail is not None:
            self.pet_tail.setH(wave * (24.0 if moving else 14.0))
        if self.pet_left_foot is not None:
            self.pet_left_foot.setP(wave * 16.0 if moving else 0)
        if self.pet_right_foot is not None:
            self.pet_right_foot.setP(-wave * 16.0 if moving else 0)

    def _pet_attack(self, target: SceneEnemy):
        if target not in self.enemies or self.pet is None:
            return

        self.pet_attack_cooldown = PET_ATTACK_COOLDOWN
        direction = target.node.getPos() - self.pet.getPos()
        direction.setZ(0)
        if direction.length() == 0:
            direction = Vec3(0, 1, 0)
        else:
            direction.normalize()
        self.pet.setH(math.degrees(math.atan2(-direction.getX(), direction.getY())))

        target.hp = max(0, target.hp - PET_ATTACK_DAMAGE)
        target.flash_time = 0.18
        target.knockback_velocity = direction * 7.0
        target.node.setColorScale(1.35, 0.58, 0.34, 1)
        self._spawn_pet_claw_effect(target.node.getPos() + Vec3(0, 0, 0.58), direction)
        if target.kind == "rabbit":
            self._spawn_rabbit_hit_effects(target, direction)
        self._log(f"Your tiger cub pounces for {PET_ATTACK_DAMAGE}.")

        if target.hp == 0:
            reward = gold_reward_for_enemy(target.kind)
            if reward:
                self.gold += reward
                self._spawn_gold_reward_effect(target.node.getPos(), reward)
                self._log(f"Your tiger cub finds {reward} gold coins.")
            if target.kind == "rabbit":
                self._spawn_rabbit_defeat_effects(target)
            target.node.removeNode()
            self.enemies.remove(target)

    def _spawn_pet_claw_effect(self, pos: Vec3, direction: Vec3):
        sideways = Vec3(-direction.getY(), direction.getX(), 0)
        if sideways.length() == 0:
            sideways = Vec3(1, 0, 0)
        else:
            sideways.normalize()
        for index, offset in enumerate((-0.16, 0.0, 0.16)):
            self._spawn_hit_piece(
                name=f"pet-claw-{index}",
                size=(0.24, 0.035, 0.045),
                color=(1.0, 0.74, 0.32, 0.72),
                pos=pos + sideways * offset,
                velocity=direction * self.rng.uniform(1.8, 2.8)
                + sideways * offset * 2.0
                + Vec3(0, 0, self.rng.uniform(1.0, 1.8)),
                lifetime=0.32,
            )

    def _start_death_sequence(self):
        if self.is_death_sequence:
            return

        self.is_death_sequence = True
        self.death_timer = self.death_duration
        self.is_player_moving = False
        self.shop_open = False
        self.inspect_open = False
        self.attack_cooldown = self.death_duration
        self.player.setColorScale(1.0, 0.72, 0.72, 1)
        self._set_catch_banner("You fell!\nRespawning...")
        self._log("You fall over. The lake pulls you back to the dock.")

    def _update_death_sequence(self, dt: float):
        if self.player_hp <= 0 and not self.is_death_sequence:
            self._start_death_sequence()

        if not self.is_death_sequence:
            return

        self.death_timer = max(0.0, self.death_timer - dt)
        progress = 1.0 - self.death_timer / self.death_duration
        fall = min(1.0, progress / 0.55)
        settle = math.sin(min(1.0, progress) * math.pi)

        self.player.setZ(-0.05 + settle * 0.06)
        self.player.setP(-82.0 * fall)
        self.player.setR(24.0 * fall)
        self._set_imported_player_pose(
            heading_offset=fall * 10.0,
            pitch_offset=-fall * 8.0,
            roll_offset=fall * 6.0,
        )
        if self.left_arm:
            self.left_arm.setHpr(8.0, -22.0 * fall, -55.0 * fall)
        if self.right_arm:
            self.right_arm.setHpr(-8.0, -18.0 * fall, 58.0 * fall)
        if self.left_leg:
            self.left_leg.setHpr(0, 0, -18.0 * fall)
        if self.right_leg:
            self.right_leg.setHpr(0, 0, 18.0 * fall)

        fade = 1.0 - max(0.0, progress - 0.55) * 0.55
        self.player.setColorScale(1.0, 0.72 + progress * 0.2, 0.72 + progress * 0.2, fade)

        if self.death_timer == 0.0:
            self.reset_arena(auto_respawn=True)

    def _update_world_details(self):
        for detail in self.animated_details:
            wave = math.sin(self.fishing_phase * detail.speed + detail.phase)
            pos = Vec3(detail.base_pos)
            pos.setZ(pos.getZ() + wave * detail.bob_amount)
            detail.node.setPos(pos)
            if detail.sway_amount:
                detail.node.setH(wave * detail.sway_amount)
            if detail.color[3] < 1.0:
                pulse = 0.68 + 0.32 * (0.5 + 0.5 * wave)
                detail.node.setColorScale(1, 1, 1, pulse)

    def _is_water_position(self, pos: Vec3) -> bool:
        x = pos.getX()
        y = pos.getY()
        dock_min_x, dock_max_x, dock_min_y, dock_max_y = DOCK_SAFE_ZONE
        if dock_min_x <= x <= dock_max_x and dock_min_y <= y <= dock_max_y:
            return False

        for center_x, center_y, radius_x, radius_y in WATER_BLOBS:
            normalized_x = (x - center_x) / radius_x
            normalized_y = (y - center_y) / radius_y
            if normalized_x * normalized_x + normalized_y * normalized_y <= 1.0:
                return True

        return False

    def _has_attack_token(self, enemy: SceneEnemy) -> bool:
        return self.attack_token_holder is enemy

    def _acquire_attack_token(self, enemy: SceneEnemy) -> bool:
        if self.attack_token_holder is enemy:
            return True
        if self.attack_token_holder is None and self.attack_token_cooldown <= 0.0:
            self.attack_token_holder = enemy
            self.attack_token_timer = 0.0
            return True
        return False

    def _release_attack_token(self, enemy: SceneEnemy, gap: float = ENEMY_TURN_GAP):
        if self.attack_token_holder is enemy:
            self.attack_token_holder = None
            self.attack_token_cooldown = gap

    def _update_attack_token(self, dt: float):
        self.attack_token_cooldown = max(0.0, self.attack_token_cooldown - dt)
        holder = self.attack_token_holder
        if holder is None:
            return
        self.attack_token_timer += dt
        if holder not in self.enemies or self.attack_token_timer > ENEMY_TURN_MAX_HOLD:
            self.attack_token_holder = None
            self.attack_token_cooldown = max(self.attack_token_cooldown, ENEMY_TURN_GAP)

    def _update_enemies(self, dt: float):
        if self.player_hp <= 0:
            return

        self._update_attack_token(dt)
        player_pos = self.player.getPos()
        player_safe = self._player_in_safe_zone()
        for enemy in self.enemies:
            enemy_pos = self._update_enemy_feedback(enemy, dt)
            player_to_home = player_pos - enemy.home_pos
            player_to_home.setZ(0)
            if player_safe or player_to_home.length() > LEASH_RANGE:
                self._release_attack_token(enemy)
                if enemy.kind == "bird":
                    enemy.ai_state = "circle"
                elif enemy.kind == "boar":
                    enemy.ai_state = "stalk"
                elif enemy.kind == "snapper":
                    enemy.ai_state = "stalk"
                elif enemy.kind == "wisp":
                    enemy.ai_state = "hover"
                else:
                    enemy.ai_state = "idle"
                self._walk_home(enemy, enemy_pos, dt)
                continue
            if enemy.kind == "rabbit":
                self._update_rabbit(enemy, player_pos, enemy_pos, dt)
            elif enemy.kind == "bird":
                self._update_bird(enemy, player_pos, enemy_pos, dt)
            elif enemy.kind == "boar":
                self._update_boar(enemy, player_pos, enemy_pos, dt)
            elif enemy.kind == "snapper":
                self._update_snapper(enemy, player_pos, enemy_pos, dt)
            elif enemy.kind == "wisp":
                self._update_wisp(enemy, player_pos, enemy_pos, dt)
            else:
                self._update_monster(enemy, player_pos, enemy_pos, dt)

    def _update_mob_respawns(self, dt: float):
        if self.player_hp <= 0 or self.is_death_sequence:
            return

        self.mob_respawn_timer = max(0.0, self.mob_respawn_timer - dt)
        if self.mob_respawn_timer > 0.0:
            return

        self.mob_respawn_timer = MOB_RESPAWN_INTERVAL
        respawned = self._top_up_roaming_mobs()
        respawned += self._top_up_chest_guards()
        if respawned:
            self._log("The wilds stir. Fresh mobs return to the map.")

    def _top_up_roaming_mobs(self) -> int:
        counts = {kind: 0 for kind in FIELD_MOB_TARGETS}
        for enemy in self.enemies:
            if enemy.kind in counts and enemy.bounds is None:
                counts[enemy.kind] += 1

        spawned = 0
        for kind, target in FIELD_MOB_TARGETS.items():
            missing = max(0, target - counts[kind])
            for _ in range(missing):
                self._spawn_single_roaming_mob(kind)
                spawned += 1
        return spawned

    def _spawn_single_roaming_mob(self, kind: str):
        spawn_index = len(self.enemies) + self.fish_count + 1
        if kind == "bird":
            self.enemies.append(self._make_bird(spawn_index, self._random_field_position()))
        elif kind == "boar":
            self.enemies.append(self._make_boar(spawn_index, self._random_field_position()))
        elif kind == "snapper":
            self.enemies.append(self._make_snapper(spawn_index, self._random_field_position()))
        elif kind == "wisp":
            self.enemies.append(self._make_wisp(spawn_index, self._random_field_position()))
        else:
            self.enemies.append(self._make_rabbit(spawn_index, self._random_arena_position()))

    def _top_up_chest_guards(self) -> int:
        spawned = 0
        for index, chest in enumerate(self.chests):
            if chest.opened or self._chest_has_living_guard(chest):
                continue
            before = len(self.enemies)
            self._spawn_chest_guards(index, chest.pos, chest.guard_kind, bounds=chest.guard_bounds)
            spawned += len(self.enemies) - before
        return spawned

    def _chest_has_living_guard(self, chest: SceneChest) -> bool:
        for enemy in self.enemies:
            if enemy.bounds is None:
                continue
            home_to_chest = enemy.home_pos - chest.pos
            home_to_chest.setZ(0)
            if home_to_chest.length() <= 2.8:
                return True
        return False

    def _player_in_safe_zone(self) -> bool:
        """Check if the player is near the pond/dock or the rod shop."""
        pos = self.player.getPos()
        lake_center = Vec3(0, 9.7, 0)
        if (pos - lake_center).length() < 8.0:
            return True
        if (pos - self.shop_spot).length() < 4.0:
            return True
        return False

    def _walk_home(self, enemy: SceneEnemy, enemy_pos: Vec3, dt: float):
        direction = enemy.home_pos - enemy_pos
        direction.setZ(0)
        distance = direction.length()
        if distance < 1.0:
            return
        direction.normalize()
        enemy.node.setH(math.degrees(math.atan2(-direction.getX(), direction.getY())))
        new_pos = self._clamp_enemy_position(enemy, enemy_pos + direction * enemy.speed * dt)
        enemy.node.setPos(new_pos)
        if enemy.kind == "bird":
            enemy.node.setZ(1.8)
        elif enemy.kind == "wisp":
            enemy.node.setZ(1.15 + math.sin(enemy.animation_phase) * 0.18)

    def _update_enemy_feedback(self, enemy: SceneEnemy, dt: float) -> Vec3:
        enemy.attack_cooldown = max(0.0, enemy.attack_cooldown - dt)
        if enemy.flash_time > 0.0:
            enemy.flash_time = max(0.0, enemy.flash_time - dt)
            if enemy.flash_time == 0.0:
                enemy.node.setColorScale(1, 1, 1, 1)

        enemy_pos = enemy.node.getPos()
        if enemy.knockback_velocity.length() > 0.05:
            enemy_pos = enemy_pos + enemy.knockback_velocity * dt
            enemy_pos = self._clamp_enemy_position(enemy, enemy_pos)
            enemy.node.setPos(enemy_pos)
            enemy.knockback_velocity = enemy.knockback_velocity * max(0.0, 1.0 - dt * 5.5)
        else:
            enemy_pos = self._clamp_enemy_position(enemy, enemy_pos)
            enemy.node.setPos(enemy_pos)

        return enemy_pos

    def _damage_player_from_enemy(self, enemy: SceneEnemy, attack_text: str):
        damage = apply_damage(enemy.contact_damage, self.player_armor_value)
        self.player_hp = max(0, self.player_hp - damage)
        self._pause_hp_regen()
        if self.player_armor_value > 0 and damage < enemy.contact_damage:
            blocked = enemy.contact_damage - damage
            self._log(f"{enemy.name} {attack_text} for {damage}. Armor blocks {blocked}.")
        else:
            self._log(f"{enemy.name} {attack_text} for {damage}.")
        if self.player_hp == 0:
            self._start_death_sequence()

    def _update_monster(self, enemy: SceneEnemy, player_pos: Vec3, enemy_pos: Vec3, dt: float):
        to_player = player_pos - enemy_pos
        to_player.setZ(0)
        distance = to_player.length()
        moving = False

        has_token = self._has_attack_token(enemy)
        if not has_token and enemy.attack_cooldown == 0.0 and distance < 1.8:
            has_token = self._acquire_attack_token(enemy)
        stand_off = 0.0 if has_token else ENEMY_WAIT_DISTANCE

        if 0.05 < distance < 9.0:
            to_player.normalize()
            enemy.node.setH(math.degrees(math.atan2(-to_player.getX(), to_player.getY())))
            if distance > stand_off:
                enemy_pos = self._clamp_enemy_position(
                    enemy, enemy_pos + to_player * enemy.speed * dt
                )
                enemy.node.setPos(enemy_pos)
                moving = True

        if has_token and distance < 1.05 and enemy.attack_cooldown == 0.0:
            enemy.attack_cooldown = 1.1
            if self._player_is_invulnerable():
                self._log(f"You roll under {enemy.name}'s bite.")
            else:
                self._damage_player_from_enemy(enemy, "bites")
            self._release_attack_token(enemy)

        self._animate_monster(enemy, dt, moving)

    def _update_bird(self, enemy: SceneEnemy, player_pos: Vec3, enemy_pos: Vec3, dt: float):
        to_player = player_pos - enemy_pos
        to_player.setZ(0)
        distance = to_player.length()
        flat = Vec3(to_player)
        if distance > 0.05:
            flat.normalize()
            enemy.node.setH(math.degrees(math.atan2(-flat.getX(), flat.getY())))

        hover_h = 1.8

        if enemy.ai_state == "telegraph":
            enemy.state_timer -= dt
            rise = 1.0 - max(0.0, enemy.state_timer) / 0.5
            enemy.node.setZ(hover_h + 0.6 * rise)
            if enemy.flash_time == 0.0:
                enemy.node.setColorScale(1.2, 1.05, 0.8, 1)
            if enemy.state_timer <= 0.0:
                enemy.ai_state = "swoop"
                enemy.state_timer = 0.5
                enemy.attack_landed = False
                enemy.lunge_direction = Vec3(flat) if flat.length() else Vec3(0, 1, 0)
                if enemy.flash_time == 0.0:
                    enemy.node.setColorScale(1, 1, 1, 1)
            self._animate_bird(enemy, dt, "telegraph")
            return

        if enemy.ai_state == "swoop":
            enemy.state_timer -= dt
            progress = 1.0 - max(0.0, enemy.state_timer) / 0.5
            enemy_pos = self._clamp_enemy_position(
                enemy, enemy_pos + enemy.lunge_direction * 11.0 * dt
            )
            enemy.node.setPos(enemy_pos)
            enemy.node.setZ(hover_h - math.sin(progress * math.pi) * (hover_h - 0.55))
            self._animate_bird(enemy, dt, "swoop", progress)

            if not enemy.attack_landed and (player_pos - enemy_pos).length() < 1.15:
                enemy.attack_landed = True
                enemy.attack_cooldown = 1.2
                if self._player_is_invulnerable():
                    self._log(f"You roll under {enemy.name}'s dive.")
                else:
                    self._damage_player_from_enemy(enemy, "rakes you")

            if enemy.state_timer <= 0.0:
                enemy.ai_state = "circle"
                enemy.state_timer = self.rng.uniform(0.5, 1.1)
                enemy.node.setZ(hover_h)
                self._release_attack_token(enemy)
            return

        enemy.state_timer -= dt
        orbit_radius = 3.4
        if distance > orbit_radius + 0.4:
            step = flat * enemy.speed * dt
        elif distance < orbit_radius - 0.4:
            step = flat * -enemy.speed * dt
        else:
            sideways = Vec3(-flat.getY(), flat.getX(), 0)
            step = sideways * enemy.speed * 0.8 * dt
        enemy_pos = self._clamp_enemy_position(enemy, enemy_pos + step)
        enemy.node.setPos(enemy_pos)
        enemy.node.setZ(hover_h + math.sin(enemy.animation_phase) * 0.18)
        self._animate_bird(enemy, dt, "circle")

        if distance < 5.5 and enemy.attack_cooldown == 0.0 and self._acquire_attack_token(enemy):
            enemy.ai_state = "telegraph"
            enemy.state_timer = 0.5

    def _animate_bird(self, enemy: SceneEnemy, dt: float, state: str, progress: float = 0.0):
        enemy.animation_phase += dt * (16.0 if state == "swoop" else 11.0)
        flap = math.sin(enemy.animation_phase)
        wing_raise = 42.0 + flap * 38.0
        if enemy.body_node:
            enemy.body_node.setP(-18.0 if state == "swoop" else flap * 4.0)
        if enemy.left_detail_node:
            enemy.left_detail_node.setR(wing_raise)
        if enemy.right_detail_node:
            enemy.right_detail_node.setR(-wing_raise)
        if enemy.tail_node:
            enemy.tail_node.setP(flap * 8.0)
        if enemy.head_node:
            enemy.head_node.setP(-8.0 if state == "swoop" else flap * 4.0)

    def _update_boar(self, enemy: SceneEnemy, player_pos: Vec3, enemy_pos: Vec3, dt: float):
        to_player = player_pos - enemy_pos
        to_player.setZ(0)
        distance = to_player.length()
        flat = Vec3(to_player)
        if distance > 0.05:
            flat.normalize()

        if enemy.knockback_velocity.length() > 0.05:
            enemy.ai_state = "stalk"
            enemy.attack_landed = False
            self._release_attack_token(enemy)
            self._animate_boar(enemy, dt, False)
            return

        if enemy.ai_state == "telegraph":
            enemy.state_timer -= dt
            enemy.node.setH(math.degrees(math.atan2(-flat.getX(), flat.getY())))
            if enemy.flash_time == 0.0:
                enemy.node.setColorScale(1.25, 0.95, 0.8, 1)
            if enemy.state_timer <= 0.0:
                enemy.ai_state = "charge"
                enemy.state_timer = 0.65
                enemy.attack_landed = False
                enemy.lunge_direction = Vec3(flat) if flat.length() else Vec3(0, 1, 0)
                if enemy.flash_time == 0.0:
                    enemy.node.setColorScale(1, 1, 1, 1)
            self._animate_boar(enemy, dt, False, telegraph=True)
            return

        if enemy.ai_state == "charge":
            enemy.state_timer -= dt
            enemy_pos = self._clamp_enemy_position(
                enemy, enemy_pos + enemy.lunge_direction * 12.0 * dt
            )
            enemy.node.setPos(enemy_pos)
            self._animate_boar(enemy, dt, True)

            if not enemy.attack_landed and (player_pos - enemy_pos).length() < 1.2:
                enemy.attack_landed = True
                enemy.attack_cooldown = 1.3
                if self._player_is_invulnerable():
                    self._log(f"You roll clear of {enemy.name}'s charge.")
                else:
                    self._damage_player_from_enemy(enemy, "gores you")

            if enemy.state_timer <= 0.0:
                enemy.ai_state = "stalk"
                enemy.state_timer = self.rng.uniform(0.4, 0.9)
                self._release_attack_token(enemy)
            return

        enemy.state_timer -= dt
        has_token = self._has_attack_token(enemy)
        stand_off = 0.0 if has_token else ENEMY_WAIT_DISTANCE
        moving = False
        if stand_off < distance < 26.0:
            enemy.node.setH(math.degrees(math.atan2(-flat.getX(), flat.getY())))
            enemy_pos = self._clamp_enemy_position(enemy, enemy_pos + flat * enemy.speed * dt)
            enemy.node.setPos(enemy_pos)
            moving = True
        self._animate_boar(enemy, dt, moving)

        if distance < 3.4 and enemy.attack_cooldown == 0.0 and self._acquire_attack_token(enemy):
            enemy.ai_state = "telegraph"
            enemy.state_timer = 0.55

    def _animate_boar(self, enemy: SceneEnemy, dt: float, moving: bool, telegraph: bool = False):
        enemy.animation_phase += dt * (12.0 if moving else 6.0)
        wave = math.sin(enemy.animation_phase)
        visual = enemy.visual_node or enemy.node

        if telegraph:
            visual.setP(7.0 + math.sin(enemy.animation_phase * 3.0) * 4.0)
            if enemy.left_foot_node:
                enemy.left_foot_node.setP(math.sin(enemy.animation_phase * 6.0) * 24.0)
            return

        visual.setZ(abs(wave) * 0.04 if moving else 0.0)
        visual.setP(wave * 2.0 if moving else 0.0)
        if enemy.left_foot_node:
            enemy.left_foot_node.setP(wave * 24.0)
        if enemy.right_foot_node:
            enemy.right_foot_node.setP(-wave * 24.0)
        if enemy.head_node:
            enemy.head_node.setP(-4.0 + wave * 3.0)
        if enemy.tail_node:
            enemy.tail_node.setH(wave * 8.0)

    def _update_snapper(self, enemy: SceneEnemy, player_pos: Vec3, enemy_pos: Vec3, dt: float):
        to_player = player_pos - enemy_pos
        to_player.setZ(0)
        distance = to_player.length()
        flat = Vec3(to_player)
        if distance > 0.05:
            flat.normalize()
            enemy.node.setH(math.degrees(math.atan2(-flat.getX(), flat.getY())))

        if enemy.ai_state == "telegraph":
            enemy.state_timer -= dt
            if enemy.flash_time == 0.0:
                enemy.node.setColorScale(0.78, 1.12, 0.86, 1)
            self._animate_snapper(enemy, dt, False, tucked=True)
            if enemy.state_timer <= 0.0:
                enemy.ai_state = "snap"
                enemy.state_timer = 0.28
                enemy.attack_landed = False
                if enemy.flash_time == 0.0:
                    enemy.node.setColorScale(1, 1, 1, 1)
            return

        if enemy.ai_state == "snap":
            enemy.state_timer -= dt
            if not enemy.attack_landed and distance < 1.25:
                enemy.attack_landed = True
                enemy.attack_cooldown = 1.25
                if self._player_is_invulnerable():
                    self._log(f"You roll away from {enemy.name}'s snap.")
                else:
                    self._damage_player_from_enemy(enemy, "snaps")
            self._animate_snapper(enemy, dt, False, snapping=True)
            if enemy.state_timer <= 0.0:
                enemy.ai_state = "stalk"
                self._release_attack_token(enemy)
            return

        has_token = self._has_attack_token(enemy)
        stand_off = 0.0 if has_token else ENEMY_WAIT_DISTANCE
        moving = False
        if stand_off < distance < 16.0:
            enemy_pos = self._clamp_enemy_position(enemy, enemy_pos + flat * enemy.speed * dt)
            enemy.node.setPos(enemy_pos)
            moving = True
        self._animate_snapper(enemy, dt, moving)

        if distance < 2.1 and enemy.attack_cooldown == 0.0 and self._acquire_attack_token(enemy):
            enemy.ai_state = "telegraph"
            enemy.state_timer = 0.45

    def _animate_snapper(
        self,
        enemy: SceneEnemy,
        dt: float,
        moving: bool,
        tucked: bool = False,
        snapping: bool = False,
    ):
        enemy.animation_phase += dt * (7.0 if moving else 3.0)
        wave = math.sin(enemy.animation_phase)
        visual = enemy.visual_node or enemy.node
        visual.setZ(abs(wave) * 0.025 if moving else 0)
        visual.setP((wave * 1.8) if moving else 0)

        head_pitch = 18.0 if snapping else (-18.0 if tucked else wave * 2.0)
        if enemy.head_node:
            enemy.head_node.setP(head_pitch)
        if enemy.left_foot_node:
            enemy.left_foot_node.setP(wave * 14.0 if moving else 0)
        if enemy.right_foot_node:
            enemy.right_foot_node.setP(-wave * 14.0 if moving else 0)
        if enemy.tail_node:
            enemy.tail_node.setH(wave * 5.0)

    def _update_wisp(self, enemy: SceneEnemy, player_pos: Vec3, enemy_pos: Vec3, dt: float):
        to_player = player_pos - enemy_pos
        to_player.setZ(0)
        distance = to_player.length()
        flat = Vec3(to_player)
        if distance > 0.05:
            flat.normalize()
            enemy.node.setH(math.degrees(math.atan2(-flat.getX(), flat.getY())))

        hover_h = 1.15
        if enemy.ai_state == "telegraph":
            enemy.state_timer -= dt
            if enemy.flash_time == 0.0:
                enemy.node.setColorScale(0.55, 0.95, 1.35, 1)
            self._animate_wisp(enemy, dt, "telegraph")
            if enemy.state_timer <= 0.0:
                enemy.ai_state = "blink"
                enemy.state_timer = 0.24
                enemy.attack_landed = False
                enemy.lunge_direction = Vec3(flat) if flat.length() else Vec3(0, 1, 0)
                if enemy.flash_time == 0.0:
                    enemy.node.setColorScale(1, 1, 1, 1)
            return

        if enemy.ai_state == "blink":
            enemy.state_timer -= dt
            enemy_pos = self._clamp_enemy_position(
                enemy, enemy_pos + enemy.lunge_direction * 10.5 * dt
            )
            enemy.node.setPos(enemy_pos)
            enemy.node.setZ(hover_h + math.sin(enemy.state_timer * 30.0) * 0.22)
            self._animate_wisp(enemy, dt, "blink")

            if not enemy.attack_landed and (player_pos - enemy_pos).length() < 1.25:
                enemy.attack_landed = True
                enemy.attack_cooldown = 1.35
                if self._player_is_invulnerable():
                    self._log(f"You roll through {enemy.name}'s spark.")
                else:
                    self._damage_player_from_enemy(enemy, "zaps you")

            if enemy.state_timer <= 0.0:
                enemy.ai_state = "hover"
                self._release_attack_token(enemy)
            return

        enemy.state_timer -= dt
        sideways = Vec3(-flat.getY(), flat.getX(), 0) if flat.length() else Vec3(1, 0, 0)
        if distance > 4.0:
            step = flat * enemy.speed * dt
        elif distance < 2.8:
            step = flat * -enemy.speed * 0.75 * dt
        else:
            step = sideways * enemy.speed * 0.7 * dt
        enemy_pos = self._clamp_enemy_position(enemy, enemy_pos + step)
        enemy.node.setPos(enemy_pos)
        enemy.node.setZ(hover_h + math.sin(enemy.animation_phase * 1.2) * 0.2)
        self._animate_wisp(enemy, dt, "hover")

        if distance < 5.0 and enemy.attack_cooldown == 0.0 and self._acquire_attack_token(enemy):
            enemy.ai_state = "telegraph"
            enemy.state_timer = 0.42

    def _animate_wisp(self, enemy: SceneEnemy, dt: float, state: str):
        enemy.animation_phase += dt * (12.0 if state == "blink" else 5.5)
        wave = math.sin(enemy.animation_phase)
        visual = enemy.visual_node or enemy.node
        pulse = 1.0 + (0.14 if state == "telegraph" else 0.08) * wave
        visual.setScale(pulse, pulse, 1.0 + abs(wave) * 0.12)
        visual.setR(wave * 8.0)
        if enemy.left_detail_node:
            enemy.left_detail_node.setH(enemy.animation_phase * 50.0)
        if enemy.right_detail_node:
            enemy.right_detail_node.setH(-enemy.animation_phase * 58.0)
        if enemy.tail_node:
            enemy.tail_node.setP(-12.0 + wave * 10.0)

    def _update_rabbit(self, enemy: SceneEnemy, player_pos: Vec3, enemy_pos: Vec3, dt: float):
        to_player = player_pos - enemy_pos
        to_player.setZ(0)
        distance = to_player.length()
        if distance > 0.05:
            to_player.normalize()
            enemy.node.setH(math.degrees(math.atan2(-to_player.getX(), to_player.getY())))

        if enemy.knockback_velocity.length() > 0.05:
            enemy.ai_state = "idle"
            enemy.state_timer = 0.18
            enemy.attack_landed = False
            enemy.node.setScale(1, 1, 1)
            self._release_attack_token(enemy)
            self._animate_rabbit(enemy, dt, "stagger")
            return

        if enemy.ai_state == "telegraph":
            enemy.state_timer -= dt
            pulse = 1.0 + math.sin(max(0.0, enemy.state_timer) * 36.0) * 0.08
            enemy.node.setScale(1.08 * pulse, 0.92, 1.08)
            if enemy.flash_time == 0.0:
                enemy.node.setColorScale(1.18, 0.78, 0.78, 1)
            if enemy.state_timer <= 0.0:
                enemy.ai_state = "lunge"
                enemy.state_timer = 0.24
                enemy.attack_landed = False
                enemy.lunge_direction = Vec3(to_player)
                if enemy.lunge_direction.length() == 0:
                    enemy.lunge_direction = Vec3(0, 1, 0)
                enemy.lunge_direction.normalize()
                if enemy.flash_time == 0.0:
                    enemy.node.setColorScale(1, 1, 1, 1)
            self._animate_rabbit(enemy, dt, "telegraph")
            return

        if enemy.ai_state == "lunge":
            enemy.state_timer -= dt
            enemy_pos = self._clamp_enemy_position(enemy, enemy_pos + enemy.lunge_direction * 8.8 * dt)
            hop_height = math.sin(max(0.0, enemy.state_timer) / 0.24 * math.pi) * 0.16
            enemy_pos.setZ(hop_height)
            enemy.node.setPos(enemy_pos)
            enemy.node.setScale(1.18, 0.82, 0.92)
            progress = 1.0 - max(0.0, enemy.state_timer) / 0.24
            self._animate_rabbit(enemy, dt, "lunge", progress)

            lunge_distance = (player_pos - enemy_pos).length()
            if lunge_distance < 1.08 and not enemy.attack_landed:
                enemy.attack_landed = True
                enemy.attack_cooldown = 1.15
                if self._player_is_invulnerable():
                    self._log(f"You roll past {enemy.name}'s lunge.")
                else:
                    self._damage_player_from_enemy(enemy, "lunges")

            if enemy.state_timer <= 0.0:
                enemy.ai_state = "idle"
                enemy.state_timer = self.rng.uniform(0.16, 0.42)
                enemy.node.setScale(1, 1, 1)
                enemy_pos.setZ(0)
                enemy.node.setPos(enemy_pos)
                self._release_attack_token(enemy)
            return

        if enemy.ai_state == "hop":
            enemy.state_timer -= dt
            progress = 1.0 - max(0.0, enemy.state_timer) / max(0.01, enemy.hop_duration)
            pos = self._lerp_vec3(enemy.hop_start_pos, enemy.hop_target_pos, progress)
            pos = self._clamp_enemy_position(enemy, pos)
            pos.setZ(math.sin(progress * math.pi) * 0.42)
            enemy.node.setPos(pos)
            enemy.node.setScale(0.96, 1.08, 1.0 + math.sin(progress * math.pi) * 0.18)
            self._animate_rabbit(enemy, dt, "hop", progress)

            if enemy.state_timer <= 0.0:
                enemy.ai_state = "idle"
                enemy.state_timer = self.rng.uniform(0.12, 0.36)
                pos.setZ(0)
                enemy.node.setPos(pos)
                enemy.node.setScale(1, 1, 1)
            return

        enemy.node.setScale(1, 1, 1)
        self._animate_rabbit(enemy, dt, "idle")
        enemy.state_timer -= dt
        if (
            distance < 2.35
            and enemy.attack_cooldown == 0.0
            and self._acquire_attack_token(enemy)
        ):
            enemy.ai_state = "telegraph"
            enemy.state_timer = 0.38
            self._spawn_rabbit_attack_tell(enemy)
        elif enemy.state_timer <= 0.0:
            self._start_rabbit_hop(enemy, enemy_pos, to_player, distance)

    def _animate_rabbit(
        self, enemy: SceneEnemy, dt: float, state: str, progress: float = 0.0
    ):
        enemy.animation_phase += dt * 7.2
        wave = math.sin(enemy.animation_phase)
        hop_wave = math.sin(progress * math.pi)
        visual = enemy.visual_node or enemy.node

        if state == "idle":
            visual.setZ(0.02 + wave * 0.018)
            visual.setP(wave * 2.2)
            visual.setR(math.sin(enemy.animation_phase * 0.7) * 1.4)
            ear_pitch = 4.0 + wave * 4.0
            head_pitch = wave * 3.0
            foot_pitch = wave * 3.0
            tail_bob = wave * 4.0
        elif state == "hop":
            visual.setZ(0.03 + hop_wave * 0.08)
            visual.setP(-8.0 + hop_wave * 18.0)
            visual.setR(math.sin(progress * math.pi * 2.0) * 6.0)
            ear_pitch = -12.0 + hop_wave * 10.0
            head_pitch = -5.0 + hop_wave * 8.0
            foot_pitch = -18.0 + hop_wave * 26.0
            tail_bob = 12.0 - hop_wave * 8.0
        elif state == "telegraph":
            visual.setZ(0.02)
            visual.setP(6.0 + wave * 2.5)
            visual.setR(wave * 5.0)
            ear_pitch = -24.0 + wave * 5.0
            head_pitch = 12.0
            foot_pitch = -10.0
            tail_bob = -8.0 + wave * 6.0
        elif state == "lunge":
            visual.setZ(0.02 + hop_wave * 0.05)
            visual.setP(-19.0 + hop_wave * 7.0)
            visual.setR(math.sin(progress * math.pi * 2.0) * 4.0)
            ear_pitch = -34.0
            head_pitch = -15.0
            foot_pitch = 24.0 - hop_wave * 12.0
            tail_bob = 16.0
        else:
            visual.setZ(0.03 + abs(wave) * 0.04)
            visual.setP(wave * 10.0)
            visual.setR(wave * 7.0)
            ear_pitch = -18.0 + wave * 10.0
            head_pitch = wave * 8.0
            foot_pitch = wave * 16.0
            tail_bob = wave * 18.0

        if enemy.body_node:
            squeeze = 1.0 + hop_wave * 0.08 if state == "hop" else 1.0 + wave * 0.018
            enemy.body_node.setScale(1.0, 1.0 + (squeeze - 1.0) * 0.5, squeeze)
        if enemy.head_node:
            enemy.head_node.setP(head_pitch)
            enemy.head_node.setR(wave * 2.0)
        if enemy.left_detail_node:
            enemy.left_detail_node.setHpr(-6.0 + wave * 4.0, ear_pitch, -5.0)
        if enemy.right_detail_node:
            enemy.right_detail_node.setHpr(6.0 - wave * 4.0, ear_pitch, 5.0)
        if enemy.left_foot_node:
            enemy.left_foot_node.setP(foot_pitch)
            enemy.left_foot_node.setR(-7.0 + wave * 3.0)
        if enemy.right_foot_node:
            enemy.right_foot_node.setP(foot_pitch)
            enemy.right_foot_node.setR(7.0 - wave * 3.0)
        if enemy.tail_node:
            enemy.tail_node.setP(tail_bob)
            enemy.tail_node.setR(wave * 6.0)

    def _animate_monster(self, enemy: SceneEnemy, dt: float, moving: bool):
        enemy.animation_phase += dt * (4.6 if moving else 1.7)
        crawl = math.sin(enemy.animation_phase)
        crawl_fast = math.sin(enemy.animation_phase * 2.0)
        visual = enemy.visual_node or enemy.node

        if moving:
            visual.setZ(0.03 + abs(crawl) * 0.045)
            visual.setP(crawl * 4.5)
            visual.setR(crawl_fast * 2.8)
            body_scale_y = 1.0 + crawl * 0.05
            body_scale_z = 1.0 - crawl * 0.035
        else:
            visual.setZ(0.02 + crawl * 0.018)
            visual.setP(crawl * 1.6)
            visual.setR(crawl_fast * 1.0)
            body_scale_y = 1.0 + crawl * 0.018
            body_scale_z = 1.0 - crawl * 0.012

        if enemy.body_node:
            enemy.body_node.setScale(1.0, body_scale_y, body_scale_z)
        if enemy.head_node:
            enemy.head_node.setP(-2.0 + crawl * 5.5)
            enemy.head_node.setR(crawl_fast * 2.5)
        if enemy.left_detail_node:
            enemy.left_detail_node.setHpr(-24.0 + crawl * 8.0, 32.0 + crawl_fast * 6.0, -14.0)
        if enemy.right_detail_node:
            enemy.right_detail_node.setHpr(24.0 - crawl * 8.0, 32.0 - crawl_fast * 6.0, 14.0)
        if enemy.left_foot_node:
            enemy.left_foot_node.setP(crawl * 13.0)
            enemy.left_foot_node.setR(-18.0 + crawl_fast * 6.0)
        if enemy.right_foot_node:
            enemy.right_foot_node.setP(-crawl * 13.0)
            enemy.right_foot_node.setR(18.0 - crawl_fast * 6.0)
        if enemy.tail_node:
            enemy.tail_node.setH(crawl_fast * 5.0)
            enemy.tail_node.setP(-4.0 + crawl * 4.0)

    def _start_rabbit_hop(
        self, enemy: SceneEnemy, enemy_pos: Vec3, to_player: Vec3, distance: float
    ):
        if distance <= 0.05:
            direction = Vec3(self.rng.uniform(-1, 1), self.rng.uniform(-1, 1), 0)
        elif distance < 1.6:
            direction = to_player * -1.0
        else:
            direction = Vec3(to_player)

        if direction.length() == 0:
            direction = Vec3(0, 1, 0)
        direction.normalize()

        sideways = Vec3(-direction.getY(), direction.getX(), 0)
        hop_distance = self.rng.uniform(0.72, 1.28)
        strafe = sideways * self.rng.uniform(-0.35, 0.35)
        target = self._clamp_enemy_position(enemy, enemy_pos + direction * hop_distance + strafe)

        enemy.ai_state = "hop"
        enemy.hop_duration = self.rng.uniform(0.24, 0.34)
        enemy.state_timer = enemy.hop_duration
        enemy.hop_start_pos = Vec3(enemy_pos.getX(), enemy_pos.getY(), 0)
        enemy.hop_target_pos = Vec3(target.getX(), target.getY(), 0)

    def _spawn_rabbit_attack_tell(self, enemy: SceneEnemy):
        pos = enemy.node.getPos() + Vec3(0, 0, 0.98)
        for index, offset in enumerate((-0.22, 0.22)):
            self._spawn_hit_piece(
                name=f"rabbit-warning-{index}",
                size=(0.1, 0.04, 0.18),
                color=(1.0, 0.12, 0.12, 0.8),
                pos=pos + Vec3(offset, 0, 0),
                velocity=Vec3(offset * 1.2, 0, 1.0),
                lifetime=0.34,
            )

    def _clamp_to_arena(self, pos: Vec3) -> Vec3:
        pos.setX(max(ARENA_MIN_X, min(ARENA_MAX_X, pos.getX())))
        pos.setY(max(ARENA_MIN_Y, min(ARENA_MAX_Y, pos.getY())))
        pos.setZ(0)
        return pos

    def _clamp_enemy_position(self, enemy: SceneEnemy, pos: Vec3) -> Vec3:
        if enemy.bounds is None:
            return self._clamp_to_arena(pos)

        min_x, max_x, min_y, max_y = enemy.bounds
        pos.setX(max(min_x, min(max_x, pos.getX())))
        pos.setY(max(min_y, min(max_y, pos.getY())))
        pos.setZ(0)
        return pos

    def _update_camera(self):
        if self.camera is None:
            return
        target = self.player.getPos()
        self.camera.setPos(target.getX(), target.getY() - 18.0, 14.0)
        self.camera.lookAt(target.getX(), target.getY() + 1.0, 0.4)

    def handle_interact(self):
        if self.fishing_state == "idle":
            chest = self._nearest_chest()
            if chest is not None:
                self._try_open_chest(chest)
            elif self._distance_to_nearest_raft() <= SHOP_RANGE:
                self._use_raft()
            elif self._distance_to_shop() <= SHOP_RANGE:
                self.shop_open = not self.shop_open
                self.forge_open = False
                if self.shop_open:
                    self.inspect_open = False
                    self._log("The rod seller opens the rack. Press 1-4 to choose.")
                else:
                    self._log("You close the rod shop menu.")
            elif self._distance_to_forge() <= FORGE_RANGE:
                self.forge_open = not self.forge_open
                self.shop_open = False
                if self.forge_open:
                    self.inspect_open = False
                    self._log("The armorer opens the forge rack. Press 1-7 to choose armor.")
                else:
                    self._log("You close the forge menu.")
            else:
                self.shop_open = False
                self.forge_open = False
                self._start_fishing_cast()
        elif self.fishing_state == "waiting":
            self._log("Not yet. The bobber only drifts.")
        elif self.fishing_state == "bite":
            self._finish_fishing(success=True)

    def handle_fishing_action(self):
        self.handle_interact()

    def _distance_to_shop(self) -> float:
        return (self.player.getPos() - self.shop_spot).length()

    def _distance_to_forge(self) -> float:
        return (self.player.getPos() - FORGE_SPOT).length()

    def _distance_to_nearest_raft(self) -> float:
        player_pos = self.player.getPos()
        return min(
            (player_pos - HOME_RAFT_SPOT).length(),
            (player_pos - LEVEL2_RAFT_SPOT).length(),
        )

    def _use_raft(self):
        player_pos = self.player.getPos()
        if (player_pos - LEVEL2_RAFT_SPOT).length() <= SHOP_RANGE:
            destination = Vec3(0, 3.0, 0)
            message = "The raft carries you back to the old dock."
        else:
            destination = Vec3(LEVEL2_ARRIVAL_SPOT)
            message = "The raft creaks across the deep water to the level 2 shore."

        self.shop_open = False
        self.forge_open = False
        self.inspect_open = False
        self.player.setPos(destination)
        self.player.setH(0)
        self._clear_fishing_visuals()
        self.fishing_state = "idle"
        self._set_catch_banner("Raft crossing")
        self._log(message)

    def _nearest_fishing_spot(self) -> Tuple[str, Vec3, float]:
        player_pos = self.player.getPos()
        spots = (
            ("lake", self.fishing_spot, (player_pos - self.fishing_spot).length()),
            ("cave pool", self.cave_fishing_spot, (player_pos - self.cave_fishing_spot).length()),
            ("level 2 lake", self.level2_fishing_spot, (player_pos - self.level2_fishing_spot).length()),
        )
        return min(spots, key=lambda item: item[2])

    def _nearest_chest(self) -> Optional[SceneChest]:
        player_pos = self.player.getPos()
        unopened = [
            ((chest.pos - player_pos).length(), chest)
            for chest in self.chests
            if not chest.opened and (chest.pos - player_pos).length() <= CHEST_RANGE
        ]
        if not unopened:
            return None
        unopened.sort(key=lambda item: item[0])
        return unopened[0][1]

    def _living_guards_for_chest(self, chest: SceneChest) -> List[SceneEnemy]:
        guards = []
        for enemy in self.enemies:
            if (enemy.node.getPos() - chest.pos).length() <= CHEST_GUARD_RADIUS:
                guards.append(enemy)
        return guards

    def _try_open_chest(self, chest: SceneChest):
        guards = self._living_guards_for_chest(chest)
        if guards:
            self._log(f"{chest.name} is guarded by {len(guards)} nearby mob(s).")
            self._log("Clear the guards, then press E by the chest.")
            return

        chest.opened = True
        self.gold += chest.reward_gold
        lid = chest.node.find("**/chest-lid")
        glow = chest.node.find("**/chest-glow")
        if not lid.isEmpty():
            lid.setPos(0, 0.2, 0.88)
            lid.setHpr(0, -32, 0)
        if not glow.isEmpty():
            glow.setColorScale(1.0, 1.0, 1.0, 0.08)
        self._spawn_gold_reward_effect(chest.pos, chest.reward_gold)
        self._set_catch_banner(f"Chest opened!\n+{chest.reward_gold} gold")
        self._log(f"You open {chest.name} and find {chest.reward_gold} gold.")

    def _select_menu_item(self, index: int):
        if self.shop_open:
            self.select_shop_rod(index)
        elif self.forge_open:
            self.select_armor(index)

    def select_shop_rod(self, tier: int):
        if not self.shop_open:
            return
        if tier < 0 or tier >= len(FISHING_RODS):
            return
        if self._distance_to_shop() > SHOP_RANGE + 0.45:
            self.shop_open = False
            self._log("You are too far from the rod shop.")
            return

        rod = FISHING_RODS[tier]
        if tier == self.rod_tier:
            self._log(f"You already have the {rod.name}.")
            return
        if tier < self.rod_tier:
            self._log(f"The {rod.name} is weaker than your current rod.")
            return

        if self.gold < rod.price:
            needed = rod.price - self.gold
            self._log(f"{rod.name} costs {rod.price} gold. You need {needed} more.")
            return

        self.gold -= rod.price
        self.rod_tier = rod.tier
        self._build_weapon_model(self.current_weapon)
        self._set_catch_banner(f"Rod upgraded!\n{rod.name}")
        self._log(f"You buy the {rod.name} for {rod.price} gold.")
        self._log("Better rods pull stronger relics from deeper water.")
        self._update_shop_ui()

    def select_armor(self, tier: int):
        if not self.forge_open:
            return
        if tier < 0 or tier >= len(ARMOR_TIERS):
            return
        if self._distance_to_forge() > FORGE_RANGE + 0.45:
            self.forge_open = False
            self._log("You are too far from the forge.")
            return

        armor = armor_tier_for_index(tier)
        if tier <= self.player_armor_tier:
            self._log(f"You already have armor at least as good as {armor.name}.")
            return
        if self.gold < armor.cost:
            needed = armor.cost - self.gold
            self._log(f"{armor.name} costs {armor.cost} gold. You need {needed} more.")
            return

        self.gold -= armor.cost
        self.player_armor_tier = tier
        self.player_armor_value = armor.armor_value
        self._set_catch_banner(f"Armor bought!\n{armor.name}")
        self._log(f"You buy {armor.name}. It blocks {armor.armor_value} damage.")
        self._update_forge_ui()

    def toggle_inspection(self):
        if self.current_weapon is None:
            self._log("There is no recovered weapon to inspect.")
            return

        self.shop_open = False
        self.inspect_open = not self.inspect_open
        self._update_inspection_ui()

    def _start_fishing_cast(self):
        spot_name, _spot_pos, distance = self._nearest_fishing_spot()
        if distance > FISHING_RANGE:
            self._log("The water is too far away to cast.")
            return
        self.active_fishing_spot_name = spot_name

        self.inspect_open = False
        self._clear_inspection_preview()
        self._update_inspection_ui()

        player_pos = self.player.getPos()
        self.cast_start_pos = Vec3(player_pos.getX(), player_pos.getY() + 0.8, 0.9)
        if spot_name == "cave pool":
            self.cast_target_pos = Vec3(
                CAVE_POOL_CENTER.getX() + self.rng.uniform(-2.2, 2.2),
                CAVE_POOL_CENTER.getY() + self.rng.uniform(-1.2, 1.2),
                0.18,
            )
        elif spot_name == "level 2 lake":
            self.cast_target_pos = Vec3(
                LEVEL2_LAKE_CENTER.getX() + self.rng.uniform(-4.2, 4.2),
                LEVEL2_LAKE_CENTER.getY() + self.rng.uniform(-2.8, 2.8),
                0.18,
            )
        else:
            self.cast_target_pos = Vec3(
                max(-8.0, min(8.0, player_pos.getX() + self.rng.uniform(-2.2, 2.2))),
                self.rng.uniform(8.2, 12.8),
                0.18,
            )
        self.fishing_state = "casting"
        self.fishing_timer = 0.0
        self.fishing_phase = 0.0
        self._build_weapon_model(None)
        self._clear_fishing_visuals()
        self.shop_open = False
        self._create_bobber(self.cast_start_pos)
        if spot_name == "cave pool":
            self._log(f"You cast into the glowing cave pool with the {fishing_rod_for_tier(self.rod_tier).name}.")
        elif spot_name == "level 2 lake":
            self._log(f"You cast into the level 2 lake. Stronger relics tug below.")
        else:
            self._log(f"You cast with the {fishing_rod_for_tier(self.rod_tier).name}.")

    def _update_fishing(self, dt: float):
        self.fishing_phase += dt
        self._update_fishing_ripples(dt)

        if self.bobber_node is not None and self.fishing_state in {"waiting", "bite"}:
            bob = Vec3(self.cast_target_pos)
            bob.setZ(0.16 + math.sin(self.fishing_phase * 7.0) * 0.035)
            self.bobber_node.setPos(bob)
            self._update_cast_line(bob)

        if self.fishing_state == "idle":
            return

        if self.fishing_state == "casting":
            self.fishing_timer += dt
            progress = min(1.0, self.fishing_timer / 0.58)
            arc = math.sin(progress * math.pi) * 1.35
            pos = self._lerp_vec3(self.cast_start_pos, self.cast_target_pos, progress)
            pos.setZ(pos.getZ() + arc)
            if self.bobber_node is not None:
                self.bobber_node.setPos(pos)
                self._update_cast_line(pos)

            if progress >= 1.0:
                self.fishing_state = "waiting"
                wait_min = max(0.75, 1.25 - self.rod_tier * 0.12)
                wait_max = max(1.45, 2.9 - self.rod_tier * 0.22)
                self.fishing_timer = self.rng.uniform(wait_min, wait_max)
                self._log("The bobber settles. Watch it closely.")
                self._spawn_fishing_ripple(self.cast_target_pos, soft=True)
            return

        if self.fishing_state == "waiting":
            self.fishing_timer -= dt
            if self.fishing_timer <= 0.0:
                self.fishing_state = "bite"
                self.fishing_timer = 1.25
                self._log("Bite! Press E now!")
                self._spawn_fishing_ripple(self.cast_target_pos, soft=False)
            return

        if self.fishing_state == "bite":
            self.fishing_timer -= dt
            if self.fishing_timer <= 0.0:
                self._finish_fishing(success=False)
            return

        if self.fishing_state == "reeling":
            self.fishing_timer -= dt
            if self.fishing_timer <= 0.0:
                self.fishing_state = "idle"
                self._clear_fishing_visuals()

    def _finish_fishing(self, success: bool):
        if success:
            self._complete_fishing_success()
        else:
            self._log("The bobber goes still. Whatever it was sinks away.")
            self._build_weapon_model(self.current_weapon)

        self.fishing_state = "reeling"
        self.fishing_timer = 0.55

    def _complete_fishing_success(self):
        effective_rod_tier = self.rod_tier
        if self.active_fishing_spot_name == "level 2 lake":
            effective_rod_tier = min(len(FISHING_RODS) - 1, self.rod_tier + 3)
            for attempt in range(4):
                self.current_weapon = generate_weapon(self.rng, effective_rod_tier)
                if self.current_weapon.rarity in {"relic", "mythic"} or attempt == 3:
                    break
        else:
            self.current_weapon = generate_weapon(self.rng, effective_rod_tier)
        if self.active_fishing_spot_name == "level 2 lake":
            self.current_weapon.base_damage += 3
        self._build_weapon_model(self.current_weapon)
        self.fish_count += 1
        hidden_count = self.current_weapon.hidden_trait_count()
        plural = "trait" if hidden_count == 1 else "traits"
        self._spawn_catch_burst(self.cast_target_pos, self.current_weapon)
        self._set_catch_banner(f"Caught!\n{self.current_weapon.name}")
        self.inspect_open = True
        self._update_inspection_ui()
        self._log(f"You wrench {self.current_weapon.name} from the lake.")
        self._log(f"It feels {self.current_weapon.rarity} and hides {hidden_count} {plural}.")

        if self.fish_count % 3 == 0:
            self.spawn_monster()
        else:
            self.spawn_rabbits(3)
        if self.active_fishing_spot_name == "cave pool":
            self.spawn_wisps(1)
        elif self.active_fishing_spot_name == "level 2 lake":
            self._spawn_level2_lake_ambush()

    def _spawn_level2_lake_ambush(self):
        choices = (
            ("snapper", LEVEL2_LAKE_CENTER + Vec3(-8.0, 3.0, 0)),
            ("wisp", LEVEL2_LAKE_CENTER + Vec3(8.0, -2.5, 0)),
            ("monster", LEVEL2_LAKE_CENTER + Vec3(0.0, -8.0, 0)),
        )
        kind, pos = choices[self.fish_count % len(choices)]
        if kind == "snapper":
            enemy = self._make_snapper(1200 + self.fish_count, pos)
        elif kind == "wisp":
            enemy = self._make_wisp(1200 + self.fish_count, pos)
        else:
            enemy = self._make_monster(pos)
        self.enemies.append(self._toughen_level2_enemy(enemy))
        self._log("Something tougher rises near the level 2 lake.")

    def _create_bobber(self, pos: Vec3):
        self.bobber_node = self.render.attachNewNode("cast-bobber")
        self.bobber_node.setPos(pos)
        make_box(self.bobber_node, "bobber-top", (0.22, 0.22, 0.13), (0.9, 0.05, 0.05, 1), (0, 0, 0.08))
        make_box(self.bobber_node, "bobber-bottom", (0.2, 0.2, 0.12), (0.96, 0.96, 0.9, 1), (0, 0, -0.05))
        make_box(
            self.bobber_node,
            "bobber-glint",
            (0.32, 0.05, 0.025),
            (0.9, 0.96, 1.0, 0.5),
            (0, 0, 0.18),
        )
        self._create_cast_line()
        self._update_cast_line(pos)

    def _create_cast_line(self):
        self.cast_line_node = self.render.attachNewNode("cast-line")
        self.cast_line_segment = make_box(
            self.cast_line_node,
            "line-to-bobber",
            (0.025, 1.0, 0.025),
            (0.82, 0.9, 0.92, 0.72),
            (0, 0, 0),
        )

    def _update_cast_line(self, bobber_pos: Vec3):
        if self.cast_line_node is None or self.cast_line_segment is None:
            return

        player_pos = self.player.getPos()
        start = Vec3(player_pos.getX() + 0.34, player_pos.getY() + 0.72, 1.25)
        end = Vec3(bobber_pos.getX(), bobber_pos.getY(), bobber_pos.getZ() + 0.18)
        delta = end - start
        horizontal_length = math.sqrt(delta.getX() * delta.getX() + delta.getY() * delta.getY())
        length = max(0.1, math.sqrt(horizontal_length * horizontal_length + delta.getZ() * delta.getZ()))
        midpoint = start + delta * 0.5

        heading = math.degrees(math.atan2(-delta.getX(), delta.getY()))
        pitch = math.degrees(math.atan2(delta.getZ(), horizontal_length))
        self.cast_line_node.setPos(midpoint)
        self.cast_line_node.setHpr(heading, -pitch, 0)
        self.cast_line_segment.setScale(0.025, length, 0.025)

    def _spawn_fishing_ripple(self, pos: Vec3, soft: bool):
        count = 2 if soft else 4
        color = (0.72, 0.9, 1.0, 0.28 if soft else 0.5)
        for index in range(count):
            ripple = self.render.attachNewNode(f"fishing-ripple-{index}")
            ripple.setPos(pos.getX(), pos.getY(), 0.13 + index * 0.01)
            make_box(ripple, "ripple-east-west", (0.7, 0.06, 0.025), color, (0, 0, 0))
            make_box(ripple, "ripple-north-south", (0.06, 0.7, 0.025), color, (0, 0, 0))
            lifetime = 0.75 + index * 0.16
            self.fishing_ripples.append((ripple, lifetime, lifetime))

    def _update_fishing_ripples(self, dt: float):
        live_ripples = []
        for ripple, lifetime, max_lifetime in self.fishing_ripples:
            lifetime -= dt
            if lifetime <= 0.0:
                ripple.removeNode()
                continue

            progress = 1.0 - lifetime / max_lifetime
            ripple.setScale(0.45 + progress * 2.4)
            ripple.setColorScale(1, 1, 1, lifetime / max_lifetime)
            live_ripples.append((ripple, lifetime, max_lifetime))

        self.fishing_ripples = live_ripples

    def _spawn_catch_burst(self, pos: Vec3, weapon: Weapon):
        burst_pos = Vec3(pos.getX(), pos.getY(), 0.2)
        glow = weapon_glow_color(weapon)
        for index in range(8):
            angle = (math.pi * 2.0 * index) / 8.0
            outward = Vec3(math.cos(angle), math.sin(angle), 0)
            self._spawn_hit_piece(
                name=f"catch-splash-{index}",
                size=(0.1, 0.1, 0.18),
                color=(0.42, 0.78, 1.0, 0.78),
                pos=burst_pos,
                velocity=outward * self.rng.uniform(1.4, 2.8) + Vec3(0, 0, self.rng.uniform(2.4, 4.2)),
                lifetime=self.rng.uniform(0.55, 0.85),
            )

        for index in range(5):
            self._spawn_hit_piece(
                name=f"catch-glow-{index}",
                size=(0.12, 0.12, 0.12),
                color=glow,
                pos=burst_pos + Vec3(0, 0, 0.15),
                velocity=Vec3(
                    self.rng.uniform(-1.6, 1.6),
                    self.rng.uniform(-1.6, 1.6),
                    self.rng.uniform(2.8, 4.8),
                ),
                lifetime=self.rng.uniform(0.75, 1.05),
            )

    def _clear_fishing_visuals(self):
        if self.bobber_node is not None:
            self.bobber_node.removeNode()
            self.bobber_node = None
        if self.cast_line_node is not None:
            self.cast_line_node.removeNode()
            self.cast_line_node = None
            self.cast_line_segment = None

        for ripple, _lifetime, _max_lifetime in self.fishing_ripples:
            ripple.removeNode()
        self.fishing_ripples = []

    def _set_catch_banner(self, text: str):
        self.catch_banner_text = text
        self.catch_banner_timer = 2.2

    def _lerp_vec3(self, start: Vec3, end: Vec3, amount: float) -> Vec3:
        return start + (end - start) * amount

    def dodge(self):
        if self.player_hp <= 0:
            return
        if self.fishing_state != "idle":
            return
        if self.dodge_time > 0.0 or self.dodge_cooldown > 0.0:
            return
        if not self._spend_stamina(DODGE_STAMINA_COST):
            self._log("Too tired to dodge.")
            return

        move_x = 0.0
        move_y = 0.0
        if self.keys["w"]:
            move_y += 1.0
        if self.keys["s"]:
            move_y -= 1.0
        if self.keys["a"]:
            move_x -= 1.0
        if self.keys["d"]:
            move_x += 1.0

        direction = Vec3(move_x, move_y, 0)
        if direction.length() == 0:
            heading = math.radians(self.player.getH())
            direction = Vec3(-math.sin(heading), math.cos(heading), 0)
        direction.normalize()

        self.dodge_direction = direction
        self.dodge_time = DODGE_DURATION
        self.dodge_cooldown = DODGE_COOLDOWN
        self._spawn_dodge_dust(direction)
        self._log("You dodge-roll.")

    def _spawn_dodge_dust(self, direction: Vec3):
        origin = self.player.getPos() + Vec3(0, 0, 0.12)
        backward = direction * -1.0
        sideways = Vec3(-direction.getY(), direction.getX(), 0)
        if sideways.length() == 0:
            sideways = Vec3(1, 0, 0)
        else:
            sideways.normalize()

        for index in range(8):
            spray = (
                backward * self.rng.uniform(1.2, 2.8)
                + sideways * self.rng.uniform(-1.8, 1.8)
                + Vec3(0, 0, self.rng.uniform(0.7, 1.8))
            )
            self._spawn_hit_piece(
                name=f"dodge-dust-{index}",
                size=(
                    self.rng.uniform(0.12, 0.22),
                    self.rng.uniform(0.08, 0.18),
                    self.rng.uniform(0.045, 0.09),
                ),
                color=(0.54, 0.44, 0.3, self.rng.uniform(0.42, 0.68)),
                pos=origin + backward * 0.28 + sideways * self.rng.uniform(-0.22, 0.22),
                velocity=spray,
                lifetime=self.rng.uniform(0.32, 0.52),
            )

    def _spawn_sprint_dust(self, direction: Vec3):
        origin = self.player.getPos() + Vec3(0, 0, 0.08)
        backward = direction * -1.0
        sideways = Vec3(-direction.getY(), direction.getX(), 0)
        if sideways.length() == 0:
            sideways = Vec3(1, 0, 0)
        else:
            sideways.normalize()

        for index in range(2):
            side = -1.0 if index == 0 else 1.0
            self._spawn_hit_piece(
                name=f"sprint-dust-{index}",
                size=(0.11, 0.06, 0.045),
                color=(0.62, 0.54, 0.38, 0.46),
                pos=origin + backward * 0.32 + sideways * side * self.rng.uniform(0.12, 0.24),
                velocity=backward * self.rng.uniform(0.9, 1.5)
                + sideways * side * self.rng.uniform(0.2, 0.55)
                + Vec3(0, 0, self.rng.uniform(0.25, 0.55)),
                lifetime=self.rng.uniform(0.18, 0.28),
            )

    def _player_is_invulnerable(self) -> bool:
        return self.dodge_time > 0.0

    def attack(self):
        if self.player_hp <= 0:
            self._log("Respawning soon...")
            return
        if self.fishing_state != "idle":
            self._log("You are busy with the line.")
            return
        if self.attack_cooldown > 0:
            return
        if self.current_weapon is None:
            self._log("Your hands are empty. The lake may fix that.")
            self.attack_cooldown = 0.12
            return

        self._start_swing()
        targets = self._enemies_in_attack_range()
        if not targets:
            if is_ranged_weapon(self.current_weapon):
                self._spawn_ranged_shot()
                self._log(f"{self.current_weapon.name} fires into empty air.")
            else:
                self._log(f"{self.current_weapon.name} cuts only air.")
            self.attack_cooldown = 0.08
            return

        if len(targets) > 1:
            if is_ranged_weapon(self.current_weapon):
                self._log(f"{self.current_weapon.name} arcs through {len(targets)} enemies.")
            else:
                self._log(f"{self.current_weapon.name} cleaves through {len(targets)} enemies.")

        any_revealed = False
        for target in targets:
            if target not in self.enemies:
                continue

            if is_ranged_weapon(self.current_weapon):
                self._spawn_ranged_shot(target)

            any_revealed = self._resolve_weapon_hit(target) or any_revealed

            if self.player_hp == 0:
                break

        if any_revealed:
            self._update_inspection_ui()
            self._log("Press I to inspect the updated weapon card.")

        self.attack_cooldown = 0.08

    def use_weapon_ability(self):
        if self.player_hp <= 0:
            self._log("Respawning soon...")
            return
        if self.fishing_state != "idle":
            self._log("You are busy with the line.")
            return
        if self.current_weapon is None:
            self._log("You need a weapon before you can use an ability.")
            return
        if self.weapon_ability_cooldown > 0.0:
            self._log(f"Ability is recharging: {self.weapon_ability_cooldown:.1f}s.")
            return
        if not self._spend_stamina(ABILITY_STAMINA_COST):
            self._log("Too tired to use the weapon ability.")
            return

        ability = weapon_ability(self.current_weapon)
        self._start_swing(powered=True)
        self._spawn_ability_burst()
        targets = self._active_ability_targets()
        if not targets:
            if is_ranged_weapon(self.current_weapon):
                self._spawn_ranged_shot(powered=True)
                self._log(f"{ability.display_name} fires into the distance.")
            else:
                self._log(f"{ability.display_name} erupts, but hits nothing.")
            self.weapon_ability_cooldown = WEAPON_ABILITY_COOLDOWN
            self.attack_cooldown = 0.7
            return

        if is_ranged_weapon(self.current_weapon):
            self._log(f"You unleash {ability.display_name}.")
        else:
            self._log(f"{ability.display_name} bursts out in a wide shockwave.")

        any_revealed = False
        for target in targets:
            if target not in self.enemies:
                continue
            if is_ranged_weapon(self.current_weapon):
                self._spawn_ranged_shot(target, powered=True)
            any_revealed = self._resolve_weapon_hit(
                target,
                damage_bonus=ACTIVE_DAMAGE_BONUS,
                bonus_message=f"{ability.display_name} adds {ACTIVE_DAMAGE_BONUS} damage.",
            ) or any_revealed
            if self.player_hp == 0:
                break

        if any_revealed:
            self._update_inspection_ui()
            self._log("Press I to inspect the updated weapon card.")

        self.weapon_ability_cooldown = WEAPON_ABILITY_COOLDOWN
        self.attack_cooldown = 0.9

    def _resolve_weapon_hit(
        self,
        target: SceneEnemy,
        damage_bonus: int = 0,
        bonus_message: str = "",
    ) -> bool:
        if self.current_weapon is None or target not in self.enemies:
            return False

        enemy_state = EnemyState(
            name=target.name,
            kind=target.kind,
            hp=target.hp,
            max_hp=target.max_hp,
        )
        result = resolve_attack(self.current_weapon, enemy_state, self.rng)
        target.hp = max(0, result.enemy_hp_after - damage_bonus)
        self.player_hp = min(self.player_max_hp, self.player_hp + result.healing)
        self.player_hp = max(0, self.player_hp - result.self_damage)

        for message in result.messages[-2:]:
            self._log(message)
        if damage_bonus:
            self._log(bonus_message or f"The ability adds {damage_bonus} damage.")

        newly_revealed = discover_traits(self.current_weapon, result.discovered_traits)
        for trait_name in newly_revealed:
            self._log(f"Discovered weapon power: {trait_name}.")

        if result.healing:
            self._log(f"You recover {result.healing} health.")
        if result.self_damage:
            self._pause_hp_regen()
            self._log(f"The weapon hurts you for {result.self_damage}.")
        if self.player_hp == 0:
            self._start_death_sequence()

        self._apply_hit_feedback(target)

        if target.hp == 0:
            reward = gold_reward_for_enemy(target.kind)
            if reward:
                self.gold += reward
                self._spawn_gold_reward_effect(target.node.getPos(), reward)
                self._log(f"You collect {reward} gold coins.")
            if target.kind == "rabbit":
                self._spawn_rabbit_defeat_effects(target)
            target.node.removeNode()
            self.enemies.remove(target)

        return bool(newly_revealed)

    def _active_ability_targets(self) -> List[SceneEnemy]:
        if self.current_weapon is None:
            return []

        player_pos = self.player.getPos()
        nearby: List[Tuple[float, SceneEnemy]] = []
        is_ranged = is_ranged_weapon(self.current_weapon)
        if is_ranged:
            heading = math.radians(self.player.getH())
            forward = Vec3(-math.sin(heading), math.cos(heading), 0)

        for enemy in self.enemies:
            to_enemy = enemy.node.getPos() - player_pos
            to_enemy.setZ(0)
            distance = to_enemy.length()
            if is_ranged:
                if distance > ACTIVE_RANGED_RANGE:
                    continue
                if distance > 0.01:
                    aim = Vec3(to_enemy)
                    aim.normalize()
                    if forward.dot(aim) < -0.05:
                        continue
            elif distance > ACTIVE_MELEE_RANGE:
                continue
            nearby.append((distance, enemy))

        nearby.sort(key=lambda item: item[0])
        targets = [enemy for _distance, enemy in nearby]
        if is_ranged:
            return targets[:4] if self.current_weapon.weapon_type == "staff" else targets[:3]
        return targets

    def _spawn_ability_burst(self):
        if self.current_weapon is None:
            return

        origin = self.player.getPos() + Vec3(0, 0, 0.7)
        glow = weapon_glow_color(self.current_weapon)
        for index in range(14):
            angle = (math.pi * 2.0 * index) / 14.0
            outward = Vec3(math.cos(angle), math.sin(angle), 0)
            self._spawn_hit_piece(
                name=f"ability-burst-{index}",
                size=(0.12, 0.12, 0.055),
                color=glow,
                pos=origin + outward * 0.22,
                velocity=outward * self.rng.uniform(2.2, 4.0)
                + Vec3(0, 0, self.rng.uniform(0.6, 1.5)),
                lifetime=self.rng.uniform(0.34, 0.58),
            )

    def _spawn_ranged_shot(self, target: Optional[SceneEnemy] = None, powered: bool = False):
        if self.current_weapon is None:
            return

        weapon_type = self.current_weapon.weapon_type
        glow = weapon_glow_color(self.current_weapon)
        heading = math.radians(self.player.getH())
        forward = Vec3(-math.sin(heading), math.cos(heading), 0)
        right = Vec3(forward.getY(), -forward.getX(), 0)
        start = self.player.getPos() + forward * 0.85 + right * 0.28 + Vec3(0, 0, 1.05)
        if target is None:
            end = start + forward * min(RANGED_ATTACK_RANGE, 7.5)
        else:
            end = target.node.getPos() + Vec3(0, 0, 0.68)

        delta = end - start
        distance = max(0.1, delta.length())
        direction = Vec3(delta)
        direction.normalize()
        speed = 32.0 if powered else 24.0
        lifetime = max(0.1, min(0.38 if powered else 0.42, distance / speed))
        velocity = delta * (1.0 / lifetime)
        shot = self.render.attachNewNode(f"{weapon_type}-shot")
        shot.setPos(start)
        horizontal = math.sqrt(delta.getX() * delta.getX() + delta.getY() * delta.getY())
        shot.setHpr(
            math.degrees(math.atan2(-delta.getX(), delta.getY())),
            -math.degrees(math.atan2(delta.getZ(), horizontal)),
            0,
        )

        if weapon_type == "staff":
            orb_size = 0.24 if powered else 0.16
            make_ellipsoid(
                shot,
                "staff-orb-shot",
                (orb_size, orb_size, orb_size),
                glow,
                (0, 0, 0),
                segments=10,
                rings=5,
            )
            ring = 0.66 if powered else 0.46
            make_box(shot, "staff-orb-ring-a", (ring, 0.04, 0.04), glow, (0, 0, 0), (0, 0, 35))
            make_box(shot, "staff-orb-ring-b", (0.04, ring, 0.04), glow, (0, 0, 0), (0, 0, 35))
            spin = Vec3(0, 0, 760 if powered else 520)
        elif weapon_type == "crossbow":
            make_box(shot, "crossbow-bolt-shot", (0.1 if powered else 0.08, 0.96 if powered else 0.76, 0.1 if powered else 0.08), (0.68, 0.62, 0.5, 1), (0, 0.18, 0))
            make_flat_prism(shot, "crossbow-bolt-shot-head", ((0, 0.72), (0.16, 0.46), (-0.16, 0.46)), 0.16 if powered else 0.12, glow, (0, 0, 0.02))
            make_box(shot, "crossbow-bolt-shot-trail", (0.26 if powered else 0.18, 0.52 if powered else 0.38, 0.04), glow, (0, -0.25, 0), (0, 0, 35))
            spin = Vec3(0, 0, 0)
        else:
            make_box(shot, "arrow-shot-shaft", (0.07 if powered else 0.055, 1.0 if powered else 0.82, 0.07 if powered else 0.055), (0.55, 0.34, 0.16, 1), (0, 0.18, 0))
            make_flat_prism(shot, "arrow-shot-head", ((0, 0.78), (0.14, 0.52), (-0.14, 0.52)), 0.13 if powered else 0.1, glow, (0, 0, 0.02))
            make_box(shot, "arrow-shot-feather-left", (0.18, 0.05, 0.045), (0.92, 0.78, 0.42, 1), (-0.08, -0.23, 0), (0, 0, -24))
            make_box(shot, "arrow-shot-feather-right", (0.18, 0.05, 0.045), (0.92, 0.78, 0.42, 1), (0.08, -0.23, 0), (0, 0, 24))
            spin = Vec3(0, 0, 0)

        self.ranged_shots.append(
            RangedShot(
                node=shot,
                velocity=velocity,
                lifetime=lifetime,
                max_lifetime=lifetime,
                spin_rate=spin,
                impact_pos=Vec3(end),
                impact_color=glow,
            )
        )

    def _apply_hit_feedback(self, target: SceneEnemy):
        direction = target.node.getPos() - self.player.getPos()
        direction.setZ(0)
        if direction.length() == 0:
            direction = Vec3(0, -1, 0)
        else:
            direction.normalize()

        target.flash_time = 0.18
        target.knockback_velocity = direction * 11.0
        target.node.setColorScale(1.5, 0.42, 0.42, 1)

        if target.kind == "rabbit":
            self._spawn_rabbit_hit_effects(target, direction)

    def _spawn_rabbit_hit_effects(self, target: SceneEnemy, direction: Vec3):
        hit_pos = target.node.getPos() + Vec3(0, 0, 0.58)
        sideways = Vec3(-direction.getY(), direction.getX(), 0)
        if sideways.length() == 0:
            sideways = Vec3(1, 0, 0)
        else:
            sideways.normalize()

        fur_velocity = (
            direction * self.rng.uniform(3.2, 4.6)
            + sideways * self.rng.uniform(-1.4, 1.4)
            + Vec3(0, 0, self.rng.uniform(2.6, 3.8))
        )
        self._spawn_hit_piece(
            name="rabbit-fur-chip",
            size=(0.18, 0.12, 0.08),
            color=(0.98, 0.95, 0.9, 1),
            pos=hit_pos,
            velocity=fur_velocity,
            lifetime=0.72,
        )

        for index in range(4):
            drop_velocity = (
                direction * self.rng.uniform(1.5, 3.2)
                + sideways * self.rng.uniform(-1.8, 1.8)
                + Vec3(0, 0, self.rng.uniform(1.1, 2.4))
            )
            self._spawn_hit_piece(
                name=f"rabbit-blood-drop-{index}",
                size=(0.08, 0.08, 0.08),
                color=(0.65, 0.02, 0.04, 0.86),
                pos=hit_pos + Vec3(0, 0, self.rng.uniform(-0.05, 0.08)),
                velocity=drop_velocity,
                lifetime=self.rng.uniform(0.45, 0.68),
            )

    def _spawn_rabbit_defeat_effects(self, target: SceneEnemy):
        center = target.node.getPos() + Vec3(0, 0, 0.45)
        for index in range(8):
            angle = (math.pi * 2.0 * index) / 8.0
            outward = Vec3(math.cos(angle), math.sin(angle), 0)
            self._spawn_hit_piece(
                name=f"rabbit-puff-{index}",
                size=(0.18, 0.18, 0.12),
                color=(0.96, 0.96, 0.9, 0.72),
                pos=center + outward * 0.18,
                velocity=outward * self.rng.uniform(0.9, 1.8)
                + Vec3(0, 0, self.rng.uniform(1.6, 2.8)),
                lifetime=self.rng.uniform(0.55, 0.88),
            )

        for index in range(3):
            self._spawn_hit_piece(
                name=f"rabbit-defeat-ear-fur-{index}",
                size=(0.12, 0.08, 0.18),
                color=(1.0, 0.92, 0.92, 0.88),
                pos=center + Vec3(0, 0, 0.25),
                velocity=Vec3(
                    self.rng.uniform(-1.8, 1.8),
                    self.rng.uniform(-1.8, 1.8),
                    self.rng.uniform(2.2, 3.6),
                ),
                lifetime=self.rng.uniform(0.7, 1.0),
            )

    def _spawn_gold_reward_effect(self, pos: Vec3, reward: int):
        coin_count = max(1, min(5, reward // 5))
        origin = pos + Vec3(0, 0, 0.7)
        for index in range(coin_count):
            angle = (math.pi * 2.0 * index) / coin_count
            outward = Vec3(math.cos(angle), math.sin(angle), 0)
            self._spawn_hit_piece(
                name=f"gold-coin-{index}",
                size=(0.15, 0.15, 0.035),
                color=(0.98, 0.73, 0.18, 1),
                pos=origin,
                velocity=outward * self.rng.uniform(1.0, 1.8)
                + Vec3(0, 0, self.rng.uniform(2.4, 3.7)),
                lifetime=self.rng.uniform(0.65, 0.95),
            )

    def _spawn_hit_piece(
        self,
        name: str,
        size: Tuple[float, float, float],
        color: Tuple[float, float, float, float],
        pos: Vec3,
        velocity: Vec3,
        lifetime: float,
    ):
        piece = make_box(
            self.render,
            name,
            size,
            color,
            (pos.getX(), pos.getY(), pos.getZ()),
            (
                self.rng.uniform(0, 360),
                self.rng.uniform(0, 360),
                self.rng.uniform(0, 360),
            ),
        )
        self.hit_effects.append(
            HitEffect(
                node=piece,
                velocity=velocity,
                lifetime=lifetime,
                max_lifetime=lifetime,
                spin_rate=Vec3(
                    self.rng.uniform(-520, 520),
                    self.rng.uniform(-520, 520),
                    self.rng.uniform(-520, 520),
                ),
            )
        )

    def _update_ranged_shots(self, dt: float):
        live_shots = []
        for shot in self.ranged_shots:
            shot.lifetime -= dt
            if shot.lifetime <= 0.0:
                impact_pos = shot.impact_pos
                impact_color = shot.impact_color
                shot.node.removeNode()
                for index in range(3):
                    self._spawn_hit_piece(
                        name=f"ranged-impact-{index}",
                        size=(0.08, 0.08, 0.08),
                        color=impact_color,
                        pos=impact_pos,
                        velocity=Vec3(
                            self.rng.uniform(-1.2, 1.2),
                            self.rng.uniform(-1.2, 1.2),
                            self.rng.uniform(1.4, 2.4),
                        ),
                        lifetime=self.rng.uniform(0.28, 0.42),
                    )
                continue

            shot.node.setPos(shot.node.getPos() + shot.velocity * dt)
            hpr = shot.node.getHpr()
            shot.node.setHpr(
                hpr.getX() + shot.spin_rate.getX() * dt,
                hpr.getY() + shot.spin_rate.getY() * dt,
                hpr.getZ() + shot.spin_rate.getZ() * dt,
            )
            fade = max(0.0, min(1.0, shot.lifetime / shot.max_lifetime))
            shot.node.setColorScale(1, 1, 1, fade)
            live_shots.append(shot)

        self.ranged_shots = live_shots

    def _update_hit_effects(self, dt: float):
        live_effects = []
        for effect in self.hit_effects:
            effect.lifetime -= dt
            if effect.lifetime <= 0.0:
                effect.node.removeNode()
                continue

            pos = effect.node.getPos() + effect.velocity * dt
            effect.velocity.setZ(effect.velocity.getZ() - 6.5 * dt)

            if pos.getZ() <= 0.04:
                pos.setZ(0.04)
                effect.velocity.setX(effect.velocity.getX() * 0.35)
                effect.velocity.setY(effect.velocity.getY() * 0.35)
                effect.velocity.setZ(abs(effect.velocity.getZ()) * 0.12)

            effect.node.setPos(pos)
            hpr = effect.node.getHpr()
            effect.node.setHpr(
                hpr.getX() + effect.spin_rate.getX() * dt,
                hpr.getY() + effect.spin_rate.getY() * dt,
                hpr.getZ() + effect.spin_rate.getZ() * dt,
            )
            fade = max(0.0, min(1.0, effect.lifetime / effect.max_lifetime))
            effect.node.setColorScale(1, 1, 1, fade)
            live_effects.append(effect)

        self.hit_effects = live_effects

    def reset_arena(self, auto_respawn: bool = False):
        for enemy in self.enemies:
            enemy.node.removeNode()
        self.enemies.clear()
        self.attack_token_holder = None
        self.attack_token_cooldown = 0.0
        for effect in self.hit_effects:
            effect.node.removeNode()
        self.hit_effects.clear()
        for shot in self.ranged_shots:
            shot.node.removeNode()
        self.ranged_shots.clear()
        self.player_hp = self.player_max_hp
        self.hp_regen_cooldown = 0.0
        self.hp_regen_timer = 0.0
        self.player_stamina = self.player_max_stamina
        self.stamina_regen_cooldown = 0.0
        self.player.setPos(0, 3.0, 0)
        self.player.setHpr(0, 0, 0)
        self.player.setColorScale(1, 1, 1, 1)
        if self.pet is not None:
            self.pet.setPos(-0.9, 2.15, 0)
            self.pet.setHpr(0, 0, 0)
            self.pet_attack_cooldown = 0.0
        self.death_timer = 0.0
        self.is_death_sequence = False
        self.attack_cooldown = 0.35
        self.weapon_ability_cooldown = 0.0
        self.mob_respawn_timer = MOB_RESPAWN_INTERVAL
        self.is_player_moving = False
        if self.left_arm:
            self.left_arm.setHpr(8, -9, -8)
        if self.right_arm:
            self.right_arm.setHpr(-10, -12, 8)
        if self.weapon_pivot:
            self.weapon_pivot.setHpr(4, 18, -8)
        if self.left_leg:
            self.left_leg.setHpr(0, 0, 0)
        if self.right_leg:
            self.right_leg.setHpr(0, 0, 0)
        self._set_imported_player_pose()
        self.spawn_rabbits(4)
        self._spawn_field_mobs()
        self._respawn_chest_guards()
        if auto_respawn:
            self._set_catch_banner("Back on your feet!")
            self._log("You wake up at the dock with fresh courage.")
        else:
            self._log("The arena is reset.")

    def _respawn_chest_guards(self):
        for index, chest in enumerate(self.chests):
            if not chest.opened:
                self._spawn_chest_guards(
                    index, chest.pos, chest.guard_kind, bounds=chest.guard_bounds
                )

    def _random_arena_position(self) -> Vec3:
        return Vec3(
            self.rng.uniform(ARENA_MIN_X + 1.6, ARENA_MAX_X - 1.6),
            self.rng.uniform(ARENA_MIN_Y + 0.8, ARENA_MAX_Y - 1.2),
            0,
        )

    def spawn_rabbits(self, count: int = 3):
        for index in range(count):
            self.enemies.append(self._make_rabbit(index + 1, self._random_arena_position()))
        self._log(f"{count} white rabbits skitter into the arena.")

    def spawn_monster(self):
        x = self.rng.uniform(-5.0, 5.0)
        y = self.rng.uniform(-12.0, -6.0)
        self.enemies.append(self._make_monster(Vec3(x, y, 0)))
        self._log("Something larger drags itself out of the reeds.")

    def _make_rabbit(self, number: int, pos: Vec3) -> SceneEnemy:
        root = self.render.attachNewNode(f"rabbit-{number}")
        make_box(root, "rabbit-shadow", (0.78, 0.42, 0.03), (0.02, 0.025, 0.02, 0.25), (0, 0.04, 0.035))
        visual = root.attachNewNode("rabbit-visual")
        body = make_ellipsoid(visual, "rabbit-body", (0.43, 0.29, 0.22), (0.96, 0.96, 0.92, 1), (0, 0, 0.31), segments=12, rings=6)
        tail = visual.attachNewNode("rabbit-tail-pivot")
        tail.setPos(0, -0.28, 0.34)
        make_ellipsoid(tail, "rabbit-tail", (0.12, 0.1, 0.1), (1.0, 0.98, 0.96, 1), segments=8, rings=4)
        left_foot = visual.attachNewNode("rabbit-left-foot-pivot")
        left_foot.setPos(-0.2, 0.06, 0.12)
        make_ellipsoid(left_foot, "rabbit-left-foot", (0.11, 0.18, 0.045), (0.94, 0.92, 0.88, 1), segments=8, rings=4)
        right_foot = visual.attachNewNode("rabbit-right-foot-pivot")
        right_foot.setPos(0.2, 0.06, 0.12)
        make_ellipsoid(right_foot, "rabbit-right-foot", (0.11, 0.18, 0.045), (0.94, 0.92, 0.88, 1), segments=8, rings=4)
        head = visual.attachNewNode("rabbit-head-pivot")
        head.setPos(0, 0.38, 0.55)
        make_ellipsoid(head, "rabbit-head", (0.25, 0.24, 0.23), (1.0, 1.0, 0.98, 1), segments=10, rings=5)
        left_ear = make_ellipsoid(head, "rabbit-ear-left", (0.055, 0.045, 0.34), (1.0, 0.93, 0.93, 1), (-0.14, 0.04, 0.37), segments=7, rings=4)
        right_ear = make_ellipsoid(head, "rabbit-ear-right", (0.055, 0.045, 0.34), (1.0, 0.93, 0.93, 1), (0.14, 0.04, 0.37), segments=7, rings=4)
        make_box(head, "rabbit-eye-left", (0.08, 0.04, 0.08), (0.95, 0.08, 0.08, 1), (-0.1, 0.23, 0.02))
        make_box(head, "rabbit-eye-right", (0.08, 0.04, 0.08), (0.95, 0.08, 0.08, 1), (0.1, 0.23, 0.02))
        root.setPos(pos)
        return SceneEnemy(
            name="Rabid White Rabbit",
            kind="rabbit",
            hp=20,
            max_hp=20,
            node=root,
            speed=2.4,
            contact_damage=2,
            visual_node=visual,
            body_node=body,
            head_node=head,
            left_detail_node=left_ear,
            right_detail_node=right_ear,
            left_foot_node=left_foot,
            right_foot_node=right_foot,
            tail_node=tail,
            animation_phase=self.rng.uniform(0.0, math.pi * 2.0),
            home_pos=Vec3(pos),
        )

    def _make_monster(self, pos: Vec3) -> SceneEnemy:
        root = self.render.attachNewNode("mire-grub")
        make_box(root, "monster-shadow", (1.85, 1.25, 0.035), (0.02, 0.025, 0.02, 0.32), (0, 0.25, 0.035))
        visual = root.attachNewNode("monster-visual")
        body = make_ellipsoid(visual, "monster-body", (0.95, 0.68, 0.52), (0.22, 0.38, 0.24, 1), (0, 0, 0.48), segments=12, rings=6)
        make_box(visual, "monster-belly-plate", (1.15, 0.12, 0.12), (0.14, 0.26, 0.15, 1), (0, -0.18, 0.43), (0, 0, 0))
        left_fin = visual.attachNewNode("monster-left-fin-pivot")
        left_fin.setPos(-0.76, 0.05, 0.38)
        make_ellipsoid(left_fin, "monster-left-fin", (0.18, 0.31, 0.065), (0.18, 0.32, 0.2, 1), hpr=(0, 0, -18), segments=7, rings=4)
        right_fin = visual.attachNewNode("monster-right-fin-pivot")
        right_fin.setPos(0.76, 0.05, 0.38)
        make_ellipsoid(right_fin, "monster-right-fin", (0.18, 0.31, 0.065), (0.18, 0.32, 0.2, 1), hpr=(0, 0, 18), segments=7, rings=4)
        tail = visual.attachNewNode("monster-tail-pivot")
        tail.setPos(0, -0.74, 0.42)
        make_ellipsoid(tail, "monster-tail", (0.42, 0.28, 0.22), (0.18, 0.32, 0.2, 1), hpr=(0, 0, 0), segments=8, rings=4)
        head = visual.attachNewNode("monster-head-pivot")
        head.setPos(0, 0.78, 0.66)
        make_ellipsoid(head, "monster-head", (0.58, 0.44, 0.42), (0.26, 0.46, 0.27, 1), segments=10, rings=5)
        make_box(head, "monster-eye-left", (0.14, 0.08, 0.14), (0.9, 0.9, 0.3, 1), (-0.22, 0.4, 0.06))
        make_box(head, "monster-eye-right", (0.14, 0.08, 0.14), (0.9, 0.9, 0.3, 1), (0.22, 0.4, 0.06))
        left_feeler = make_cylinder(
            head,
            "monster-left-feeler",
            (0.035, 0.03),
            0.62,
            (0.16, 0.3, 0.17, 1),
            (-0.32, 0.18, 0.32),
            (-24, 34, -14),
            segments=7,
        )
        right_feeler = make_cylinder(
            head,
            "monster-right-feeler",
            (0.035, 0.03),
            0.62,
            (0.16, 0.3, 0.17, 1),
            (0.32, 0.18, 0.32),
            (24, 34, 14),
            segments=7,
        )
        root.setPos(pos)
        return SceneEnemy(
            name="Mire Grub",
            kind="monster",
            hp=48,
            max_hp=48,
            node=root,
            speed=1.2,
            contact_damage=6,
            visual_node=visual,
            body_node=body,
            head_node=head,
            left_detail_node=left_feeler,
            right_detail_node=right_feeler,
            left_foot_node=left_fin,
            right_foot_node=right_fin,
            tail_node=tail,
            animation_phase=self.rng.uniform(0.0, math.pi * 2.0),
            home_pos=Vec3(pos),
        )

    def _make_bird(self, number: int, pos: Vec3) -> SceneEnemy:
        root = self.render.attachNewNode(f"gull-{number}")
        visual = root.attachNewNode("gull-visual")
        body = make_ellipsoid(visual, "gull-body", (0.26, 0.42, 0.22), (0.9, 0.9, 0.94, 1), (0, 0, 0), segments=10, rings=5)
        head = visual.attachNewNode("gull-head-pivot")
        head.setPos(0, 0.4, 0.12)
        make_ellipsoid(head, "gull-head", (0.17, 0.18, 0.17), (0.96, 0.96, 0.98, 1), segments=9, rings=5)
        make_box(head, "gull-beak", (0.08, 0.22, 0.07), (0.95, 0.7, 0.2, 1), (0, 0.22, 0.0))
        make_box(head, "gull-eye-left", (0.05, 0.04, 0.05), (0.1, 0.1, 0.1, 1), (-0.08, 0.13, 0.05))
        make_box(head, "gull-eye-right", (0.05, 0.04, 0.05), (0.1, 0.1, 0.1, 1), (0.08, 0.13, 0.05))
        left_wing = visual.attachNewNode("gull-left-wing-pivot")
        left_wing.setPos(-0.18, 0, 0.06)
        make_ellipsoid(left_wing, "gull-left-wing", (0.5, 0.34, 0.05), (0.82, 0.82, 0.88, 1), (-0.45, 0, 0), segments=8, rings=4)
        right_wing = visual.attachNewNode("gull-right-wing-pivot")
        right_wing.setPos(0.18, 0, 0.06)
        make_ellipsoid(right_wing, "gull-right-wing", (0.5, 0.34, 0.05), (0.82, 0.82, 0.88, 1), (0.45, 0, 0), segments=8, rings=4)
        tail = visual.attachNewNode("gull-tail-pivot")
        tail.setPos(0, -0.4, 0.05)
        make_ellipsoid(tail, "gull-tail", (0.16, 0.26, 0.05), (0.86, 0.86, 0.9, 1), (0, -0.12, 0), segments=8, rings=4)
        root.setPos(pos)
        root.setZ(1.8)
        return SceneEnemy(
            name="Carrion Gull",
            kind="bird",
            hp=18,
            max_hp=18,
            node=root,
            speed=3.4,
            contact_damage=4,
            visual_node=visual,
            body_node=body,
            head_node=head,
            left_detail_node=left_wing,
            right_detail_node=right_wing,
            tail_node=tail,
            animation_phase=self.rng.uniform(0.0, math.pi * 2.0),
            ai_state="circle",
            bounds=WORLD_FIELD_BOUNDS,
            home_pos=Vec3(pos),
        )

    def _make_boar(self, number: int, pos: Vec3) -> SceneEnemy:
        root = self.render.attachNewNode(f"boar-{number}")
        make_box(root, "boar-shadow", (1.5, 1.0, 0.03), (0.02, 0.025, 0.02, 0.3), (0, 0.0, 0.035))
        visual = root.attachNewNode("boar-visual")
        body = make_ellipsoid(visual, "boar-body", (0.55, 0.85, 0.5), (0.3, 0.22, 0.18, 1), (0, 0, 0.55), segments=12, rings=6)
        make_box(visual, "boar-back-ridge", (0.12, 1.0, 0.2), (0.18, 0.12, 0.1, 1), (0, 0, 0.95))
        head = visual.attachNewNode("boar-head-pivot")
        head.setPos(0, 0.78, 0.5)
        make_ellipsoid(head, "boar-head", (0.4, 0.42, 0.38), (0.34, 0.25, 0.2, 1), segments=10, rings=5)
        make_box(head, "boar-snout", (0.26, 0.3, 0.22), (0.4, 0.3, 0.26, 1), (0, 0.34, -0.05))
        make_box(head, "boar-eye-left", (0.07, 0.05, 0.07), (0.85, 0.2, 0.12, 1), (-0.18, 0.3, 0.12))
        make_box(head, "boar-eye-right", (0.07, 0.05, 0.07), (0.85, 0.2, 0.12, 1), (0.18, 0.3, 0.12))
        make_box(head, "boar-tusk-left", (0.05, 0.18, 0.05), (0.9, 0.88, 0.78, 1), (-0.14, 0.44, -0.12), (0, 40, 0))
        make_box(head, "boar-tusk-right", (0.05, 0.18, 0.05), (0.9, 0.88, 0.78, 1), (0.14, 0.44, -0.12), (0, -40, 0))
        make_box(head, "boar-ear-left", (0.12, 0.06, 0.16), (0.26, 0.18, 0.14, 1), (-0.26, 0.0, 0.34))
        make_box(head, "boar-ear-right", (0.12, 0.06, 0.16), (0.26, 0.18, 0.14, 1), (0.26, 0.0, 0.34))
        left_foot = visual.attachNewNode("boar-left-foot-pivot")
        left_foot.setPos(-0.32, 0.42, 0.28)
        make_box(left_foot, "boar-left-front-leg", (0.16, 0.16, 0.5), (0.2, 0.14, 0.11, 1), (0, 0, -0.25))
        right_foot = visual.attachNewNode("boar-right-foot-pivot")
        right_foot.setPos(0.32, 0.42, 0.28)
        make_box(right_foot, "boar-right-front-leg", (0.16, 0.16, 0.5), (0.2, 0.14, 0.11, 1), (0, 0, -0.25))
        make_box(visual, "boar-left-back-leg", (0.17, 0.17, 0.5), (0.2, 0.14, 0.11, 1), (-0.32, -0.5, 0.25))
        make_box(visual, "boar-right-back-leg", (0.17, 0.17, 0.5), (0.2, 0.14, 0.11, 1), (0.32, -0.5, 0.25))
        tail = visual.attachNewNode("boar-tail-pivot")
        tail.setPos(0, -0.82, 0.6)
        make_box(tail, "boar-tail", (0.05, 0.28, 0.05), (0.2, 0.14, 0.11, 1), (0, -0.1, 0), (40, 0, 0))
        root.setPos(pos)
        return SceneEnemy(
            name="Bramble Boar",
            kind="boar",
            hp=40,
            max_hp=40,
            node=root,
            speed=2.0,
            contact_damage=7,
            visual_node=visual,
            body_node=body,
            head_node=head,
            left_foot_node=left_foot,
            right_foot_node=right_foot,
            tail_node=tail,
            animation_phase=self.rng.uniform(0.0, math.pi * 2.0),
            ai_state="stalk",
            bounds=WORLD_FIELD_BOUNDS,
            home_pos=Vec3(pos),
        )

    def _make_snapper(self, number: int, pos: Vec3) -> SceneEnemy:
        root = self.render.attachNewNode(f"snapper-{number}")
        make_box(root, "snapper-shadow", (1.2, 0.95, 0.03), (0.02, 0.025, 0.02, 0.28), (0, 0, 0.035))
        visual = root.attachNewNode("snapper-visual")
        shell = make_ellipsoid(visual, "snapper-shell", (0.52, 0.68, 0.32), (0.16, 0.32, 0.22, 1), (0, 0, 0.46), segments=12, rings=6)
        make_box(visual, "snapper-shell-ridge", (0.12, 0.92, 0.12), (0.08, 0.18, 0.12, 1), (0, 0, 0.78))
        make_box(visual, "snapper-shell-band", (0.86, 0.08, 0.08), (0.08, 0.18, 0.12, 1), (0, 0.14, 0.72))
        head = visual.attachNewNode("snapper-head-pivot")
        head.setPos(0, 0.62, 0.4)
        make_ellipsoid(head, "snapper-head", (0.28, 0.26, 0.22), (0.24, 0.44, 0.28, 1), segments=10, rings=5)
        make_box(head, "snapper-jaw", (0.3, 0.16, 0.08), (0.16, 0.3, 0.18, 1), (0, 0.22, -0.08))
        make_box(head, "snapper-eye-left", (0.06, 0.04, 0.06), (1.0, 0.92, 0.28, 1), (-0.11, 0.19, 0.06))
        make_box(head, "snapper-eye-right", (0.06, 0.04, 0.06), (1.0, 0.92, 0.28, 1), (0.11, 0.19, 0.06))
        left_foot = visual.attachNewNode("snapper-left-foot-pivot")
        left_foot.setPos(-0.38, 0.2, 0.24)
        make_box(left_foot, "snapper-left-foot", (0.22, 0.26, 0.1), (0.18, 0.36, 0.22, 1), (0, 0, 0))
        right_foot = visual.attachNewNode("snapper-right-foot-pivot")
        right_foot.setPos(0.38, 0.2, 0.24)
        make_box(right_foot, "snapper-right-foot", (0.22, 0.26, 0.1), (0.18, 0.36, 0.22, 1), (0, 0, 0))
        tail = visual.attachNewNode("snapper-tail-pivot")
        tail.setPos(0, -0.62, 0.38)
        make_ellipsoid(tail, "snapper-tail", (0.16, 0.24, 0.08), (0.18, 0.36, 0.22, 1), (0, -0.1, 0), segments=7, rings=4)
        root.setPos(pos)
        return SceneEnemy(
            name="Moss Snapper",
            kind="snapper",
            hp=34,
            max_hp=34,
            node=root,
            speed=1.35,
            contact_damage=5,
            visual_node=visual,
            body_node=shell,
            head_node=head,
            left_foot_node=left_foot,
            right_foot_node=right_foot,
            tail_node=tail,
            animation_phase=self.rng.uniform(0.0, math.pi * 2.0),
            ai_state="stalk",
            bounds=WORLD_FIELD_BOUNDS,
            home_pos=Vec3(pos),
        )

    def _make_wisp(self, number: int, pos: Vec3) -> SceneEnemy:
        root = self.render.attachNewNode(f"wisp-{number}")
        make_box(root, "wisp-shadow", (0.8, 0.8, 0.03), (0.02, 0.025, 0.02, 0.18), (0, 0, 0.035))
        visual = root.attachNewNode("wisp-visual")
        glow = make_ellipsoid(visual, "wisp-glow", (0.3, 0.3, 0.42), (0.32, 0.86, 1.0, 0.72), (0, 0, 0.65), segments=10, rings=5)
        core = make_ellipsoid(visual, "wisp-core", (0.16, 0.16, 0.24), (0.82, 0.98, 1.0, 0.9), (0, 0, 0.65), segments=8, rings=4)
        ring_a = make_box(visual, "wisp-ring-a", (0.78, 0.05, 0.05), (0.54, 0.9, 1.0, 0.52), (0, 0, 0.65), (0, 0, 22))
        ring_b = make_box(visual, "wisp-ring-b", (0.05, 0.78, 0.05), (0.54, 0.9, 1.0, 0.52), (0, 0, 0.65), (0, 0, -22))
        tail = visual.attachNewNode("wisp-tail-pivot")
        tail.setPos(0, -0.18, 0.3)
        make_ellipsoid(tail, "wisp-tail", (0.12, 0.2, 0.28), (0.22, 0.68, 1.0, 0.46), (0, -0.06, 0), segments=7, rings=4)
        root.setPos(pos)
        root.setZ(1.15)
        return SceneEnemy(
            name="Lantern Wisp",
            kind="wisp",
            hp=20,
            max_hp=20,
            node=root,
            speed=2.7,
            contact_damage=5,
            visual_node=visual,
            body_node=core,
            left_detail_node=ring_a,
            right_detail_node=ring_b,
            tail_node=tail,
            animation_phase=self.rng.uniform(0.0, math.pi * 2.0),
            ai_state="hover",
            bounds=WORLD_FIELD_BOUNDS,
            home_pos=Vec3(pos),
        )

    def _make_boss(self) -> SceneEnemy:
        pos = Vec3(BOSS_ARENA_CENTER.getX(), BOSS_ARENA_CENTER.getY(), 0)
        root = self.render.attachNewNode("boss")
        make_box(root, "boss-shadow", (2.0, 1.4, 0.03), (0.02, 0.025, 0.02, 0.3), (0, 0, 0.035))
        visual = root.attachNewNode("boss-visual")
        crown_gold = (0.85, 0.72, 0.22, 1)
        cape_color = (0.55, 0.08, 0.12, 1)
        armor_color = (0.28, 0.26, 0.24, 1)
        skin_color = (0.62, 0.48, 0.38, 1)

        body = make_box(visual, "boss-body", (0.9, 0.6, 1.4), armor_color, (0, 0, 1.1))
        make_box(visual, "boss-cape", (1.0, 0.2, 1.5), cape_color, (0, -0.35, 1.15))
        make_box(visual, "boss-belt", (0.95, 0.65, 0.15), (0.42, 0.28, 0.12, 1), (0, 0, 0.5))
        head = visual.attachNewNode("boss-head-pivot")
        head.setPos(0, 0, 2.0)
        make_box(head, "boss-head", (0.5, 0.45, 0.55), skin_color)
        make_box(head, "boss-crown", (0.6, 0.5, 0.22), crown_gold, (0, 0, 0.35))
        make_box(head, "boss-crown-point-l", (0.08, 0.08, 0.2), crown_gold, (-0.2, 0, 0.52))
        make_box(head, "boss-crown-point-r", (0.08, 0.08, 0.2), crown_gold, (0.2, 0, 0.52))
        make_box(head, "boss-crown-point-c", (0.08, 0.08, 0.25), crown_gold, (0, 0, 0.55))
        make_box(head, "boss-eye-left", (0.1, 0.06, 0.1), (0.85, 0.15, 0.1, 1), (-0.14, -0.24, 0.05))
        make_box(head, "boss-eye-right", (0.1, 0.06, 0.1), (0.85, 0.15, 0.1, 1), (0.14, -0.24, 0.05))
        make_box(head, "boss-beard", (0.32, 0.12, 0.28), (0.4, 0.35, 0.3, 1), (0, -0.22, -0.28))

        left_arm = visual.attachNewNode("boss-left-arm-pivot")
        left_arm.setPos(-0.6, 0, 1.65)
        make_box(left_arm, "boss-left-arm", (0.25, 0.25, 0.75), armor_color, (0, 0, -0.38))
        make_box(left_arm, "boss-left-gauntlet", (0.28, 0.28, 0.2), (0.35, 0.32, 0.28, 1), (0, 0, -0.78))

        right_arm = visual.attachNewNode("boss-right-arm-pivot")
        right_arm.setPos(0.6, 0, 1.65)
        make_box(right_arm, "boss-right-arm", (0.25, 0.25, 0.75), armor_color, (0, 0, -0.38))
        make_box(right_arm, "boss-sword-hilt", (0.12, 0.12, 0.28), (0.42, 0.28, 0.12, 1), (0, 0, -0.92))
        make_box(right_arm, "boss-sword-blade", (0.08, 0.16, 1.15), (0.65, 0.62, 0.58, 1), (0, 0, -1.55))
        make_box(right_arm, "boss-sword-guard", (0.28, 0.06, 0.06), (0.42, 0.28, 0.12, 1), (0, 0, -0.78))

        make_box(visual, "boss-left-leg", (0.3, 0.3, 0.75), armor_color, (-0.22, 0, 0.0))
        make_box(visual, "boss-right-leg", (0.3, 0.3, 0.75), armor_color, (0.22, 0, 0.0))
        make_box(visual, "boss-left-boot", (0.35, 0.4, 0.18), (0.2, 0.16, 0.12, 1), (-0.22, 0.05, -0.35))
        make_box(visual, "boss-right-boot", (0.35, 0.4, 0.18), (0.2, 0.16, 0.12, 1), (0.22, 0.05, -0.35))

        root.setPos(pos)
        root.setScale(1.35)
        enemy = SceneEnemy(
            name="The Old King",
            kind="boss",
            hp=135,
            max_hp=135,
            node=root,
            speed=1.8,
            contact_damage=9,
            visual_node=visual,
            body_node=body,
            head_node=head,
            left_detail_node=left_arm,
            right_detail_node=right_arm,
            animation_phase=0.0,
            ai_state="stalk",
            home_pos=Vec3(pos),
        )
        return enemy

    def _random_field_position(self) -> Vec3:
        """Pick a spot out in the open field, away from the central hub."""

        for _ in range(40):
            x = self.rng.uniform(-WORLD_LIMIT + 6.0, WORLD_LIMIT - 6.0)
            y = self.rng.uniform(-WORLD_LIMIT + 6.0, WORLD_LIMIT - 6.0)
            pos = Vec3(x, y, 0)
            if (pos - self.player.getPos()).length() < 12.0:
                continue
            if -32.0 < x < 36.0 and -40.0 < y < 22.0:
                continue
            if self._is_water_position(pos):
                continue
            return pos
        return Vec3(WORLD_LIMIT - 8.0, -(WORLD_LIMIT - 8.0), 0)

    def spawn_birds(self, count: int = 3):
        for index in range(count):
            self.enemies.append(self._make_bird(index + 1, self._random_field_position()))
        self._log(f"{count} carrion gulls wheel overhead.")

    def spawn_boars(self, count: int = 2):
        for index in range(count):
            self.enemies.append(self._make_boar(index + 1, self._random_field_position()))
        self._log(f"{count} bramble boars root through the far field.")

    def spawn_snappers(self, count: int = 2):
        for index in range(count):
            self.enemies.append(self._make_snapper(index + 1, self._random_field_position()))
        self._log(f"{count} moss snappers crawl from the wet brush.")

    def spawn_wisps(self, count: int = 2):
        for index in range(count):
            self.enemies.append(self._make_wisp(index + 1, self._random_field_position()))
        self._log(f"{count} lantern wisps flicker between the trees.")

    def _spawn_field_mobs(self):
        self.spawn_birds(5)
        self.spawn_boars(4)
        self.spawn_snappers(3)
        self.spawn_wisps(3)

    def _enemies_in_attack_range(self) -> List[SceneEnemy]:
        player_pos = self.player.getPos()
        attack_range = ATTACK_RANGE
        is_ranged = self.current_weapon is not None and is_ranged_weapon(self.current_weapon)
        if is_ranged:
            attack_range = RANGED_ATTACK_RANGE
            heading = math.radians(self.player.getH())
            forward = Vec3(-math.sin(heading), math.cos(heading), 0)
        nearby: List[Tuple[float, SceneEnemy]] = []
        for enemy in self.enemies:
            to_enemy = enemy.node.getPos() - player_pos
            to_enemy.setZ(0)
            distance = to_enemy.length()
            if is_ranged and distance > 0.01:
                aim = Vec3(to_enemy)
                aim.normalize()
                if forward.dot(aim) < RANGED_ATTACK_CONE_DOT:
                    continue
            if distance <= attack_range:
                nearby.append((distance, enemy))

        nearby.sort(key=lambda item: item[0])
        enemies = [enemy for _distance, enemy in nearby]
        if is_ranged:
            return enemies[:1]
        return enemies

    def _nearest_enemy_in_range(self) -> Optional[SceneEnemy]:
        targets = self._enemies_in_attack_range()
        return targets[0] if targets else None

    def _update_ui(self):
        rod = fishing_rod_for_tier(self.rod_tier)
        armor_name = "None"
        if self.player_armor_tier >= 0:
            armor_name = armor_tier_for_index(self.player_armor_tier).name
        self._update_resource_bars()
        self.status_text.setText(
            f"Gold {self.gold}\n"
            f"Rod {rod.name}\n"
            f"Armor {armor_name}\n"
            f"Enemies nearby {len(self.enemies)}"
        )

        if self.current_weapon is None:
            weapon_lines = "Weapon: none\nTraits: none discovered"
        else:
            ability_ready = (
                "Q ready"
                if self.weapon_ability_cooldown <= 0.0
                else f"Q {self.weapon_ability_cooldown:.1f}s"
            )
            weapon_lines = (
                f"Weapon: {self.current_weapon.name}\n"
                f"Type: {self.current_weapon.weapon_type}  "
                f"Rarity: {self.current_weapon.rarity}  "
                f"Damage: {self.current_weapon.base_damage}\n"
                f"Ability: {ability_summary(self.current_weapon)}\n"
                f"Active: {ability_ready}\n"
                f"Traits: {trait_summary(self.current_weapon)}"
            )
        self.weapon_text.setText(weapon_lines)

        spot_name, _spot_pos, distance_to_water = self._nearest_fishing_spot()
        distance_to_shop = self._distance_to_shop()
        distance_to_forge = self._distance_to_forge()
        distance_to_raft = self._distance_to_nearest_raft()
        nearby_chest = self._nearest_chest()
        if self.fishing_state == "casting":
            prompt = "Casting..."
        elif self.fishing_state == "waiting":
            prompt = "Watch the bobber."
        elif self.fishing_state == "bite":
            prompt = "Bite! Press E now!"
        elif self.fishing_state == "reeling":
            prompt = "Reeling in..."
        elif self.player_hp <= 0:
            prompt = "You are down. Auto-respawning..."
        elif nearby_chest is not None:
            guard_count = len(self._living_guards_for_chest(nearby_chest))
            if guard_count:
                prompt = f"Defeat {guard_count} guard(s) to open this chest."
            else:
                prompt = "Press E to open the chest."
        elif distance_to_shop <= SHOP_RANGE:
            prompt = self._shop_prompt()
        elif distance_to_forge <= FORGE_RANGE:
            prompt = self._forge_prompt()
        elif distance_to_raft <= SHOP_RANGE:
            if (self.player.getPos() - LEVEL2_RAFT_SPOT).length() <= SHOP_RANGE:
                prompt = "Press E to raft back to the old lake."
            else:
                prompt = "Press E to raft to the level 2 zone."
        elif distance_to_water <= FISHING_RANGE:
            if spot_name == "cave pool":
                prompt = "Press E to cast into the glowing cave pool."
            elif spot_name == "level 2 lake":
                prompt = "Press E to cast into the level 2 lake."
            else:
                prompt = "Press E to cast into the lake."
        elif self.enemies:
            prompt = "Explore the cave, frost marsh, sunken meadow, or take the raft to level 2."
        else:
            prompt = "The arena is quiet. The raft and distant chests wait."
        self.prompt_text.setText(prompt)

        if self.catch_banner_timer > 0.0:
            self.catch_text.setText(self.catch_banner_text)
        else:
            self.catch_text.setText("")

        self._update_inspection_ui()
        self._update_shop_ui()
        self._update_forge_ui()
        self.log_text.setText("\n".join(self.log_lines[-7:]))

    def _update_resource_bars(self):
        if self.health_bar_fill is None:
            return

        health_ratio = 0.0
        if self.player_max_hp > 0:
            health_ratio = max(0.0, min(1.0, self.player_hp / self.player_max_hp))

        left = 0.345
        right = left + (0.89 * health_ratio)
        if health_ratio <= 0.0:
            right = left
        self.health_bar_fill["frameSize"] = (left, right, 0.89, 0.935)
        self.health_bar_fill["frameColor"] = (0.9, 0.16, 0.13, 0.92)

        if self.stamina_bar_fill is None:
            return
        stamina_ratio = 0.0
        if self.player_max_stamina > 0:
            stamina_ratio = max(0.0, min(1.0, self.player_stamina / self.player_max_stamina))
        stamina_left = 0.345
        stamina_right = stamina_left + (0.89 * stamina_ratio)
        if stamina_ratio <= 0.0:
            stamina_right = stamina_left
        self.stamina_bar_fill["frameSize"] = (stamina_left, stamina_right, 0.8, 0.845)
        self.stamina_bar_fill["frameColor"] = (0.22, 0.82, 0.28, 0.92)

    def _shop_prompt(self) -> str:
        if self.shop_open:
            return "Press 1-4 to choose a rod, or E to close."
        return "Press E to open the rod shop."

    def _forge_prompt(self) -> str:
        if self.forge_open:
            return "Press 1-7 to choose armor, or E to close."
        return "Press E to open the forge."

    def _update_shop_ui(self):
        if self.shop_frame is None:
            return

        if not self.shop_open:
            self.shop_frame.hide()
            return

        self.shop_frame.show()
        self.shop_title.setText("Rod Shop")
        self.shop_body.setText(self._format_shop_menu())

    def _format_shop_menu(self) -> str:
        lines = [f"Gold: {self.gold}", ""]
        for index, rod in enumerate(FISHING_RODS, start=1):
            if rod.tier == self.rod_tier:
                state = "owned"
            elif rod.tier < self.rod_tier:
                state = "older"
            elif self.gold >= rod.price:
                state = "ready"
            else:
                state = f"need {rod.price - self.gold}"
            lines.append(f"{index}. {rod.name}")
            lines.append(f"   {rod.price} gold - {state}")
        lines.extend(("", "Press a number to buy."))
        return "\n".join(lines)

    def _update_forge_ui(self):
        if self.forge_frame is None:
            return

        if not self.forge_open:
            self.forge_frame.hide()
            return

        self.forge_frame.show()
        self.forge_title.setText("Armor Forge")
        self.forge_body.setText(self._format_forge_menu())

    def _format_forge_menu(self) -> str:
        current = "none"
        if self.player_armor_tier >= 0:
            current = armor_tier_for_index(self.player_armor_tier).name
        lines = [f"Gold: {self.gold}", f"Current: {current}", ""]
        for index, armor in enumerate(ARMOR_TIERS, start=1):
            tier = index - 1
            if tier <= self.player_armor_tier:
                state = "owned"
            elif self.gold >= armor.cost:
                state = "ready"
            else:
                state = f"need {armor.cost - self.gold}"
            lines.append(f"{index}. {armor.name}")
            lines.append(f"   {armor.cost} gold - blocks {armor.armor_value} - {state}")
        lines.extend(("", "Press a number to buy."))
        return "\n".join(lines)

    def _update_inspection_ui(self):
        if self.inspect_frame is None:
            return

        if not self.inspect_open or self.current_weapon is None:
            self.inspect_frame.hide()
            self._clear_inspection_preview()
            return

        weapon = self.current_weapon
        self.inspect_frame.show()
        if self.inspect_preview_weapon is not weapon:
            self._rebuild_inspection_preview(weapon)
        if self.inspect_preview_root is not None:
            spin = (self.fishing_phase * 24.0) % 360.0
            self.inspect_preview_root.setHpr(-28 + spin, 0, -34)
        self.inspect_title.setText("Recovered Relic")
        self.inspect_body.setText(self._format_weapon_inspection(weapon))

    def _clear_inspection_preview(self):
        if self.inspect_preview_model is not None:
            self.inspect_preview_model.removeNode()
            self.inspect_preview_model = None
        self.inspect_preview_weapon = None

    def _rebuild_inspection_preview(self, weapon: Weapon):
        if self.inspect_preview_root is None:
            return

        self._clear_inspection_preview()
        self.inspect_preview_model = self.inspect_preview_root.attachNewNode(
            "inspection-weapon-model"
        )
        self._populate_weapon_model(self.inspect_preview_model, weapon, preview=True)
        self.inspect_preview_weapon = weapon

    def _format_weapon_inspection(self, weapon: Weapon) -> str:
        lines = [
            weapon.name,
            "",
            f"Form: {weapon.weapon_type.title()}",
            f"Rarity: {weapon.rarity.title()}",
            f"Base damage: {weapon.base_damage}",
            "",
            "Signature:",
        ]

        for wrapped_line in textwrap.wrap(self._weapon_signature(weapon), width=34):
            lines.append(f"  {wrapped_line}")

        ability = weapon_ability(weapon)
        lines.extend(["", "Ability:"])
        if ability.key in weapon.discovered:
            lines.append(f"  {ability.display_name}")
            for wrapped_line in textwrap.wrap(ability.description, width=32):
                lines.append(f"  {wrapped_line}")
        else:
            lines.append("  ???")
            lines.append("  Try the weapon in combat.")

        lines.extend(
            [
                "",
                "Traits:",
            ]
        )

        for index, enchantment in enumerate(weapon.enchantments, start=1):
            if enchantment.key in weapon.discovered:
                lines.append(f"{index}. {enchantment.display_name}")
                for wrapped_line in textwrap.wrap(enchantment.description, width=32):
                    lines.append(f"   {wrapped_line}")
            else:
                lines.append(f"{index}. ???")
                lines.append("   Not understood yet.")

        return "\n".join(lines)

    def _weapon_signature(self, weapon: Weapon) -> str:
        signatures = {
            "saber": "A moon-bright dueling blade with a crescent flash along its edge.",
            "falchion": "A heavy curved cutter whose bright spine makes every swing feel dangerous.",
            "axe": "A brutal rune-marked axe built to land with a loud, final thunk.",
            "mace": "A spiked relic with a floating halo around its head, like it remembers old gravity.",
            "rapier": "A needle-thin noble weapon with a star-glint at the point.",
            "spear": "A lake-spear with a tiny battle banner tied below the ancient tip.",
            "cleaver": "A broad chopping blade with a dark notch and a hungry old rune.",
            "staff": "A crooked mage staff with a bright lake-star trapped above the prongs.",
            "bow": "A curved old war bow with a glowing string and a patient arrow.",
            "crossbow": "A compact relic crossbow built around one heavy rune-bolt.",
        }

        return signatures.get(
            weapon.weapon_type,
            "An old weapon pulled from the lake, still deciding what it wants to be.",
        )

    def _log(self, message: str):
        self.log_lines.append(message)
        self.log_lines = self.log_lines[-9:]


def main():
    game = SwordfishGame()
    game.run()


if __name__ == "__main__":
    main()
