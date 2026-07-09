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

---

## 2026-07-09 - Fix NYT puzzle fetch (cookie popup) and push first commit

**Files modified:**
- `fetch_puzzle.py` - `FAVORITES` list now points at the NYT sudoku chooser page instead of
  direct `/easy`/`/medium`/`/hard` deep links; dropped the abandoned Guardian favorite
  (working)

**Context:**
- User reported the fetcher couldn't find puzzles on NYT — direct difficulty links loaded
  a cookie-consent overlay that blocked `window.gameData` from populating before
  extraction ran, so `Extract Puzzle` failed. Root cause confirmed interactively: dismissing
  the popup let extraction succeed.
- Landing on the general chooser page (`https://www.nytimes.com/puzzles/sudoku`) lets the
  user click through to a difficulty via NYT's normal flow, avoiding the stuck state.
- Also noticed (not a bug): `QWebEngineView` sometimes doesn't repaint the loaded page
  until the pane receives a click — a known Chromium/Qt compositing quirk on Windows, not a
  loading failure. Confirmed via temporary debug prints that the page and extraction both
  succeed even when the pane looks blank; the prints were removed afterward.
- Guardian extraction code (`GUARDIAN_JS`, `extract_guardian`, `detect_site` branch) is now
  unused dead code left in place — not removed this session, out of scope.

**Status:** Working. Committed (`a1106e8`) and pushed to `origin/main`
(`https://github.com/clivexx/sudoku.git`) — first push since the repo was restored.

**Next steps:**
- Finish exercising solver/generator dialogs for lingering PyQt5-style enum issues
  (carried over from last session).
- Consider removing the now-dead Guardian extraction code from `fetch_puzzle.py` if Guardian
  support stays abandoned.
