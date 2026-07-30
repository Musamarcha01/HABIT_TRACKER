"""Unit tests for the functional analytics module.

Covers the four required analytics functions plus streak edge cases, asserting
against the deterministic 4-week example fixture where useful.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import analytics
from fixtures import EXPECTED_LONGEST_STREAK_ALL, EXPECTED_STREAKS
from habit import Habit


def test_list_all_habits_returns_dicts():
    habits = [Habit("A", "daily"), Habit("B", "weekly")]
    result = analytics.list_all_habits(habits)
    assert [item["name"] for item in result] == ["A", "B"]
    assert all(isinstance(item, dict) for item in result)


def test_habits_by_periodicity_filters_correctly():
    habits = [Habit("A", "daily"), Habit("B", "weekly"), Habit("C", "daily")]
    daily = analytics.habits_by_periodicity(habits, "daily")
    assert {h.name for h in daily} == {"A", "C"}
    assert analytics.habits_by_periodicity(habits, "weekly")[0].name == "B"


def test_streak_of_empty_list_is_zero():
    assert analytics.calculate_streak([], "daily") == 0


def test_single_completion_is_a_streak_of_one():
    assert analytics.calculate_streak([datetime(2024, 1, 1)], "daily") == 1


def test_consecutive_days_form_a_streak():
    start = datetime(2024, 1, 1, 8)
    days = [start + timedelta(days=i) for i in range(5)]
    assert analytics.calculate_streak(days, "daily") == 5


def test_a_gap_breaks_the_streak():
    start = datetime(2024, 1, 1, 8)
    # Days 0,1,2  (gap)  4,5  -> longest run is 3.
    days = [start + timedelta(days=i) for i in (0, 1, 2, 4, 5)]
    assert analytics.calculate_streak(days, "daily") == 3


def test_multiple_completions_same_day_count_once():
    day = datetime(2024, 1, 1, 8)
    duplicates = [day, day + timedelta(hours=2), day + timedelta(hours=5)]
    assert analytics.calculate_streak(duplicates, "daily") == 1


def test_weekly_streak_counts_consecutive_weeks():
    base = datetime(2024, 1, 1, 8)  # a Monday
    weeks = [base + timedelta(weeks=i, days=2) for i in range(4)]
    assert analytics.calculate_streak(weeks, "weekly") == 4


def test_weekly_streak_breaks_on_missed_week():
    base = datetime(2024, 1, 1, 8)
    # Weeks 0, 1, (skip 2), 3 -> longest run is 2.
    weeks = [base + timedelta(weeks=i, days=1) for i in (0, 1, 3)]
    assert analytics.calculate_streak(weeks, "weekly") == 2


def test_fixture_per_habit_streaks(seeded_service):
    for habit in seeded_service.get_all_habits():
        assert seeded_service.get_longest_streak(habit.id) == \
            EXPECTED_STREAKS[habit.name]


def test_fixture_longest_streak_all(seeded_service):
    assert seeded_service.get_longest_streak_all() == EXPECTED_LONGEST_STREAK_ALL
