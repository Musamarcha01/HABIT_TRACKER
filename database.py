"""Data-access layer for the Habit Tracker application.

This module implements :class:`HabitRepository`, the only component that talks
to the SQLite database. It hides all SQL behind a small set of methods so the
rest of the application depends on an intention-revealing interface rather than
on raw queries.

The schema consists of two tables:

* ``habits``       — one row per defined habit.
* ``completions``  — one row per time a habit is checked off (an append-only
  event log). A foreign key ties each completion back to its habit, with
  ``ON DELETE CASCADE`` so deleting a habit also removes its history.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import List, Optional

from habit import Habit

DEFAULT_DB_PATH = "habits.db"


class HabitRepository:
    """Persist and retrieve habits and their completion events via SQLite."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        """Open (or create) the database and initialise the schema.

        Args:
            db_path: Path to the SQLite file. Use ``":memory:"`` for an
                isolated, in-memory database (handy for tests).
        """
        # ``detect_types`` is not needed because timestamps are stored as ISO
        # strings and parsed explicitly, which keeps behaviour predictable.
        self._connection = sqlite3.connect(db_path)
        # Enforce foreign-key constraints (off by default in SQLite).
        self._connection.execute("PRAGMA foreign_keys = ON;")
        self._initialise_schema()

    def _initialise_schema(self) -> None:
        """Create the ``habits`` and ``completions`` tables if absent."""
        with self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS habits (
                    id          TEXT PRIMARY KEY,
                    name        TEXT NOT NULL,
                    periodicity TEXT NOT NULL CHECK (periodicity IN ('daily', 'weekly')),
                    created_at  TEXT NOT NULL
                );
                """
            )
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS completions (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    habit_id     TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    FOREIGN KEY (habit_id) REFERENCES habits (id) ON DELETE CASCADE
                );
                """
            )

    # ------------------------------------------------------------------ #
    # Habit CRUD
    # ------------------------------------------------------------------ #
    def add_habit(self, habit: Habit) -> None:
        """Insert a new habit.

        Args:
            habit: The habit to persist.

        Raises:
            ValueError: If a habit with the same name already exists.
        """
        if self.get_habit_by_name(habit.name) is not None:
            raise ValueError(f"A habit named {habit.name!r} already exists.")
        with self._connection:
            self._connection.execute(
                "INSERT INTO habits (id, name, periodicity, created_at) "
                "VALUES (?, ?, ?, ?);",
                (habit.id, habit.name, habit.periodicity, habit.created_at.isoformat()),
            )

    def get_habits(self) -> List[Habit]:
        """Return every stored habit, ordered by creation time."""
        rows = self._connection.execute(
            "SELECT id, name, periodicity, created_at FROM habits "
            "ORDER BY created_at;"
        ).fetchall()
        return [Habit.from_row(row) for row in rows]

    def get_habit_by_id(self, habit_id: str) -> Optional[Habit]:
        """Return the habit with the given id, or ``None`` if not found."""
        row = self._connection.execute(
            "SELECT id, name, periodicity, created_at FROM habits WHERE id = ?;",
            (habit_id,),
        ).fetchone()
        return Habit.from_row(row) if row else None

    def get_habit_by_name(self, name: str) -> Optional[Habit]:
        """Return the habit with the given name, or ``None`` if not found."""
        row = self._connection.execute(
            "SELECT id, name, periodicity, created_at FROM habits WHERE name = ?;",
            (name,),
        ).fetchone()
        return Habit.from_row(row) if row else None

    def delete_habit(self, habit_id: str) -> bool:
        """Delete a habit and, via cascade, all of its completions.

        Args:
            habit_id: Identifier of the habit to remove.

        Returns:
            ``True`` if a habit was deleted, ``False`` if no such habit existed.
        """
        with self._connection:
            cursor = self._connection.execute(
                "DELETE FROM habits WHERE id = ?;", (habit_id,)
            )
        return cursor.rowcount > 0

    # ------------------------------------------------------------------ #
    # Completion events
    # ------------------------------------------------------------------ #
    def add_completion(
        self, habit_id: str, completed_at: Optional[datetime] = None
    ) -> None:
        """Record that a habit was checked off.

        Args:
            habit_id: Identifier of the habit being completed.
            completed_at: When the completion happened. Defaults to now.

        Raises:
            ValueError: If the habit does not exist.
        """
        if self.get_habit_by_id(habit_id) is None:
            raise ValueError(f"No habit found with id {habit_id!r}.")
        when = completed_at if completed_at is not None else datetime.now()
        with self._connection:
            self._connection.execute(
                "INSERT INTO completions (habit_id, completed_at) VALUES (?, ?);",
                (habit_id, when.isoformat()),
            )

    def get_completions(self, habit_id: str) -> List[datetime]:
        """Return all completion timestamps for a single habit, sorted."""
        rows = self._connection.execute(
            "SELECT completed_at FROM completions WHERE habit_id = ? "
            "ORDER BY completed_at;",
            (habit_id,),
        ).fetchall()
        return [datetime.fromisoformat(row[0]) for row in rows]

    def close(self) -> None:
        """Close the underlying database connection."""
        self._connection.close()

    def __enter__(self) -> "HabitRepository":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
