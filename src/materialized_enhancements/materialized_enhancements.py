"""Reflex expects the app module at `<app_name>.<app_name>` by default.

With `app_name="materialized_enhancements"` this means it imports
`materialized_enhancements.materialized_enhancements`.
We keep the actual app definition in `materialized_enhancements.app` and re-export it here.
"""

from materialized_enhancements.app import app  # noqa: F401
