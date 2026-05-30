"""Panda3D vertical slice for Swordfish."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
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

from .combat import EnemyState, gold_reward_for_enemy, resolve_attack
from .weapons import (
    Weapon,
    discover_traits,
    fishing_rod_for_tier,
    generate_weapon,
    next_fishing_rod,
    trait_summary,
)


WORLD_LIMIT = 18.0
PLAYER_SPEED = 7.0
ATTACK_RANGE = 2.6
FISHING_RANGE = 4.5
SHOP_RANGE = 3.0
SHOP_SPOT = Vec3(-10.4, 1.7, 0)
ARENA_MIN_X = -8.2
ARENA_MAX_X = 8.2
ARENA_MIN_Y = -13.2
ARENA_MAX_Y = -4.6
WATER_BLOBS = (
    (0.0, 9.7, 12.2, 6.3),
    (-8.2, 9.5, 4.3, 3.7),
    (8.4, 10.2, 4.0, 3.3),
)
DOCK_SAFE_ZONE = (-1.9, 1.9, 2.4, 6.9)
DEFAULT_WEAPON_COLOR = (0.74, 0.78, 0.78, 1)
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


@dataclass
class HitEffect:
    node: object
    velocity: Vec3
    lifetime: float
    max_lifetime: float
    spin_rate: Vec3


@dataclass
class AnimatedDetail:
    node: object
    base_pos: Vec3
    phase: float
    speed: float
    bob_amount: float
    sway_amount: float
    color: Tuple[float, float, float, float]


def make_box(
    parent,
    name: str,
    size: Tuple[float, float, float],
    color: Tuple[float, float, float, float],
    pos: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    hpr: Tuple[float, float, float] = (0.0, 0.0, 0.0),
):
    """Create a simple colored box without relying on external art files."""

    vertices = (
        (-0.5, -0.5, -0.5),
        (0.5, -0.5, -0.5),
        (0.5, 0.5, -0.5),
        (-0.5, 0.5, -0.5),
        (-0.5, -0.5, 0.5),
        (0.5, -0.5, 0.5),
        (0.5, 0.5, 0.5),
        (-0.5, 0.5, 0.5),
    )
    triangles = (
        (0, 1, 2),
        (0, 2, 3),
        (4, 6, 5),
        (4, 7, 6),
        (0, 4, 5),
        (0, 5, 1),
        (1, 5, 6),
        (1, 6, 2),
        (2, 6, 7),
        (2, 7, 3),
        (3, 7, 4),
        (3, 4, 0),
    )

    vdata = GeomVertexData(name, GeomVertexFormat.getV3(), Geom.UHStatic)
    vertex_writer = GeomVertexWriter(vdata, "vertex")
    for vertex in vertices:
        vertex_writer.addData3(*vertex)

    primitive = GeomTriangles(Geom.UHStatic)
    for triangle in triangles:
        primitive.addVertices(*triangle)
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
    vdata = GeomVertexData(name, GeomVertexFormat.getV3(), Geom.UHStatic)
    vertex_writer = GeomVertexWriter(vdata, "vertex")
    vertex_writer.addData3(0, 0, 0)

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

    vdata = GeomVertexData(name, GeomVertexFormat.getV3(), Geom.UHStatic)
    vertex_writer = GeomVertexWriter(vdata, "vertex")
    vertex_writer.addData3(center_x, center_y, half_thickness)
    vertex_writer.addData3(center_x, center_y, -half_thickness)

    for x, y in points:
        vertex_writer.addData3(x, y, half_thickness)
    for x, y in points:
        vertex_writer.addData3(x, y, -half_thickness)

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
    return node_path


def weapon_glow_color(weapon: Optional[Weapon]) -> Tuple[float, float, float, float]:
    if weapon is None:
        return DEFAULT_WEAPON_COLOR

    for enchantment in weapon.enchantments:
        if enchantment.key in ENCHANTMENT_GLOW_COLORS:
            return ENCHANTMENT_GLOW_COLORS[enchantment.key]

    return DEFAULT_WEAPON_COLOR


def make_tree(parent, name: str, pos: Tuple[float, float, float], scale: float = 1.0):
    root = parent.attachNewNode(name)
    root.setPos(*pos)
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
        self.win.requestProperties(props)

        self.disableMouse()
        self.setBackgroundColor(0.1, 0.14, 0.17, 1)

        self.rng = random.Random()
        self.keys = {"w": False, "a": False, "s": False, "d": False}
        self.fishing_spot = Vec3(0, 7.0, 0)
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
        self.attack_cooldown = 0.0
        self.fish_count = 0
        self.enemies: List[SceneEnemy] = []
        self.hit_effects: List[HitEffect] = []
        self.animated_details: List[AnimatedDetail] = []
        self.log_lines: List[str] = []
        self.swing_time = 0.0
        self.swing_duration = 0.26
        self.right_arm = None
        self.weapon_pivot = None
        self.weapon_root = None
        self.slash_root = None
        self.slash_parts = []
        self.catch_banner_timer = 0.0
        self.catch_banner_text = ""
        self.inspect_open = False
        self.inspect_frame = None
        self.inspect_title = None
        self.inspect_body = None
        self.inspect_preview_root = None
        self.inspect_preview_model = None
        self.inspect_preview_weapon = None

        self._bind_controls()
        self._build_world()
        self._build_player()
        self._build_lights()
        self._build_ui()
        self.spawn_rabbits(4)
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
        self.accept("r", self.reset_arena)
        self.accept("m", self.spawn_monster)
        self.accept("escape", self.userExit)

    def _set_key(self, key: str, value: bool):
        self.keys[key] = value

    def _build_world(self):
        make_box(
            self.render,
            "ground",
            (42, 42, 0.1),
            (0.14, 0.29, 0.16, 1),
            (0, 0, -0.08),
        )
        self._build_ground_layers()
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
        make_box(
            self.render,
            "fishing-marker",
            (0.6, 0.6, 1.6),
            (0.72, 0.86, 1.0, 1),
            (0, 5.8, 0.75),
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
        self._build_world_details()

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
        for index in range(3):
            make_box(
                shop,
                f"counter-coin-{index}",
                (0.16, 0.16, 0.035),
                gold,
                (-0.35 + index * 0.18, -1.05, 0.75),
                (0, 0, self.rng.uniform(-20, 20)),
            )

    def _build_player(self):
        self.player = self.render.attachNewNode("player")
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
        make_box(
            self.player,
            "player-belt",
            (0.78, 0.54, 0.14),
            (0.18, 0.1, 0.06, 1),
            (0, 0.01, 0.58),
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
        make_box(
            self.player,
            "player-left-leg",
            (0.22, 0.24, 0.55),
            (0.12, 0.15, 0.18, 1),
            (-0.19, 0, 0.25),
        )
        make_box(
            self.player,
            "player-right-leg",
            (0.22, 0.24, 0.55),
            (0.12, 0.15, 0.18, 1),
            (0.19, 0, 0.25),
        )
        make_box(
            self.player,
            "player-left-boot",
            (0.28, 0.36, 0.16),
            (0.07, 0.05, 0.04, 1),
            (-0.19, 0.05, 0.02),
        )
        make_box(
            self.player,
            "player-right-boot",
            (0.28, 0.36, 0.16),
            (0.07, 0.05, 0.04, 1),
            (0.19, 0.05, 0.02),
        )
        make_box(
            self.player,
            "player-left-arm",
            (0.18, 0.2, 0.72),
            (0.1, 0.31, 0.39, 1),
            (-0.52, 0.02, 0.84),
            (0, 0, -10),
        )

        self.right_arm = self.player.attachNewNode("right-arm")
        self.right_arm.setPos(0.52, 0.02, 1.06)
        self.right_arm.setHpr(-16, -4, 12)
        make_box(
            self.right_arm,
            "right-sleeve",
            (0.18, 0.22, 0.62),
            (0.1, 0.31, 0.39, 1),
            (0, 0.18, -0.22),
            (0, 0, 14),
        )
        make_box(
            self.right_arm,
            "right-hand",
            (0.19, 0.18, 0.16),
            (0.9, 0.64, 0.44, 1),
            (0, 0.42, -0.54),
        )
        self.weapon_pivot = self.right_arm.attachNewNode("weapon-pivot")
        self.weapon_pivot.setPos(0, 0.52, -0.55)
        self.weapon_pivot.setHpr(0, 0, 0)
        self.weapon_root = self.weapon_pivot.attachNewNode("weapon-root")
        self._build_weapon_model(None)
        self._build_slash_trail()
        self.player.setPos(0, 3.0, 0)

        self.camera.setPos(0, -17, 14)
        self.camera.lookAt(self.player)

    def _build_weapon_model(self, weapon: Optional[Weapon]):
        if self.weapon_root is not None:
            self.weapon_root.removeNode()

        self.weapon_root = self.weapon_pivot.attachNewNode("weapon-root")
        self._populate_weapon_model(self.weapon_root, weapon, preview=False)

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

        make_box(parent, "grip", (0.13, 0.58, 0.13), leather, (0, 0.27, 0))

        if weapon_type in {"saber", "falchion"}:
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
                "slash-low",
                (0.1, 1.45, 0.05),
                (0.8, 0.95, 1.0, 0.2),
                (-0.36, 0.25, -0.08),
                (-38, 0, 0),
            ),
            make_box(
                self.slash_root,
                "slash-mid",
                (0.12, 1.75, 0.05),
                (0.85, 0.98, 1.0, 0.32),
                (0, 0.3, 0),
            ),
            make_box(
                self.slash_root,
                "slash-high",
                (0.1, 1.45, 0.05),
                (0.8, 0.95, 1.0, 0.2),
                (0.36, 0.25, 0.08),
                (38, 0, 0),
            ),
        ]
        self.slash_root.hide()

    def _start_swing(self):
        if self.right_arm is None or self.weapon_pivot is None:
            return

        self.swing_time = self.swing_duration
        color = weapon_glow_color(self.current_weapon)
        red, green, blue, alpha = color
        if self.current_weapon is None:
            red, green, blue, alpha = (0.85, 0.94, 1.0, 0.35)

        for index, part in enumerate(self.slash_parts):
            part_alpha = alpha * (0.7 + index * 0.18)
            part.setColor(red, green, blue, min(part_alpha, 0.72))

        if self.slash_root is not None:
            self.slash_root.show()

    def _update_swing(self, dt: float):
        if self.right_arm is None or self.weapon_pivot is None:
            return

        if self.swing_time <= 0.0:
            self.right_arm.setHpr(-16, -4, 12)
            self.weapon_pivot.setHpr(0, 0, 0)
            if self.slash_root is not None:
                self.slash_root.hide()
            return

        self.swing_time = max(0.0, self.swing_time - dt)
        progress = 1.0 - (self.swing_time / self.swing_duration)
        impact_curve = math.sin(progress * math.pi)
        arm_heading = 58 - 132 * progress
        arm_pitch = -8 - 18 * impact_curve
        arm_roll = 22 * impact_curve
        self.right_arm.setHpr(arm_heading, arm_pitch, arm_roll)
        self.weapon_pivot.setHpr(0, 0, -22 + 44 * progress)

        if self.slash_root is not None:
            self.slash_root.setScale(0.85 + impact_curve * 0.3)
            self.slash_root.setH(-20 + 40 * progress)

        if self.swing_time == 0.0:
            self.right_arm.setHpr(-16, -4, 12)
            self.weapon_pivot.setHpr(0, 0, 0)
            if self.slash_root is not None:
                self.slash_root.hide()

    def _build_lights(self):
        ambient = AmbientLight("soft-ambient")
        ambient.setColor((0.58, 0.62, 0.66, 1))
        self.render.setLight(self.render.attachNewNode(ambient))

        sun = DirectionalLight("low-sun")
        sun.setColor((0.96, 0.86, 0.65, 1))
        sun_path = self.render.attachNewNode(sun)
        sun_path.setHpr(-35, -55, 0)
        self.render.setLight(sun_path)

        fill = DirectionalLight("cool-fill")
        fill.setColor((0.24, 0.34, 0.46, 1))
        fill_path = self.render.attachNewNode(fill)
        fill_path.setHpr(130, -28, 0)
        self.render.setLight(fill_path)

    def _build_ui(self):
        self.status_frame = DirectFrame(
            frameColor=(0.025, 0.035, 0.032, 0.58),
            frameSize=(-1.36, -0.14, 0.67, 0.98),
            pos=(0, 0, 0),
        )
        self.weapon_frame = DirectFrame(
            frameColor=(0.025, 0.04, 0.05, 0.54),
            frameSize=(-1.36, -0.08, 0.47, 0.72),
            pos=(0, 0, 0),
        )
        self.prompt_frame = DirectFrame(
            frameColor=(0.04, 0.035, 0.025, 0.58),
            frameSize=(-0.72, 0.72, -0.92, -0.8),
            pos=(0, 0, 0),
        )
        self.log_frame = DirectFrame(
            frameColor=(0.025, 0.025, 0.028, 0.48),
            frameSize=(-1.36, -0.04, -0.92, -0.51),
            pos=(0, 0, 0),
        )
        self.status_text = OnscreenText(
            text="",
            pos=(-1.32, 0.92),
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
            pos=(-1.32, -0.55),
            scale=0.036,
            align=TextNode.ALeft,
            fg=(0.92, 0.92, 0.92, 1),
            mayChange=True,
        )
        self._build_inspection_ui()
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

    def _update(self, task):
        dt = min(globalClock.getDt(), 0.05)
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        self.catch_banner_timer = max(0.0, self.catch_banner_timer - dt)
        self.water_bump_cooldown = max(0.0, self.water_bump_cooldown - dt)
        self._move_player(dt)
        self._update_fishing(dt)
        self._update_world_details()
        self._update_enemies(dt)
        self._update_hit_effects(dt)
        self._update_swing(dt)
        self._update_camera()
        self._update_ui()
        return task.cont

    def _move_player(self, dt: float):
        if self.player_hp <= 0:
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

        movement = Vec3(move_x, move_y, 0)
        if movement.length() == 0:
            return

        movement.normalize()
        old_pos = self.player.getPos()
        new_pos = old_pos + movement * PLAYER_SPEED * dt
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

        heading = math.degrees(math.atan2(-movement.getX(), movement.getY()))
        self.player.setH(heading)

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

    def _update_enemies(self, dt: float):
        if self.player_hp <= 0:
            return

        player_pos = self.player.getPos()
        for enemy in self.enemies:
            enemy_pos = self._update_enemy_feedback(enemy, dt)
            if enemy.kind == "rabbit":
                self._update_rabbit(enemy, player_pos, enemy_pos, dt)
            else:
                self._update_monster(enemy, player_pos, enemy_pos, dt)

    def _update_enemy_feedback(self, enemy: SceneEnemy, dt: float) -> Vec3:
        enemy.attack_cooldown = max(0.0, enemy.attack_cooldown - dt)
        if enemy.flash_time > 0.0:
            enemy.flash_time = max(0.0, enemy.flash_time - dt)
            if enemy.flash_time == 0.0:
                enemy.node.setColorScale(1, 1, 1, 1)

        enemy_pos = enemy.node.getPos()
        if enemy.knockback_velocity.length() > 0.05:
            enemy_pos = enemy_pos + enemy.knockback_velocity * dt
            enemy_pos = self._clamp_to_arena(enemy_pos)
            enemy.node.setPos(enemy_pos)
            enemy.knockback_velocity = enemy.knockback_velocity * max(0.0, 1.0 - dt * 7.5)
        else:
            enemy_pos = self._clamp_to_arena(enemy_pos)
            enemy.node.setPos(enemy_pos)

        return enemy_pos

    def _update_monster(self, enemy: SceneEnemy, player_pos: Vec3, enemy_pos: Vec3, dt: float):
        to_player = player_pos - enemy_pos
        to_player.setZ(0)
        distance = to_player.length()

        if 0.05 < distance < 9.0:
            to_player.normalize()
            enemy.node.setH(math.degrees(math.atan2(-to_player.getX(), to_player.getY())))
            enemy_pos = self._clamp_to_arena(enemy_pos + to_player * enemy.speed * dt)
            enemy.node.setPos(enemy_pos)

        if distance < 1.05 and enemy.attack_cooldown == 0.0:
            enemy.attack_cooldown = 1.1
            self.player_hp = max(0, self.player_hp - enemy.contact_damage)
            self._log(f"{enemy.name} bites for {enemy.contact_damage}.")
            if self.player_hp == 0:
                self._log("You collapse. Reset the arena to stand back up.")

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
            return

        if enemy.ai_state == "lunge":
            enemy.state_timer -= dt
            enemy_pos = self._clamp_to_arena(enemy_pos + enemy.lunge_direction * 8.8 * dt)
            hop_height = math.sin(max(0.0, enemy.state_timer) / 0.24 * math.pi) * 0.16
            enemy_pos.setZ(hop_height)
            enemy.node.setPos(enemy_pos)
            enemy.node.setScale(1.18, 0.82, 0.92)

            lunge_distance = (player_pos - enemy_pos).length()
            if lunge_distance < 1.08 and not enemy.attack_landed:
                enemy.attack_landed = True
                enemy.attack_cooldown = 1.15
                self.player_hp = max(0, self.player_hp - enemy.contact_damage)
                self._log(f"{enemy.name} lunges for {enemy.contact_damage}.")
                if self.player_hp == 0:
                    self._log("You collapse. Reset the arena to stand back up.")

            if enemy.state_timer <= 0.0:
                enemy.ai_state = "idle"
                enemy.state_timer = self.rng.uniform(0.16, 0.42)
                enemy.node.setScale(1, 1, 1)
                enemy_pos.setZ(0)
                enemy.node.setPos(enemy_pos)
            return

        if enemy.ai_state == "hop":
            enemy.state_timer -= dt
            progress = 1.0 - max(0.0, enemy.state_timer) / max(0.01, enemy.hop_duration)
            pos = self._lerp_vec3(enemy.hop_start_pos, enemy.hop_target_pos, progress)
            pos = self._clamp_to_arena(pos)
            pos.setZ(math.sin(progress * math.pi) * 0.42)
            enemy.node.setPos(pos)
            enemy.node.setScale(0.96, 1.08, 1.0 + math.sin(progress * math.pi) * 0.18)

            if enemy.state_timer <= 0.0:
                enemy.ai_state = "idle"
                enemy.state_timer = self.rng.uniform(0.12, 0.36)
                pos.setZ(0)
                enemy.node.setPos(pos)
                enemy.node.setScale(1, 1, 1)
            return

        enemy.node.setScale(1, 1, 1)
        enemy.state_timer -= dt
        if distance < 2.35 and enemy.attack_cooldown == 0.0:
            enemy.ai_state = "telegraph"
            enemy.state_timer = 0.38
            self._spawn_rabbit_attack_tell(enemy)
        elif enemy.state_timer <= 0.0:
            self._start_rabbit_hop(enemy, enemy_pos, to_player, distance)

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
        target = self._clamp_to_arena(enemy_pos + direction * hop_distance + strafe)

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

    def _update_camera(self):
        target = self.player.getPos()
        self.camera.setPos(target.getX(), target.getY() - 18.0, 14.0)
        self.camera.lookAt(target.getX(), target.getY() + 1.0, 0.4)

    def handle_interact(self):
        if self.fishing_state == "idle":
            if self._distance_to_shop() <= SHOP_RANGE:
                self._try_buy_next_rod()
            else:
                self._start_fishing_cast()
        elif self.fishing_state == "waiting":
            self._log("Not yet. The bobber only drifts.")
        elif self.fishing_state == "bite":
            self._finish_fishing(success=True)

    def handle_fishing_action(self):
        self.handle_interact()

    def _distance_to_shop(self) -> float:
        return (self.player.getPos() - self.shop_spot).length()

    def _try_buy_next_rod(self):
        next_rod = next_fishing_rod(self.rod_tier)
        if next_rod is None:
            self._log(f"You already own the best rod: {fishing_rod_for_tier(self.rod_tier).name}.")
            return

        if self.gold < next_rod.price:
            needed = next_rod.price - self.gold
            self._log(f"{next_rod.name} costs {next_rod.price} gold. You need {needed} more.")
            return

        self.gold -= next_rod.price
        self.rod_tier = next_rod.tier
        self._build_weapon_model(self.current_weapon)
        self._set_catch_banner(f"Rod upgraded!\n{next_rod.name}")
        self._log(f"You buy the {next_rod.name} for {next_rod.price} gold.")
        self._log("Better rods pull stronger relics from deeper water.")

    def toggle_inspection(self):
        if self.current_weapon is None:
            self._log("There is no recovered weapon to inspect.")
            return

        self.inspect_open = not self.inspect_open
        self._update_inspection_ui()

    def _start_fishing_cast(self):
        distance = (self.player.getPos() - self.fishing_spot).length()
        if distance > FISHING_RANGE:
            self._log("The lake is too far away to cast.")
            return

        self.inspect_open = False
        self._clear_inspection_preview()
        self._update_inspection_ui()

        player_pos = self.player.getPos()
        self.cast_start_pos = Vec3(player_pos.getX(), player_pos.getY() + 0.8, 0.9)
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
        self._create_bobber(self.cast_start_pos)
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
        self.current_weapon = generate_weapon(self.rng, self.rod_tier)
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

    def attack(self):
        if self.player_hp <= 0:
            self._log("You need to reset the arena first.")
            return
        if self.fishing_state != "idle":
            self._log("You are busy with the line.")
            return
        if self.attack_cooldown > 0:
            return
        if self.current_weapon is None:
            self._log("Your hands are empty. The lake may fix that.")
            self.attack_cooldown = 0.45
            return

        self._start_swing()
        target = self._nearest_enemy_in_range()
        if target is None:
            self._log(f"{self.current_weapon.name} cuts only air.")
            self.attack_cooldown = 0.45
            return

        enemy_state = EnemyState(
            name=target.name,
            kind=target.kind,
            hp=target.hp,
            max_hp=target.max_hp,
        )
        result = resolve_attack(self.current_weapon, enemy_state, self.rng)
        target.hp = result.enemy_hp_after
        self.player_hp = min(self.player_max_hp, self.player_hp + result.healing)
        self.player_hp = max(0, self.player_hp - result.self_damage)

        for message in result.messages[-3:]:
            self._log(message)

        newly_revealed = discover_traits(self.current_weapon, result.discovered_traits)
        for trait_name in newly_revealed:
            self._log(f"Discovered weapon trait: {trait_name}.")
        if newly_revealed:
            self._update_inspection_ui()
            self._log("Press I to inspect the updated weapon card.")

        if result.healing:
            self._log(f"You recover {result.healing} health.")
        if result.self_damage:
            self._log(f"The weapon hurts you for {result.self_damage}.")

        self._apply_hit_feedback(target)

        if result.defeated:
            reward = gold_reward_for_enemy(target.kind)
            if reward:
                self.gold += reward
                self._spawn_gold_reward_effect(target.node.getPos(), reward)
                self._log(f"You collect {reward} gold coins.")
            if target.kind == "rabbit":
                self._spawn_rabbit_defeat_effects(target)
            target.node.removeNode()
            self.enemies.remove(target)

        self.attack_cooldown = 0.55

    def _apply_hit_feedback(self, target: SceneEnemy):
        direction = target.node.getPos() - self.player.getPos()
        direction.setZ(0)
        if direction.length() == 0:
            direction = Vec3(0, -1, 0)
        else:
            direction.normalize()

        target.flash_time = 0.18
        target.knockback_velocity = direction * 6.5
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

    def reset_arena(self):
        for enemy in self.enemies:
            enemy.node.removeNode()
        self.enemies.clear()
        for effect in self.hit_effects:
            effect.node.removeNode()
        self.hit_effects.clear()
        self.player_hp = self.player_max_hp
        self.player.setPos(0, 3.0, 0)
        self.spawn_rabbits(4)
        self._log("The arena is reset.")

    def spawn_rabbits(self, count: int = 3):
        for index in range(count):
            x = self.rng.uniform(-6.5, 6.5)
            y = self.rng.uniform(-12.4, -5.2)
            self.enemies.append(self._make_rabbit(index + 1, Vec3(x, y, 0)))
        self._log(f"{count} white rabbits skitter into the arena.")

    def spawn_monster(self):
        x = self.rng.uniform(-5.0, 5.0)
        y = self.rng.uniform(-12.0, -6.0)
        self.enemies.append(self._make_monster(Vec3(x, y, 0)))
        self._log("Something larger drags itself out of the reeds.")

    def _make_rabbit(self, number: int, pos: Vec3) -> SceneEnemy:
        root = self.render.attachNewNode(f"rabbit-{number}")
        make_box(root, "rabbit-shadow", (0.78, 0.42, 0.03), (0.02, 0.025, 0.02, 0.25), (0, 0.04, 0.035))
        make_box(root, "rabbit-body", (0.8, 0.5, 0.35), (0.96, 0.96, 0.92, 1), (0, 0, 0.28))
        make_box(root, "rabbit-head", (0.42, 0.42, 0.38), (1.0, 1.0, 0.98, 1), (0, 0.38, 0.52))
        make_box(root, "rabbit-ear-left", (0.12, 0.12, 0.62), (1.0, 0.93, 0.93, 1), (-0.14, 0.42, 0.92))
        make_box(root, "rabbit-ear-right", (0.12, 0.12, 0.62), (1.0, 0.93, 0.93, 1), (0.14, 0.42, 0.92))
        make_box(root, "rabbit-eye-left", (0.08, 0.04, 0.08), (0.95, 0.08, 0.08, 1), (-0.1, 0.61, 0.57))
        make_box(root, "rabbit-eye-right", (0.08, 0.04, 0.08), (0.95, 0.08, 0.08, 1), (0.1, 0.61, 0.57))
        root.setPos(pos)
        return SceneEnemy(
            name="Rabid White Rabbit",
            kind="rabbit",
            hp=18,
            max_hp=18,
            node=root,
            speed=2.4,
            contact_damage=2,
        )

    def _make_monster(self, pos: Vec3) -> SceneEnemy:
        root = self.render.attachNewNode("mire-grub")
        make_box(root, "monster-shadow", (1.85, 1.25, 0.035), (0.02, 0.025, 0.02, 0.32), (0, 0.25, 0.035))
        make_box(root, "monster-body", (1.7, 1.2, 0.9), (0.22, 0.38, 0.24, 1), (0, 0, 0.45))
        make_box(root, "monster-head", (1.0, 0.8, 0.75), (0.26, 0.46, 0.27, 1), (0, 0.78, 0.62))
        make_box(root, "monster-eye-left", (0.14, 0.08, 0.14), (0.9, 0.9, 0.3, 1), (-0.22, 1.18, 0.72))
        make_box(root, "monster-eye-right", (0.14, 0.08, 0.14), (0.9, 0.9, 0.3, 1), (0.22, 1.18, 0.72))
        root.setPos(pos)
        return SceneEnemy(
            name="Mire Grub",
            kind="monster",
            hp=42,
            max_hp=42,
            node=root,
            speed=1.2,
            contact_damage=5,
        )

    def _nearest_enemy_in_range(self) -> Optional[SceneEnemy]:
        player_pos = self.player.getPos()
        nearby: List[Tuple[float, SceneEnemy]] = []
        for enemy in self.enemies:
            distance = (enemy.node.getPos() - player_pos).length()
            if distance <= ATTACK_RANGE:
                nearby.append((distance, enemy))

        if not nearby:
            return None

        nearby.sort(key=lambda item: item[0])
        return nearby[0][1]

    def _update_ui(self):
        rod = fishing_rod_for_tier(self.rod_tier)
        self.status_text.setText(
            f"Health {self.player_hp}/{self.player_max_hp}\n"
            f"Gold {self.gold}\n"
            f"Rod {rod.name}\n"
            f"Enemies nearby {len(self.enemies)}"
        )

        if self.current_weapon is None:
            weapon_lines = "Weapon: none\nTraits: none discovered"
        else:
            weapon_lines = (
                f"Weapon: {self.current_weapon.name}\n"
                f"Type: {self.current_weapon.weapon_type}  "
                f"Rarity: {self.current_weapon.rarity}  "
                f"Damage: {self.current_weapon.base_damage}\n"
                f"Traits: {trait_summary(self.current_weapon)}"
            )
        self.weapon_text.setText(weapon_lines)

        distance_to_lake = (self.player.getPos() - self.fishing_spot).length()
        distance_to_shop = self._distance_to_shop()
        if self.fishing_state == "casting":
            prompt = "Casting..."
        elif self.fishing_state == "waiting":
            prompt = "Watch the bobber."
        elif self.fishing_state == "bite":
            prompt = "Bite! Press E now!"
        elif self.fishing_state == "reeling":
            prompt = "Reeling in..."
        elif self.player_hp <= 0:
            prompt = "You are down. Reset the arena."
        elif distance_to_shop <= SHOP_RANGE:
            prompt = self._shop_prompt()
        elif distance_to_lake <= FISHING_RANGE:
            prompt = "Press E to cast into the lake."
        elif self.enemies:
            prompt = "The arena waits below the dock."
        else:
            prompt = "The arena is quiet."
        self.prompt_text.setText(prompt)

        if self.catch_banner_timer > 0.0:
            self.catch_text.setText(self.catch_banner_text)
        else:
            self.catch_text.setText("")

        self._update_inspection_ui()
        self.log_text.setText("\n".join(self.log_lines[-7:]))

    def _shop_prompt(self) -> str:
        next_rod = next_fishing_rod(self.rod_tier)
        if next_rod is None:
            return f"{fishing_rod_for_tier(self.rod_tier).name}: best rod owned."
        if self.gold >= next_rod.price:
            return f"Press E to buy {next_rod.name} for {next_rod.price} gold."
        return f"{next_rod.name} costs {next_rod.price} gold. You have {self.gold}."

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
