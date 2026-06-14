"""JSON-driven choice helpers for generic deployments.

The original project contains many domain-specific tuples in
``EnterpriseApp.utility_toolkit.system_variables``.  Keep those for backward
compatibility, but use this module for new generic models/forms so choices can
be changed without editing Python code.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from django.conf import settings

DEFAULT_CHOICES_PATH = Path(settings.BASE_DIR) / "EnterpriseApp" / "config" / "choices.json"


@lru_cache(maxsize=1)
def load_choice_config(path: str | Path | None = None) -> dict[str, list[dict[str, str]]]:
    """Load choice configuration from JSON.

    The cache avoids reading the file repeatedly during form/model creation.
    Tests can call ``load_choice_config.cache_clear()`` after replacing the file.
    """

    config_path = Path(path) if path else DEFAULT_CHOICES_PATH
    with config_path.open(encoding="utf-8") as fh:
        return json.load(fh)


def get_choices(key: str, *, path: str | Path | None = None) -> list[tuple[str, str]]:
    """Return Django-compatible choices for the given key.

    Example: ``get_choices("personnel_status")`` returns
    ``[("active", "Active"), ...]``.
    """

    config = load_choice_config(path)
    values: Iterable[dict[str, str]] = config.get(key, [])
    return [(item["value"], item["label"]) for item in values]
