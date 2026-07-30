"""Predefined habits and four weeks of example tracking data.

The task requires the tracker to ship with **five predefined habits** (at
least one weekly and one daily) and, for each, **four weeks of example
completion data**. That data doubles as a *test fixture*: the streaks it
produces are fixed and known, so the automated tests can assert exact values
against it.

Each daily habit is described by the set of day-offsets (``0``-``27``) on which
it was completed; each weekly habit by the day-offsets of its weekly check-off.
Offsets are counted from a Monday start date so that weekly grouping lines up
cleanly with calendar weeks. The resulting longest streaks are:

======================  ========  ================
Habit                   Period    Longest streak
======================  ========  ================
Morning Exercise        daily     14 days
Read 30 Minutes         daily     13 days
Drink 2L Water          daily      7 days
Meditation              daily      6 days
Weekly Review           weekly     4 weeks
======================  ========  ================

The overall longest streak across all habits is therefore **14**.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Dict, List, Tuple

from database import HabitRepository
from habit import Habit
from service import HabitService

# Time of day stamped onto each generated completion (keeps timestamps tidy).
_COMPLETION_TIME = time(hour=8, minute=0)

# (name, periodicity, [completed day-offsets within the 28-day window])
PredefinedHabit = Tuple[str, str, List[int]]

PREDEFINED_HABITS: List[PredefinedHabit] = [
    # Completed every day except day 13 -> runs of 13 and 14 -> streak 14.
    ("Morning Exercise", "daily", [d for d in range(28) if d != 13]),
    # Completed every day except days 7 and 21 -> longest run 8..20 -> streak 13.
    ("Read 30 Minutes", "daily", [d for d in range(28) if d not in (7, 21)]),
    # Four blocks of 7/6/5/7 consecutive days -> longest run -> streak 7.
    (
        "Drink 2L Water",
        "daily",
        [0, 1, 2, 3, 4, 5, 6]          # week 1: 7
        + [8, 9, 10, 11, 12, 13]        # week 2: 6
        + [15, 16, 17, 18, 19]          # week 3: 5
        + [21, 22, 23, 24, 25, 26, 27], # week 4: 7
    ),
    # An improving but patchy record; longest block is days 18..23 -> streak 6.
    (
        "Meditation",
        "daily",
        [0, 1, 2]                       # 3
        + [5, 6, 7, 8, 9]               # 5
        + [12, 13, 14, 15]              # 4
        + [18, 19, 20, 21, 22, 23]      # 6
        + [25, 27],                     # sparse tail
    ),
    # One check-off in each of the four weeks -> 4 consecutive weeks -> streak 4.
    ("Weekly Review", "weekly", [3, 10, 17, 24]),
]

# The streaks the data above is engineered to produce, for use in tests.
EXPECTED_STREAKS: Dict[str, int] = {
    "Morning Exercise": 14,
    "Read 30 Minutes": 13,
    "Drink 2L Water": 7,
    "Meditation": 6,
    "Weekly Review": 4,
}
EXPECTED_LONGEST_STREAK_ALL = 14


def default_start_date() -> date:
    """Return the Monday that begins the four-week example window.

    Anchored so the window ends in the current week and every generated
    completion sits in the past. Starting on a Monday keeps weekly grouping
    aligned with calendar weeks.
    """
    monday_this_week = date.today() - timedelta(days=date.today().weekday())
    return monday_this_week - timedelta(weeks=3)


def seed(repository: HabitRepository, start: date | None = None) -> HabitService:
    """Populate a repository with the predefined habits and their data.

    Existing habits with the same name are skipped, so calling :func:`seed`
    twice will not create duplicates.

    Args:
        repository: The repository to populate.
        start: Monday on which the 28-day window begins. Defaults to
            :func:`default_start_date`. Pass a fixed value in tests for full
            reproducibility.

    Returns:
        A :class:`HabitService` wrapping the seeded repository, for convenience.
    """
    start = start or default_start_date()
    service = HabitService(repository)

    for name, periodicity, offsets in PREDEFINED_HABITS:
        if repository.get_habit_by_name(name) is not None:
            continue
        # Backdate the creation to the start of the window.
        habit = Habit(
            name=name,
            periodicity=periodicity,
            created_at=datetime.combine(start, _COMPLETION_TIME),
        )
        repository.add_habit(habit)
        for offset in offsets:
            completed_at = datetime.combine(
                start + timedelta(days=offset), _COMPLETION_TIME
            )
            repository.add_completion(habit.id, completed_at)

    return service
