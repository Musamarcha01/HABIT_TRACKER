"""Shared pytest fixtures for the Habit Tracker test suite.

A fixed Monday start date makes the seeded example data — and every streak the
tests assert against — deterministic, regardless of the day the tests run.
"""

from __future__ import annotations

import os
import sys
from datetime import date

import pytest

# Make the project modules importable when pytest runs from the repo root.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import fixtures  # noqa: E402
from database import HabitRepository  # noqa: E402
from service import HabitService  # noqa: E402

# A fixed Monday so weekly grouping and streaks are reproducible.
FIXED_START = date(2024, 1, 1)  # 1 Jan 2024 is a Monday.


@pytest.fixture
def repository():
    """An empty in-memory repository, isolated per test."""
    repo = HabitRepository(":memory:")
    yield repo
    repo.close()


@pytest.fixture
def service(repository):
    """A service backed by an empty in-memory repository."""
    return HabitService(repository)


@pytest.fixture
def seeded_repository(repository):
    """An in-memory repository preloaded with the 4-week example fixture."""
    fixtures.seed(repository, start=FIXED_START)
    return repository


@pytest.fixture
def seeded_service(seeded_repository):
    """A service backed by the preloaded example fixture."""
    return HabitService(seeded_repository)
