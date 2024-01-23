# SPDX-FileCopyrightText: 2023-present Benjamin Gervan <benjamin@websideproject.com>
#
# SPDX-License-Identifier: MIT
from django.core.serializers.json import DjangoJSONEncoder


class PrettyJSONEncoder(DjangoJSONEncoder):
    def __init__(self, *args, indent, sort_keys, **kwargs):
        super().__init__(*args, indent=4, sort_keys=True, **kwargs)
