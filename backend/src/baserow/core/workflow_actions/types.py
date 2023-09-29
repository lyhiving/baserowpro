from typing import TypedDict, TypeVar

from baserow.core.workflow_actions.models import WorkflowAction


class WorkflowActionDict(TypedDict):
    id: int


WorkflowActionDictSubClass = TypeVar(
    "WorkflowActionDictSubClass", bound=WorkflowActionDict
)
WorkflowActionSubClass = TypeVar("WorkflowActionSubClass", bound=WorkflowAction)
