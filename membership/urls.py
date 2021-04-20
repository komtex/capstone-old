from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("view_user", views.view_user, name="view_user"),
    path("add", views.add_user, name="add_user"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("login", views.login_view, name="login"),
    path("search", views.search_user, name="search_user"),
    path("delete/<int:id>", views.delete_user, name="delete_user"),
    path("update/<int:id>", views.update_user, name="update_user"),
    path("users", views.users, name="users")
]
