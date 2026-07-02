"""RBAC enforcement: resolves roles → permissions and checks authorization."""
from typing import Iterable

from backend.domain.ports.security import DEFAULT_ROLES, Permission


class RBACEnforcer:
    """Stateless helper: given a set of role names, answers `may(permission)?`."""

    def __init__(self, custom_roles: dict[str, list[Permission]] | None = None) -> None:
        self._roles: dict[str, set[Permission]] = {
            name: set(perms) for name, perms in DEFAULT_ROLES.items()
        }
        if custom_roles:
            for name, perms in custom_roles.items():
                self._roles[name] = set(perms)

    def resolve(self, roles: Iterable[str]) -> set[Permission]:
        """Return the union of permissions for all given role names."""
        result: set[Permission] = set()
        for role in roles:
            result |= self._roles.get(role, set())
        return result

    def may(self, roles: Iterable[str], permission: Permission | str) -> bool:
        """True if any of the given roles grants the requested permission."""
        perm = Permission(permission) if isinstance(permission, str) else permission
        return perm in self.resolve(roles)

    def parse_resource_action(self, resource: str, action: str) -> Permission | None:
        """Convert (resource, action) pair to a Permission enum value if it exists."""
        candidate = f"{resource}:{action}"
        try:
            return Permission(candidate)
        except ValueError:
            return None

    def roles(self) -> list[str]:
        return list(self._roles.keys())
