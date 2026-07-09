# Project: Sudoku

> Read `C:\Users\hp\OneDrive\Desktop\python_stuff\global_claude.md` immediately without asking - it contains session startup instructions.

**Updated:** 2026-07-09 (session end)
**Status:** In Progress

## What This Is
Interactive Sudoku player with hints and puzzle library

## Tech Stack
- Python 3 + PyQt6
- Entry points: `run_sudoku_complete.py` (main player), `run_sudoku_solver.py` (technique
  research tool), `run_generator.py` (puzzle generator), `fetch_puzzle.py` (web puzzle
  importer, needs PyQt6-WebEngine)
- Shared logic in `shared/` (solver, analyzer, library — no Qt dependency), shared widgets
  in `player/` (grid, cell)

## Current State
- Restored from a dead PC; migrated from PyQt5 to PyQt6 since only PyQt6 was installed.
- `run_sudoku_complete.py` confirmed working by user.
- `fetch_puzzle.py` NYT extraction confirmed working; favorite now points at the puzzle
  chooser page (`/puzzles/sudoku`) rather than direct difficulty links, which avoids a
  cookie-consent overlay that blocked `window.gameData` from loading.
- `run_sudoku_solver.py`, `run_generator.py` launch without crashing; full interactive
  testing still in progress.
- `player/sudoku_player.py`, `fetch_puzzle_backup.py`, `_patch.py`, `_write_helper.py` are
  unused/backup files, still on PyQt5, not part of the live app.
- Git repo initialized and pushed to `origin/main`
  (`https://github.com/clivexx/sudoku.git`).

## Next Steps
1. Finish testing solver/generator interactive paths for stray PyQt5-style unscoped enums
2. Guardian sudoku extraction is abandoned — `GUARDIAN_JS`/`extract_guardian` in
   `fetch_puzzle.py` are now dead code; consider removing

## Setup
```
pip install PyQt6 PyQt6-WebEngine
python run_sudoku_complete.py
```

## Notes
- This app is PyQt6, not PyQt5. All enum access must be fully qualified
  (`Qt.AlignmentFlag.AlignCenter`, `Qt.GlobalColor.black`, `QFont.Weight.Bold`, etc.) —
  PyQt6 dropped the unscoped shortcuts PyQt5 allowed via sip. If you hit
  `AttributeError: type object 'X' has no attribute 'Y'` on a Qt class, that's almost
  certainly the cause.
- `QWebEngineView` in `fetch_puzzle.py` sometimes doesn't repaint a loaded page until the
  pane is clicked — a Chromium/Qt compositing quirk on Windows, not a functional bug. If a
  page looks blank, click into it before assuming the load failed.
