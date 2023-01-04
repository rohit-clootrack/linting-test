from django.urls import path

from linting_test.users.views import (
    user_detail_view,
    user_get,
    user_redirect_view,
    user_update_view,
)

app_name = "users"
urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("me/", view=user_get, name="update"),
    path("<str:username>/", view=user_detail_view, name="detail"),
]
