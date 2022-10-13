from unittest.mock import patch
import pytest
from baserow_enterprise.role.actions import AssignRoleActionType
from baserow_enterprise.role.models import Role, RoleAssignment
from baserow_enterprise.role.operations import AssignRoleGroupOperationType

from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry
from baserow.core.action.scopes import GroupActionScopeType
from baserow.test_utils.helpers import assert_undo_redo_actions_are_valid


@pytest.mark.django_db
@pytest.mark.undo_redo
@patch("baserow.core.handler.CoreHandler.check_permissions")
def test_can_undo_create_table(mock_check_permissions, data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    user2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user)

    table = data_fixture.create_database_table(user=user)

    builder_role = Role.objects.get(uid="builder")

    action_type_registry.get_by_type(AssignRoleActionType).do(
        user, user2, group, builder_role, scope=table
    )

    mock_check_permissions.assert_called_with(
        user, AssignRoleGroupOperationType.type, group=group, context=group
    )

    assert RoleAssignment.objects.count() == 1

    mock_check_permissions.reset_mock()

    actions_undone = ActionHandler.undo(
        user, [GroupActionScopeType.value(group_id=group.id)], session_id
    )

    mock_check_permissions.assert_called_with(
        user, AssignRoleGroupOperationType.type, group=group, context=group
    )

    assert_undo_redo_actions_are_valid(actions_undone, [AssignRoleActionType])
    assert RoleAssignment.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.undo_redo
@patch("baserow.core.handler.CoreHandler.check_permissions")
def test_can_undo_redo_create_table(mock_check_permissions, data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    user2 = data_fixture.create_user()
    group = data_fixture.create_group(user=user)

    table = data_fixture.create_database_table(user=user)

    builder_role = Role.objects.get(uid="builder")

    action_type_registry.get_by_type(AssignRoleActionType).do(
        user, user2, group, builder_role, table
    )

    assert RoleAssignment.objects.count() == 1

    ActionHandler.undo(
        user, [GroupActionScopeType.value(group_id=group.id)], session_id
    )

    assert RoleAssignment.objects.count() == 0

    mock_check_permissions.reset_mock()

    actions_redone = ActionHandler.redo(
        user, [GroupActionScopeType.value(group_id=group.id)], session_id
    )
    assert_undo_redo_actions_are_valid(actions_redone, [AssignRoleActionType])

    mock_check_permissions.assert_called_with(
        user, AssignRoleGroupOperationType.type, group=group, context=group
    )

    assert RoleAssignment.objects.count() == 1
