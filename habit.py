"""Domain model for the Habit Tracker application.

This module defines :class:`Habit`, the core object-oriented entity of the
system. A habit is a *clearly defined task that must be completed
periodically*. Each habit encapsulates its own identity, name, periodicity
and creation timestamp, together with the behaviour required to validate
and serialise itself.

The class is intentionally free of any persistence or presentation logic so
that it can be reused across the data layer, the analytics layer and the CLI
without creating dependencies between them.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

# The two periodicities the tracker is required to support.
VALID_PERIODICITIES = ("daily", "weekly")


class Habit:
    """Represent a single trackable habit.

    Attributes:
        id: A stable, unique identifier for the habit (32-char hex UUID).
        name: The human-readable task specification, e.g. ``"Morning Exercise"``.
        periodicity: How often the habit must be completed; either
            ``"daily"`` or ``"weekly"``.
        created_at: The moment the habit was created.
    """

    def __init__(
        self,
        name: str,
        periodicity: str,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ) -> None:
        """Create a habit and validate its fields.

        Args:
            name: Task specification of the habit. Must be a non-empty string.
            periodicity: Either ``"daily"`` or ``"weekly"``.
            id: Optional pre-existing identifier. When ``None`` (the default,
                used when a user creates a brand-new habit) a fresh UUID is
                generated. Supplying an ``id`` is used when re-building a habit
                loaded from the database.
            created_at: Optional creation timestamp. Defaults to
                :func:`datetime.now` for new habits and is supplied explicitly
                when re-hydrating a habit from storage.

        Raises:
            ValueError: If ``name`` is empty or ``periodicity`` is invalid.
        """
        self.id: str = id if id is not None else uuid4().hex
        self.name: str = name
        self.periodicity: str = periodicity
        self.created_at: datetime = (
            created_at if created_at is not None else datetime.now()
        )
        self.validate()

    def validate(self) -> None:
        """Ensure the habit's fields are well-formed.

        Raises:
            ValueError: If the name is blank or the periodicity is not one of
                :data:`VALID_PERIODICITIES`.
        """
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Habit name must be a non-empty string.")
        if self.periodicity not in VALID_PERIODICITIES:
            raise ValueError(
                f"Periodicity must be one of {VALID_PERIODICITIES}, "
                f"got {self.periodicity!r}."
            )

    def to_dict(self) -> dict:
        """Return a plain-``dict`` representation of the habit.

        Used by the analytics layer (functional transformations map habits to
        dictionaries) and anywhere a serialisable form is convenient.
        """
        return {
            "id": self.id,
            "name": self.name,
            "periodicity": self.periodicity,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_row(cls, row: tuple) -> "Habit":
        """Rebuild a :class:`Habit` from a database row.

        Args:
            row: A ``(id, name, periodicity, created_at)`` tuple as returned by
                the repository, where ``created_at`` is an ISO-8601 string.

        Returns:
            A fully-initialised :class:`Habit` instance.
        """
        habit_id, name, periodicity, created_at = row
        return cls(
            name=name,
            periodicity=periodicity,
            id=habit_id,
            created_at=datetime.fromisoformat(created_at),
        )

    def __eq__(self, other: object) -> bool:
        """Two habits are equal when they share the same identifier."""
        return isinstance(other, Habit) and self.id == other.id

    def __repr__(self) -> str:
        return (
            f"Habit(name={self.name!r}, periodicity={self.periodicity!r}, "
            f"id={self.id!r})"
        )
