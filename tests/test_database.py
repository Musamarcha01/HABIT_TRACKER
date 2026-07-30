"""Unit tests for the repository (data layer) and service (application layer)."""

from __future__ import annotations

from datetime import date

import pytest

from habit import Habit

# A fixed Monday so seeding is reproducible (matches conftest.py).
FIXED_START = date(2024, 1, 1)


def test_add_and_retrieve_habit(repository):
    habit = Habit("Exercise", "daily")
    repository.add_habit(habit)
    assert repository.get_habit_by_id(habit.id) == habit
    assert repository.get_habit_by_name("Exercise") == habit


def test_duplicate_name_is_rejected(repository):
    repository.add_habit(Habit("Exercise", "daily"))
    with pytest.raises(ValueError):
        repository.add_habit(Habit("Exercise", "weekly"))


def test_completions_are_stored_and_ordered(repository):
    habit = Habit("Exercise", "daily")
    repository.add_habit(habit)
    repository.add_completion(habit.id)
    repository.add_completion(habit.id)
    assert len(repository.get_completions(habit.id)) == 2


def test_completion_for_unknown_habit_raises(repository):
    with pytest.raises(ValueError):
        repository.add_completion("does-not-exist")


def test_delete_cascades_to_completions(repository):
    habit = Habit("Exercise", "daily")
    repository.add_habit(habit)
    repository.add_completion(habit.id)
    assert repository.delete_habit(habit.id) is True
    assert repository.get_habit_by_id(habit.id) is None
    # Completions must be gone too (ON DELETE CASCADE).
    assert repository.get_completions(habit.id) == []


def test_delete_missing_habit_returns_false(repository):
    assert repository.delete_habit("nope") is False


def test_service_creates_and_lists(service):
    service.create_habit("Read", "daily")
    service.create_habit("Review", "weekly")
    assert len(service.get_all_habits()) == 2


def test_service_rejects_bad_periodicity(service):
    with pytest.raises(ValueError):
        service.create_habit("Read", "yearly")


def test_service_filters_by_periodicity(service):
    service.create_habit("Read", "daily")
    service.create_habit("Review", "weekly")
    daily = service.get_habits_by_periodicity("daily")
    assert len(daily) == 1 and daily[0].name == "Read"


def test_seeded_service_has_five_habits(seeded_service):
    assert len(seeded_service.get_all_habits()) == 5


def test_seeding_is_idempotent(seeded_repository):
    import fixtures

    fixtures.seed(seeded_repository, start=FIXED_START)  # seed again
    assert len(seeded_repository.get_habits()) == 5  # no duplicates
