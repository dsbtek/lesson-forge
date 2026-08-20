"""SQLAlchemy models.

Importing this package registers every model on ``Base.metadata`` so Alembic
autogenerate and ``create_all`` see the full schema.
"""

from app.models.export import Export
from app.models.generation import AgentEvent, GenerationRun
from app.models.knowledge import KnowledgeChunk
from app.models.lesson import Lesson, LessonVersion
from app.models.user import User

__all__ = [
    "User",
    "Lesson",
    "LessonVersion",
    "GenerationRun",
    "AgentEvent",
    "Export",
    "KnowledgeChunk",
]
