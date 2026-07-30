"""Entry point for the Habit Tracker command-line application.

Run it with::

    python main.py            # use the persistent database (habits.db)
    python main.py --seed     # load the 5 predefined habits + 4 weeks of data
    python main.py --db PATH   # use a custom database file

On first run against an empty database the program offers to load the sample
data so there is something to explore immediately.
"""

from __future__ import annotations

import argparse

import fixtures
from cli import CLI
from database import HabitRepository
from service import HabitService


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="A CLI habit tracker.")
    parser.add_argument(
        "--db",
        default="habits.db",
        help="Path to the SQLite database file (default: habits.db).",
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Load the 5 predefined habits with 4 weeks of example data.",
    )
    return parser.parse_args()


def main() -> None:
    """Wire the layers together and start the interactive CLI."""
    args = _parse_args()
    repository = HabitRepository(args.db)
    service = HabitService(repository)

    try:
        if args.seed:
            fixtures.seed(repository)
            print("\u2713 Sample data loaded.")
        elif not service.get_all_habits():
            answer = input("Database is empty. Load sample data? (y/n): ")
            if answer.strip().lower() == "y":
                fixtures.seed(repository)
                print("\u2713 Sample data loaded.")

        CLI(service).run()
    finally:
        repository.close()


if __name__ == "__main__":
    main()
