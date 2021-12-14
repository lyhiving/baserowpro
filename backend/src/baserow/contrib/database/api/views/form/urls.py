from django.urls import re_path

from .views import (
    SubmitFormViewView,
    FormViewLinkRowFieldLookupView,
)

app_name = "baserow.contrib.database.api.views.form"

urlpatterns = [
    re_path(
        r"(?P<slug>[-\w]+)/submit/$",
        SubmitFormViewView.as_view(),
        name="submit",
    ),
    re_path(
        r"(?P<slug>[-\w]+)/link-row-field-lookup/(?P<field_id>[0-9]+)/$",
        FormViewLinkRowFieldLookupView.as_view(),
        name="link_row_field_lookup",
    ),
]
