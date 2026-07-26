# Top-level on purpose: the launcher must be importable without executing
# reactivated/__init__.py, which requires configured Django settings and
# eagerly patches runserver. Nothing here may import Django or reactivated.
