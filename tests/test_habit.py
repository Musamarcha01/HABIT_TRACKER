"""Unit tests for the Habit domain model."""

from __future__ import annotations

from datetime import datetime

import pytest

from habit import Habit


def test_habit_creation_sets_fields():
    habit = Habit("Read", "daily")
    assert habit.name == "Read"
    assert habit.periodicity == "daily"
    assert isinstance(habit.created_at, datetime)
    assert len(habit.id) == 32  # uuid4 hex


def test_each_habit_gets_a_unique_id():
    assert Habit("A", "daily").id != Habit("B", "daily").id


def test_empty_name_is_rejected():
    with pytest.raises(ValueError):
        Habit("   ", "daily")


def test_invalid_periodicity_is_rejected():
    with pytest.raises(ValueError):
        Habit("Read", "monthly")


def test_round_trip_through_dict_and_row():
    habit = Habit("Meditate", "weekly")
    row = (habit.id, habit.name, habit.periodicity, habit.created_at.isoformat())
    rebuilt = Habit.from_row(row)
    assert rebuilt == habit  # equal by id
    assert rebuilt.to_dict()["periodicity"] == "weekly"
