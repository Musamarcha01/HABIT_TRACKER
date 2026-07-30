# Habit Tracker

A command-line habit-tracking backend written in Python, built for the IU
course *Object Oriented and Functional Programming with Python*
(DLBDSOOFPP01). It lets a user define habits, check them off over time, and
analyse their behaviour — combining **object-oriented programming** for the
data model with the **functional programming** paradigm for the analytics.

There is no graphical interface: the application is a clean, menu-driven CLI,
exactly as the task requires.

---

## Features

- Create daily or weekly habits, each with a unique id and a creation timestamp.
- Check off (complete) a habit at any time; every completion is timestamped and stored.
- Delete a habit, which also removes its completion history (cascade delete).
- Persistent storage in a local SQLite database, so data survives between sessions.
- A functional analytics module that can:
  - list all currently tracked habits,
  - list all habits with the same periodicity,
  - return the longest run streak across all habits,
  - return the longest run streak for a single habit,
  - rank the habits the user struggled with most.
- Ships with **5 predefined habits** and **4 weeks of example data**, usable as a demo and as an automated test fixture.
- A full unit-test suite written with `pytest`.

---

## Requirements

- Python 3.7 or later (developed and tested on Python 3.13).
- No third-party libraries are needed to run the app — it uses only the Python
  standard library (`sqlite3`, `datetime`, `uuid`, `functools`, `argparse`).
- `pytest` is required only to run the automated tests.

---

## Installation

1. Download or clone this repository:

   ```
   git clone https://github.com/Musamarcha01/HABIT_TRACKER.git
   cd HABIT_TRACKER
   ```

2. (Optional but recommended) create and activate a virtual environment:

   ```
   python -m venv venv
   venv\Scripts\activate       # on Windows
   source venv/bin/activate    # on macOS / Linux
   ```

3. Install the test dependency:

   ```
   pip install -r requirements.txt
   ```

---

## Running the application

From the project folder, start the program with:

```
python main.py
```

On the first run the database is empty, so the program offers to load the
sample data. Type `y` to load the 5 predefined habits with their 4 weeks of
history. You can also force this at any time:

```
python main.py --seed
```

You will then see the main menu:

```
=== HABIT TRACKER ===
1) Create Habit
2) List Habits
3) Complete Habit
4) Delete Habit
5) View Analytics
6) Load Sample Data
7) Exit
```

Type the number of the option you want and press Enter.

### Creating a habit

Choose `1`, enter a name (for example `Drink Water`), then a period —
either `daily` or `weekly`. Invalid names or periods are rejected with a clear
message, so the app never crashes on bad input.

### Completing a habit

Choose `3`, then pick the habit from the numbered list. The current date and
time are recorded automatically as a completion.

### Viewing analytics

Choose `5` to see the longest streak across all habits, your current daily and
weekly habits, the longest streak for each habit, and which habits you have
struggled with most.

---

## Predefined habits and example data

The application seeds the following five habits, each with four weeks of
example completions. The data is deliberately shaped to produce known streaks,
which the automated tests verify:

| Habit             | Period  | Longest streak |
|-------------------|---------|----------------|
| Morning Exercise  | daily   | 14 days        |
| Read 30 Minutes   | daily   | 13 days        |
| Drink 2L Water    | daily   | 7 days         |
| Meditation        | daily   | 6 days         |
| Weekly Review     | weekly  | 4 weeks        |

The longest streak across all habits is therefore 14.

---

## Running the tests

The critical components — the habit model, the analytics functions and the
data layer — are covered by a `pytest` suite. From the project folder run:

```
python -m pytest
```

All tests should pass. Each test uses an isolated in-memory database, so
running them never touches your real `habits.db` file.

---

## Project structure

```
HABIT_TRACKER/
├── habit.py           # Habit class — the object-oriented domain model
├── database.py        # HabitRepository — the SQLite data-access layer
├── analytics.py       # Pure functional analytics (map / filter / reduce)
├── service.py         # HabitService — application / business logic
├── cli.py             # Command-line interface (presentation layer)
├── fixtures.py        # 5 predefined habits + 4 weeks of example data
├── main.py            # Entry point
├── requirements.txt   # Test dependency (pytest)
├── pytest.ini         # pytest configuration
├── README.md          # This file
└── tests/             # Automated pytest suite
    ├── conftest.py
    ├── test_habit.py
    ├── test_analytics.py
    └── test_database.py
```

---

## Design overview

The project follows a **layered architecture** so each concern is isolated and
independently testable:

- **Presentation layer (`cli.py`)** — renders the menu and reads user input; it
  contains no business rules and no SQL.
- **Application layer (`service.py`)** — the `HabitService` orchestrates
  operations, enforces business rules (such as preventing duplicate names) and
  connects the CLI to the layers below.
- **Domain layer (`habit.py`)** — the `Habit` class encapsulates a habit's data
  and its own validation, using object-oriented programming.
- **Analytics (`analytics.py`)** — pure functions implemented with `map`,
  `filter` and `functools.reduce`, following the functional paradigm. They take
  data as input and return results with no side effects.
- **Data layer (`database.py`)** — the `HabitRepository` is the only component
  that talks to SQLite, hiding all queries behind clear method names.

### Why these choices

- **SQLite** was chosen for persistence because it is built into Python,
  requires zero configuration, is file-based (easy to share and inspect), and
  enforces relational integrity through foreign-key constraints.
- **Object-oriented programming** models the real-world concept of a habit as a
  self-contained object with data and behaviour.
- **Functional programming** suits the analytics: transforming and aggregating
  lists of completions is expressed cleanly and without side effects using
  `map`, `filter` and `reduce`.

### How streaks are calculated

A streak is a run of consecutive periods completed without a break. Daily
streaks count consecutive calendar days; weekly streaks normalise each
completion to the Monday of its week, which makes consecutive-week detection
correct even across month and year boundaries. Multiple completions within the
same period count once.

---

## Author

Musa Yerima Marcha — IU International University of Applied Sciences,
DLBDSOOFPP01 portfolio.
