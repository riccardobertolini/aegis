"""Unit tests: RBAC enforcer."""
import pytest

from backend.domain.ports.security import Permission
from backend.infrastructure.security.rbac import RBACEnforcer


@pytest.fixture
def enforcer():
    return RBACEnforcer()


def test_superadmin_has_all_permissions(enforcer):
    for perm in Permission:
        assert enforcer.may(["superadmin"], perm)


def test_viewer_can_read_model(enforcer):
    assert enforcer.may(["viewer"], Permission.MODEL_READ)


def test_viewer_cannot_train(enforcer):
    assert not enforcer.may(["viewer"], Permission.MODEL_TRAIN)


def test_operator_inherits_viewer_perms(enforcer):
    viewer_perms = enforcer.resolve(["viewer"])
    operator_perms = enforcer.resolve(["operator"])
    assert viewer_perms.issubset(operator_perms)


def test_unknown_role_grants_nothing(enforcer):
    assert enforcer.resolve(["ghost"]) == set()


def test_combined_roles_union(enforcer):
    perms = enforcer.resolve(["viewer", "operator"])
    assert Permission.KNOWLEDGE_WRITE in perms


def test_parse_resource_action_valid(enforcer):
    perm = enforcer.parse_resource_action("model", "read")
    assert perm == Permission.MODEL_READ


def test_parse_resource_action_invalid(enforcer):
    assert enforcer.parse_resource_action("galaxy", "destroy") is None


def test_custom_role_override():
    custom = {"custom_reader": [Permission.DOCUMENT_READ]}
    e = RBACEnforcer(custom_roles=custom)
    assert e.may(["custom_reader"], Permission.DOCUMENT_READ)
    assert not e.may(["custom_reader"], Permission.DOCUMENT_WRITE)
