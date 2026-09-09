from dataclasses import dataclass, field


@dataclass(frozen=True)
class Identity:
    kind: str = ""
    actor: object = None
    label: str = ""
    capabilities: frozenset = field(default_factory=frozenset)

    @property
    def authenticated(self) -> bool:
        return bool(self.kind)

    def has_any(self, *capabilities) -> bool:
        if not capabilities:
            return self.authenticated
        return bool(self.capabilities.intersection(capabilities))


ANONYMOUS = Identity()
