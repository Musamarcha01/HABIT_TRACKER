"""Application layer for the Habit Tracker.

:class:`HabitService` is the orchestrator that sits between the presentation
layer (the CLI) and the two lower layers (the repository and the analytics
functions). It owns the business rules — validating input, preventing
duplicates, coordinating a create-then-complete flow — so the CLI can stay a
thin layer of input/output and the analytics functions can stay pure.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import analytics
from habit import VALID_PERIODICITIES, Habit
from database import HabitRepository


class HabitService:
    """Coordinate habit operations across the data and analytics layers."""

    def __init__(self, repository: HabitRepository) -> None:
        """Create the service.

        Args:
            repository: The data-access layer the service delegates to.
        """
        self._repository = repository

    # ------------------------------------------------------------------ #
    # Habit management
    # ------------------------------------------------------------------ #
    def create_habit(self, name: str, periodicity: str) -> Habit:
        """Create and persist a new habit.

        Args:
            name: Task specification for the habit.
            periodicity: ``"daily"`` or ``"weekly"``.

        Returns:
            The newly created habit.

        Raises:
            ValueError: If the name/periodicity are invalid or the name is
                already taken (surfaced from the model and repository).
        """
        habit = Habit(name=name.strip(), periodicity=periodicity)
        self._repository.add_habit(habit)
        return habit

    def delete_habit(self, habit_id: str) -> bool:
        """Delete a habit and all of its completion history.

        Returns:
            ``True`` if a habit was removed, ``False`` otherwise.
        """
        return self._repository.delete_habit(habit_id)

    def complete_habit(
        self, habit_id: str, when: Optional[datetime] = None
    ) -> None:
        """Check off a habit at the given time (default: now).

        Raises:
            ValueError: If the habit does not exist.
        """
        self._repository.add_completion(habit_id, when)

    def get_all_habits(self) -> List[Habit]:
        """Return every tracked habit."""
        return self._repository.get_habits()

    def get_habit(self, habit_id: str) -> Optional[Habit]:
        """Return a single habit by id, or ``None``."""
        return self._repository.get_habit_by_id(habit_id)

    def get_habit_by_name(self, name: str) -> Optional[Habit]:
        """Return a single habit by name, or ``None``."""
        return self._repository.get_habit_by_name(name)

    # ------------------------------------------------------------------ #
    # Analytics (delegated to the pure functional module)
    # ------------------------------------------------------------------ #
    def list_habits_as_dicts(self) -> List[dict]:
        """Return all habits in serialisable dictionary form."""
        return analytics.list_all_habits(self._repository.get_habits())

    def get_habits_by_periodicity(self, periodicity: str) -> List[Habit]:
        """Return all habits with the requested periodicity.

        Raises:
            ValueError: If ``periodicity`` is not a supported value.
        """
        if periodicity not in VALID_PERIODICITIES:
            raise ValueError(
                f"Periodicity must be one of {VALID_PERIODICITIES}."
            )
        return analytics.habits_by_periodicity(
            self._repository.get_habits(), periodicity
        )

    def get_longest_streak_all(self) -> int:
        """Return the longest run streak across every habit."""
        return analytics.longest_streak_all(
            self._repository.get_habits(), self._repository.get_completions
        )

    def get_longest_streak(self, habit_id: str) -> int:
        """Return the longest run streak for one habit.

        Raises:
            ValueError: If the habit does not exist.
        """
        habit = self._repository.get_habit_by_id(habit_id)
        if habit is None:
            raise ValueError(f"No habit found with id {habit_id!r}.")
        completions = self._repository.get_completions(habit_id)
        return analytics.longest_streak_for_habit(habit, completions)

    def get_struggling_habits(self) -> List[dict]:
        """Return habits ranked worst-first by number of missed periods."""
        return analytics.struggling_habits(
            self._repository.get_habits(), self._repository.get_completions
        )
