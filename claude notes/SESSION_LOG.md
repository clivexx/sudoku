# Session Log

---

## 2026-07-08 - Restore project after dead PC, migrate PyQt5 → PyQt6

**Files modified:**
- `run_sudoku_complete.py`, `run_sudoku_solver.py`, `run_generator.py`, `fetch_puzzle.py`,
  `player/sudoku_cell.py`, `player/sudoku_grid.py` - ported from PyQt5 to PyQt6 (working)

**Context:**
- Project restored from a dead PC; code was intact, but the whole app was written against
  PyQt5, while only PyQt6 was installed (per global standard). Chose to migrate rather than
  install PyQt5 alongside.
- Migration: `PyQt5` → `PyQt6` imports, `QAction` moved from `QtWidgets` to `QtGui`,
  `.exec_()` → `.exec()`, and all unscoped enums qualified (e.g. `Qt.AlignCenter` →
  `Qt.AlignmentFlag.AlignCenter`, `Qt.black` → `Qt.GlobalColor.black`, `QFont.Bold` →
  `QFont.Weight.Bold`, etc.) — PyQt6 removed the PyQt5 backward-compat shortcuts for these.
- Left `player/sudoku_player.py`, `fetch_puzzle_backup.py`, `_patch.py`, `_write_helper.py`
  untouched — not imported by any live entry point, so out of scope.

**Status:** User confirmed `run_sudoku_complete.py` works after fixing a `Qt.black` enum
miss in `sudoku_grid.py`. `run_sudoku_solver.py`, `run_generator.py`, `fetch_puzzle.py`
launch without crashing; user was mid-testing these when session ended.

**Next steps:**
- Finish exercising solver/generator/fetch_puzzle dialogs — any interactive code path not
  yet clicked could still have an unqualified PyQt5-style enum lurking.
- No git repo yet in this project — consider `git init` if version history is wanted.
