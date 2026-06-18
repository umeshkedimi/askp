"""SQLModel ORM models — the physical realization of the Core Concepts domain model.

Importing this package registers every table on ``SQLModel.metadata``, which Alembic and the
test harness use to know the full schema. Add new model modules to the imports below so they
are discovered.
"""

from askp.models.base import Base
from askp.models.tenancy import Organization, Project

__all__ = ["Base", "Organization", "Project"]
