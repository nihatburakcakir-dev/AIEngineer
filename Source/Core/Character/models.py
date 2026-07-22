from dataclasses import asdict, dataclass, field


@dataclass
class CharacterProfile:
    name: str
    dimension: str
    archetype: str
    locomotion: str
    source_image: str
    confidence: float
    needs_placeholder_mesh: bool = True


@dataclass
class PhysicsSetup:
    collider: str
    rigidbody: str
    mass: float
    constraints: list[str]


@dataclass
class AnimatorSetup:
    controller_path: str
    states: list[str] = field(default_factory=lambda: ["Idle", "Walk", "Run", "Jump"])
    uses_placeholder_clips: bool = True


@dataclass
class CharacterPrefabPlan:
    profile: CharacterProfile
    physics: PhysicsSetup
    animator: AnimatorSetup
    controller_class: str
    prefab_path: str
    operations: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    requires_review: bool = True

    def to_dict(self):
        return asdict(self)
