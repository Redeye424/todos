"""
URL configuration for todos project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from todo1 import views
urlpatterns = [
    path('', views.home, name='home'),

    path("accounts/signup/", views.signup, name="signup"),
    path("about_us", views.about_us, name="about_us"),

    path("service-worker.js", views.service_worker, name="service_worker"),
    path("accounts/login/", views.CustomLoginView.as_view(), name="login"),
    path("accounts/logout/", views.accounts, name="logout"),

    path('accounts/', views.accounts, name='accounts'),

    path("accounts/", include('django.contrib.auth.urls')),

    path('make_todo/', views.make_todo, name='make_todo'),
    path("ai/", views.ai, name="ai"),

    path("webpush/", include("webpush.urls")),

    path('admin/', admin.site.urls),
    path("save-webpush/", views.save_webpush, name="save_webpush"),

    path("todos/export/", views.export_todos, name="export_todos"),
    path("todos/import/", views.import_todos, name="import_todos"),
    path(
    "test-notification/",
    views.test_notification,
    name="test_notification"
    ),
]
