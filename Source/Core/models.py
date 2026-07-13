from dataclasses import dataclass, field


@dataclass
class UnityDocument:

    title: str

    path: str

    paragraphs: list[str] = field(default_factory=list)

    code_blocks: list[str] = field(default_factory=list)

    tables: list[str] = field(default_factory=list)

    links: list[str] = field(default_factory=list)

    images: list[str] = field(default_factory=list)