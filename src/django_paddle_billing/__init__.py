# SPDX-FileCopyrightText: 2023-present Benjamin Gervan <benjamin@websideproject.com>
#
# SPDX-License-Identifier: MIT
from django_paddle_billing.settings import settings as default_settings


class AppSettings:
    def __getattr__(self, name):
        if name in default_settings:
            return default_settings[name]

        raise AttributeError(f"'PADDLE_BILLING' settings object has no attribute '{name}'")


settings = AppSettings()
