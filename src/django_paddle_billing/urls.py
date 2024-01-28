from django.urls import path

from django_paddle_billing import views

urlpatterns = [
    path("webhook/", views.paddle_webhook_view, name="webhook"),
]
