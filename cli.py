"""Command-line interface for the Habit Tracker.

:class:`CLI` is the presentation layer. It renders an interactive text menu,
reads user input with the built-in :func:`input`, and delegates every action
to a :class:`~service.HabitService`. It contains no business rules and no SQL —
its only job is to talk to the user.
"""

from __future__ import annotations

from typing import Callable, List, Optional

from habit import VALID_PERIODICITIES, Habit
from service import HabitService

_MENU = """
=== HABIT TRACKER ===
1) Create Habit
2) List Habits
3) Complete Habit
4) Delete Habit
5) View Analytics
6) Load Sample Data
7) Exit
"""


class CLI:
    """Interactive menu-driven front end for the habit tracker."""

    def __init__(
        self,
        service: HabitService,
        input_func: Callable[[str], str] = input,
        output_func: Callable[[str], None] = print,
    ) -> None:
        """Create the CLI.

        Args:
            service: The application service to delegate to.
            input_func: Function used to read a line of input. Injectable so
                the CLI can be driven in tests without real keyboard input.
            output_func: Function used to write a line of output.
        """
        self._service = service
        self._input = input_func
        self._output = output_func

    # ------------------------------------------------------------------ #
    # Main loop
    # ------------------------------------------------------------------ #
    def run(self) -> None:
        """Display the menu and dispatch choices until the user exits."""
        actions = {
            "1": self._create_habit,
            "2": self._list_habits,
            "3": self._complete_habit,
            "4": self._delete_habit,
            "5": self._view_analytics,
            "6": self._load_sample_data,
        }
        while True:
            self._output(_MENU)
            choice = self._input("> Select: ").strip()
            if choice == "7":
                self._output("Goodbye!")
                return
            action = actions.get(choice)
            if action is None:
                self._output("Invalid choice. Please pick a number from the menu.")
                continue
            action()

    # ------------------------------------------------------------------ #
    # Menu actions
    # ------------------------------------------------------------------ #
    def _create_habit(self) -> None:
        name = self._input("Habit name: ").strip()
        periodicity = self._input("Period (daily/weekly): ").strip().lower()
        try:
            habit = self._service.create_habit(name, periodicity)
        except ValueError as error:
            self._output(f"Could not create habit: {error}")
            return
        self._output(f"\u2713 Habit '{habit.name}' created!")

    def _list_habits(self) -> None:
        habits = self._service.get_all_habits()
        if not habits:
            self._output("No habits yet. Create one or load the sample data.")
            return
        self._output("\nYour habits:")
        self._render_habit_table(habits)

    def _complete_habit(self) -> None:
        habit = self._prompt_for_habit("complete")
        if habit is None:
            return
        self._service.complete_habit(habit.id)
        self._output(f"\u2713 '{habit.name}' checked off.")

    def _delete_habit(self) -> None:
        habit = self._prompt_for_habit("delete")
        if habit is None:
            return
        confirm = self._input(
            f"Delete '{habit.name}' and all its history? (y/n): "
        ).strip().lower()
        if confirm == "y":
            self._service.delete_habit(habit.id)
            self._output(f"\u2717 '{habit.name}' deleted.")
        else:
            self._output("Cancelled.")

    def _view_analytics(self) -> None:
        habits = self._service.get_all_habits()
        if not habits:
            self._output("No habits to analyse yet.")
            return

        self._output("\n--- ANALYTICS ---")

        overall = self._service.get_longest_streak_all()
        self._output(f"Longest streak across all habits: {overall} period(s)")

        self._output("\nCurrent daily habits:")
        for habit in self._service.get_habits_by_periodicity("daily"):
            self._output(f"  - {habit.name}")

        self._output("\nCurrent weekly habits:")
        for habit in self._service.get_habits_by_periodicity("weekly"):
            self._output(f"  - {habit.name}")

        self._output("\nLongest streak per habit:")
        for habit in habits:
            streak = self._service.get_longest_streak(habit.id)
            self._output(f"  - {habit.name}: {streak} period(s)")

        self._output("\nHabits you struggled with most:")
        for item in self._service.get_struggling_habits():
            self._output(
                f"  - {item['habit'].name}: {item['breaks']} missed period(s)"
            )

    def _load_sample_data(self) -> None:
        # Imported lazily to avoid a hard dependency when unused.
        import fixtures

        # ``seed`` needs the repository; the service exposes it indirectly, so
        # re-seed through a fresh service bound to the same repository.
        fixtures.seed(self._service._repository)  # noqa: SLF001 (internal wiring)
        self._output("\u2713 Sample data loaded (5 habits, 4 weeks of history).")

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _prompt_for_habit(self, verb: str) -> Optional[Habit]:
        """List habits, ask the user to pick one by number, and return it."""
        habits = self._service.get_all_habits()
        if not habits:
            self._output("No habits available.")
            return None
        self._output(f"\nSelect a habit to {verb}:")
        for index, habit in enumerate(habits, start=1):
            self._output(f"  {index}) {habit.name} ({habit.periodicity})")
        raw = self._input("> Number: ").strip()
        if not raw.isdigit() or not (1 <= int(raw) <= len(habits)):
            self._output("Invalid selection.")
            return None
        return habits[int(raw) - 1]

    def _render_habit_table(self, habits: List[Habit]) -> None:
        """Print a simple aligned table of habits and their streaks."""
        header = f"  {'Name':<20} {'Period':<8} {'Longest streak':<14}"
        self._output(header)
        self._output("  " + "-" * (len(header) - 2))
        for habit in habits:
            streak = self._service.get_longest_streak(habit.id)
            self._output(
                f"  {habit.name:<20} {habit.periodicity:<8} {streak:<14}"
            )
