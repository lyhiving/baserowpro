from django.urls import re_path

from baserow.contrib.builder.api.workflow_actions.views import (
    BuilderWorkflowActionsView,
)

app_name = "baserow.contrib.builder.api.workflow_actions"

urls_without_builder_id = [
    re_path(
        r"page/(?P<page_id>[0-9]+)/workflow_actions/$",
        BuilderWorkflowActionsView.as_view(),
        name="list",
    )
]
