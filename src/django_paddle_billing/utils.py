from django.apps import apps

from django_paddle_billing import settings as app_settings


def get_account_model():
    app, model = app_settings.PADDLE_ACCOUNT_MODEL.split(".")
    return apps.get_model(app, model, require_ready=False)
