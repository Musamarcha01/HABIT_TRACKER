"""Analytics for the Habit Tracker, written in the functional paradigm.

Every function in this module is *pure*: it takes data in and returns a value
out, with no side effects and no knowledge of the database or the CLI. Habit
and completion data are passed in as arguments, which keeps the functions easy
to test in isolation and lets the transformations be expressed with the
classic functional trio — :func:`map`, :func:`filter` and
:func:`functools.reduce` — plus small lambdas and comprehensions.

The four functions mandated by the task specification are:

* :func:`list_all_habits`            — list every tracked habit;
* :func:`habits_by_periodicity`      — list habits sharing a periodicity;
* :func:`longest_streak_all`         — longest run streak across all habits;
* :func:`longest_streak_for_habit`   — longest run streak for one habit.

Two extra helpers answer the analytical questions raised in the brief
(*"which habits did I struggle with most?"*, *"what are my current daily
habits?"*).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from functools import reduce
from typing import Callable, Dict, List

from habit import Habit

# Number of days in each period, used to test whether two consecutive
# completions belong to adjacent periods.
_PERIOD_STEP: Dict[str, timedelta] = {
    "daily": timedelta(days=1),
    "weekly": timedelta(days=7),
}


def list_all_habits(habits: List[Habit]) -> List[dict]:
    """Return every tracked habit as a plain dictionary.

    Implemented with :func:`map`, mapping each :class:`Habit` object to its
    dictionary form.

    Args:
        habits: The habits to list.

    Returns:
        A list of habit dictionaries (see :meth:`Habit.to_dict`).
    """
    return list(map(lambda habit: habit.to_dict(), habits))


def habits_by_periodicity(habits: List[Habit], periodicity: str) -> List[Habit]:
    """Return the habits that share a given periodicity.

    Implemented with :func:`filter`.

    Args:
        habits: The habits to search.
        periodicity: ``"daily"`` or ``"weekly"``.

    Returns:
        The subset of ``habits`` whose periodicity matches.
    """
    return list(filter(lambda habit: habit.periodicity == periodicity, habits))


def _period_key(moment: datetime, periodicity: str) -> date:
    """Collapse a timestamp onto the start of the period it belongs to.

    For daily habits this is simply the calendar date. For weekly habits it is
    the Monday of that week, so any two completions in the same week map to the
    same key and adjacent weeks are exactly seven days apart — which also makes
    the logic correct across month and year boundaries.
    """
    day = moment.date()
    if periodicity == "weekly":
        day = day - timedelta(days=day.weekday())  # back up to Monday
    return day


def _longest_run(sorted_periods: List[date], step: timedelta) -> int:
    """Return the length of the longest run of consecutive periods.

    Args:
        sorted_periods: Unique period-start dates in ascending order.
        step: The gap that separates two *adjacent* periods (1 or 7 days).

    Returns:
        The longest number of periods completed back-to-back.
    """

    def accumulate(state: tuple, current: date) -> tuple:
        best, run_length, previous = state
        if previous is not None and current - previous == step:
            run_length += 1  # streak continues
        else:
            run_length = 1  # streak (re)starts at this period
        return (max(best, run_length), run_length, current)

    best, _, _ = reduce(accumulate, sorted_periods, (0, 0, None))
    return best


def calculate_streak(completions: List[datetime], periodicity: str) -> int:
    """Compute the longest run streak from a list of completion timestamps.

    Args:
        completions: All timestamps at which a habit was checked off.
        periodicity: ``"daily"`` or ``"weekly"``.

    Returns:
        The length of the longest streak of consecutive completed periods.
        Multiple completions within the same period count once. Returns ``0``
        when there are no completions.
    """
    if not completions:
        return 0
    step = _PERIOD_STEP[periodicity]
    # Map every timestamp to its period key, drop duplicates, sort ascending.
    unique_periods = sorted(
        set(map(lambda moment: _period_key(moment, periodicity), completions))
    )
    return _longest_run(unique_periods, step)


def longest_streak_for_habit(habit: Habit, completions: List[datetime]) -> int:
    """Return the longest run streak for a single habit.

    Args:
        habit: The habit in question (its periodicity drives the calculation).
        completions: That habit's completion timestamps.
    """
    return calculate_streak(completions, habit.periodicity)


def longest_streak_all(
    habits: List[Habit],
    completions_of: Callable[[str], List[datetime]],
) -> int:
    """Return the longest run streak found across *all* habits.

    Implemented with :func:`reduce`, folding the per-habit streaks into a
    single maximum.

    Args:
        habits: All defined habits.
        completions_of: A function mapping a habit id to its completion
            timestamps (typically ``repository.get_completions``).

    Returns:
        The best streak achieved by any habit, or ``0`` when there is no data.
    """
    return reduce(
        lambda best, habit: max(
            best, longest_streak_for_habit(habit, completions_of(habit.id))
        ),
        habits,
        0,
    )


def struggling_habits(
    habits: List[Habit],
    completions_of: Callable[[str], List[datetime]],
) -> List[dict]:
    """Rank habits by how much the user struggled with them.

    "Struggle" is measured by the number of *breaks*: periods between the first
    completion and now in which the habit was expected but not completed. A
    higher break count means more struggle. Habits are returned worst-first.

    Args:
        habits: All defined habits.
        completions_of: A function mapping a habit id to its completions.

    Returns:
        A list of ``{"habit", "breaks", "streak"}`` dicts sorted by ``breaks``
        in descending order.
    """

    def summarise(habit: Habit) -> dict:
        completions = completions_of(habit.id)
        return {
            "habit": habit,
            "breaks": _count_breaks(habit, completions),
            "streak": longest_streak_for_habit(habit, completions),
        }

    summaries = list(map(summarise, habits))
    return sorted(summaries, key=lambda item: item["breaks"], reverse=True)


def _count_breaks(habit: Habit, completions: List[datetime]) -> int:
    """Count expected-but-missed periods since a habit's first completion."""
    if not completions:
        return 0
    step = _PERIOD_STEP[habit.periodicity]
    completed = set(
        map(lambda moment: _period_key(moment, habit.periodicity), completions)
    )
    first = min(completed)
    today = _period_key(datetime.now(), habit.periodicity)
    # Walk every period from the first completion up to today, counting gaps.
    breaks, cursor = 0, first
    while cursor <= today:
        if cursor not in completed:
            breaks += 1
        cursor += step
    return breaks
