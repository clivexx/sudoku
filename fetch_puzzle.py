"""
Module: fetch_puzzle.py
Created: 2026-03-21
Purpose: Browser-based puzzle fetcher for NYT and Guardian sudoku
Status: needs testing
Dependencies: PyQt5, PyQtWebEngine, shared/sudoku_library.py
See also: run_sudoku_complete.py
"""

import sys
import json
import re
import subprocess
from pathlib import Path as _Path

sys.path.insert(0, str(_Path(__file__).parent / "shared"))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QLineEdit, QPushButton,
    QLabel, QComboBox, QDialog, QToolBar,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QPainter, QColor, QFont, QPen

from sudoku_library import CustomPuzzleLibrary


FAVORITES = [
    ("NYT Sudoku", "https://www.nytimes.com/puzzles/sudoku"),
]

DIFFICULTY_OPTIONS = ["Easy", "Medium", "Hard", "Expert"]

NYT_JS = "JSON.stringify(window.gameData || null)"

GUARDIAN_JS = r"""
(function() {
    var result = {debug: [], data: null};
    result.debug.push("URL: " + window.location.href);

    // 1. Check for iframes - Guardian interactive puzzles often use interactive.guim.co.uk
    var iframes = document.querySelectorAll("iframe");
    result.debug.push("Iframes found: " + iframes.length);
    for (var fi = 0; fi < iframes.length; fi++) {
        result.debug.push("  iframe[" + fi + "] src: " + (iframes[fi].src || iframes[fi].getAttribute("data-src") || "(no src)"));
    }

    // 2. Dump window.guardian.config.page keys (Guardian DCR passes all page data here)
    if (window.guardian && window.guardian.config && window.guardian.config.page) {
        var page = window.guardian.config.page;
        result.debug.push("guardian.config.page keys: " + Object.keys(page).join(", "));
        // Look for puzzle/sudoku related keys
        var pageStr = JSON.stringify(page);
        var sudokuIdx = pageStr.toLowerCase().indexOf("sudoku");
        if (sudokuIdx >= 0) {
            result.debug.push("'sudoku' found in page at idx " + sudokuIdx + ": " + pageStr.substring(Math.max(0,sudokuIdx-20), sudokuIdx+200));
        }
        var puzzleIdx = pageStr.toLowerCase().indexOf("puzzle");
        if (puzzleIdx >= 0) {
            result.debug.push("'puzzle' found in page at idx " + puzzleIdx + ": " + pageStr.substring(Math.max(0,puzzleIdx-20), puzzleIdx+200));
        }
    }

    // 3. Check common React/Redux global state vars
    var globals = ["__PRELOADED_STATE__", "__REDUX_STATE__", "__NEXT_DATA__", "CAPI_DATA", "__guardian__", "DOTCOM_RENDERING"];
    for (var gi = 0; gi < globals.length; gi++) {
        if (window[globals[gi]]) {
            var s = JSON.stringify(window[globals[gi]]);
            result.debug.push("window." + globals[gi] + " found, length: " + s.length + ", starts: " + s.substring(0, 200));
        }
    }

    // 4. Search ALL globals for anything containing 81-element arrays of small integers (0-9)
    var globalKeys = Object.keys(window);
    result.debug.push("Scanning " + globalKeys.length + " window globals for puzzle data...");
    for (var k = 0; k < globalKeys.length; k++) {
        try {
            var val = window[globalKeys[k]];
            if (val && typeof val === "object") {
                var s = JSON.stringify(val);
                if (s && s.length > 100 && s.length < 2000) {
                    var nums = s.match(/\b[0-9]\b/g);
                    if (nums && nums.length >= 81) {
                        result.debug.push("Candidate global: window." + globalKeys[k] + " (" + s.length + " chars): " + s.substring(0, 300));
                    }
                }
            }
        } catch(e) {}
    }

    // 5. Guardian-specific DOM selectors
    var selectors = [
        "[data-gu-name]", "[data-component*=sudoku]", "[data-component*=puzzle]",
        "[id*=sudoku]", "[id*=puzzle]", "[class*=sudoku]",
        ".crossword__grid", ".sudoku", ".puzzle",
        "[data-interactive]", "figure[data-interactive]"
    ];
    for (var si = 0; si < selectors.length; si++) {
        var els = document.querySelectorAll(selectors[si]);
        if (els.length > 0) {
            result.debug.push("Selector '" + selectors[si] + "': " + els.length + " els, first outerHTML: " + els[0].outerHTML.substring(0, 300));
        }
    }

    result.debug.push("--- end ---");
    return JSON.stringify(result);
})()
"""

def detect_site(url: str) -> str | None:
    if "nytimes.com/puzzles/sudoku" in url:
        return "nyt"
    if "theguardian.com" in url and "sudoku" in url:
        return "guardian"
    return None


def extract_nyt(data: dict, url: str = "") -> tuple[str, str, str]:
    difficulty_map = {"easy": "Easy", "medium": "Medium", "hard": "Hard"}
    url_lower = url.lower()
    preferred = next((k for k in ("easy", "medium", "hard") if k in url_lower), None)
    keys = ([preferred] + [k for k in ("easy", "medium", "hard") if k != preferred]
            if preferred else ["easy", "medium", "hard"])
    for key in keys:
        if key not in data:
            continue
        puzzle = data[key].get("puzzle_data", {}).get("puzzle", [])
        if len(puzzle) == 81:
            puzzle_str = "".join(str(n) for n in puzzle)
            print_date = data[key].get("print_date", "")
            title = f"NYT {key.title()} - {print_date}" if print_date else f"NYT {key.title()}"
            return puzzle_str, difficulty_map[key], title
    raise ValueError("Could not find puzzle data in NYT gameData")


def extract_guardian(data, url: str) -> tuple[str, str, str]:
    difficulty = "Medium"
    puzzle_number = ""
    match = re.search(r"sudoku-(\d+)-?(easy|medium|hard|difficult)?", url, re.IGNORECASE)
    if match:
        puzzle_number = match.group(1)
        diff_str = (match.group(2) or "").lower()
        difficulty_map = {"easy": "Easy", "medium": "Medium", "hard": "Hard", "difficult": "Hard"}
        difficulty = difficulty_map.get(diff_str, "Medium")
    puzzle = None
    if isinstance(data, list) and len(data) == 81:
        puzzle = data
    elif isinstance(data, dict):
        for key in ("puzzle", "grid", "cells", "data"):
            v = data.get(key)
            if isinstance(v, list) and len(v) == 81:
                puzzle = v
                break
    if puzzle is None:
        raise ValueError("Could not find 81-cell array in Guardian data")
    puzzle_str = "".join(str(n) for n in puzzle)
    title = f"Guardian {difficulty} #{puzzle_number}" if puzzle_number else f"Guardian {difficulty}"
    return puzzle_str, difficulty, title


def launch_player(puzzle_name: str):
    player = _Path(__file__).parent / "run_sudoku_complete.py"
    subprocess.Popen([sys.executable, str(player), "--puzzle", puzzle_name])

class MiniGridWidget(QWidget):

    def __init__(self, puzzle_str: str, parent=None):
        super().__init__(parent)
        self.puzzle_str = puzzle_str
        self.setFixedSize(198, 198)

    def paintEvent(self, event):
        painter = QPainter(self)
        cell = 20
        off = 9
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 8))
        for row in range(9):
            for col in range(9):
                x = off + col * cell
                y = off + row * cell
                if ((row // 3) + (col // 3)) % 2 == 0:
                    painter.fillRect(x, y, cell, cell, QColor(235, 235, 235))
                idx = row * 9 + col
                if idx < len(self.puzzle_str) and self.puzzle_str[idx] != "0":
                    painter.setPen(QColor(0, 0, 0))
                    painter.drawText(x, y, cell, cell, Qt.AlignmentFlag.AlignCenter, self.puzzle_str[idx])
        painter.setPen(QPen(QColor(190, 190, 190), 1))
        for i in range(10):
            painter.drawLine(off + i * cell, off, off + i * cell, off + 9 * cell)
            painter.drawLine(off, off + i * cell, off + 9 * cell, off + i * cell)
        painter.setPen(QPen(QColor(60, 60, 60), 2))
        for i in range(0, 10, 3):
            painter.drawLine(off + i * cell, off, off + i * cell, off + 9 * cell)
            painter.drawLine(off, off + i * cell, off + 9 * cell, off + i * cell)


class SavePuzzleDialog(QDialog):

    def __init__(self, puzzle_str: str, title: str, difficulty: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Puzzle")
        self.action = "cancel"
        self._setup_ui(puzzle_str, title, difficulty)

    def _setup_ui(self, puzzle_str: str, title: str, difficulty: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        preview_row = QHBoxLayout()
        preview_row.addStretch()
        preview_row.addWidget(MiniGridWidget(puzzle_str))
        preview_row.addStretch()
        layout.addLayout(preview_row)
        title_row = QHBoxLayout()
        title_row.addWidget(QLabel("Title:"))
        self.title_edit = QLineEdit(title)
        self.title_edit.setMinimumWidth(240)
        title_row.addWidget(self.title_edit)
        layout.addLayout(title_row)
        diff_row = QHBoxLayout()
        diff_row.addWidget(QLabel("Difficulty:"))
        self.diff_combo = QComboBox()
        self.diff_combo.addItems(DIFFICULTY_OPTIONS)
        idx = DIFFICULTY_OPTIONS.index(difficulty) if difficulty in DIFFICULTY_OPTIONS else 1
        self.diff_combo.setCurrentIndex(idx)
        diff_row.addWidget(self.diff_combo)
        diff_row.addStretch()
        layout.addLayout(diff_row)
        btn_row = QHBoxLayout()
        btn_cancel    = QPushButton("Cancel")
        btn_save      = QPushButton("Save")
        btn_save_play = QPushButton("Save && Play")
        btn_save_play.setDefault(True)
        btn_cancel.clicked.connect(self.reject)
        btn_save.clicked.connect(lambda: self._finish("save"))
        btn_save_play.clicked.connect(lambda: self._finish("save_and_play"))
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_save_play)
        layout.addLayout(btn_row)

    def _finish(self, action: str):
        self.action = action
        self.accept()

    def get_result(self) -> tuple[str, str, str]:
        return self.title_edit.text().strip(), self.diff_combo.currentText(), self.action

class FetchPuzzleWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("")
        self.resize(1100, 760)
        self._setup_ui()

    def _setup_ui(self):
        # --- Toolbar (spans full window width) ---
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.btn_back    = QPushButton("Back"); self.btn_back.setFixedWidth(44)
        self.btn_forward = QPushButton("Fwd");  self.btn_forward.setFixedWidth(44)
        self.btn_reload  = QPushButton("R");    self.btn_reload.setFixedWidth(30)
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL...")
        self.url_bar.returnPressed.connect(self._on_url_entered)
        btn_go = QPushButton("Go")
        btn_go.setFixedWidth(36)
        btn_go.clicked.connect(self._on_url_entered)
        self.btn_extract = QPushButton("Extract Puzzle")
        self.btn_extract.setStyleSheet(
            "QPushButton { background: #0078d4; color: white; padding: 4px 16px;"
            " border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background: #005fa3; }"
        )
        self.btn_extract.clicked.connect(self._on_extract_clicked)
        self.btn_back.clicked.connect(lambda: self.browser.back())
        self.btn_forward.clicked.connect(lambda: self.browser.forward())
        self.btn_reload.clicked.connect(lambda: self.browser.reload())
        for w in (self.btn_back, self.btn_forward, self.btn_reload):
            toolbar.addWidget(w)
        toolbar.addWidget(self.url_bar)
        toolbar.addWidget(btn_go)
        toolbar.addSeparator()
        toolbar.addWidget(self.btn_extract)
        self.addToolBar(toolbar)

        # --- Central widget: sidebar + browser ---
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QWidget()
        sidebar.setFixedWidth(140)
        sidebar.setStyleSheet("background: white; border-right: 1px solid #d0d0d0;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 8, 0, 0)
        sidebar_layout.setSpacing(0)
        fav_label = QLabel("Favorites")
        fav_label.setStyleSheet("color: #555; font-size: 11px; padding: 4px 10px 6px 10px;")
        sidebar_layout.addWidget(fav_label)
        self.favorites_list = QListWidget()
        self.favorites_list.setStyleSheet(
            "QListWidget { background: white; color: black; border: none; font-size: 13px; }"
            " QListWidget::item { padding: 8px 10px; }"
            " QListWidget::item:hover { background: #e8f0fe; }"
            " QListWidget::item:selected { background: #0078d4; color: white; }"
        )
        for name, url in FAVORITES:
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, url)
            self.favorites_list.addItem(item)
        self.favorites_list.itemClicked.connect(self._on_favorite_clicked)
        sidebar_layout.addWidget(self.favorites_list)
        main_layout.addWidget(sidebar)

        self.browser = QWebEngineView()
        self.browser.setZoomFactor(0.5)
        self.browser.urlChanged.connect(lambda url: self.url_bar.setText(url.toString()))
        self.browser.loadFinished.connect(self._on_load_finished)
        main_layout.addWidget(self.browser)
        self.statusBar().showMessage("Ready")

    def _on_load_finished(self, ok: bool):
        self.browser.setZoomFactor(0.5)
        self.statusBar().showMessage("Page loaded" if ok else "Load failed")

    def _on_favorite_clicked(self, item: QListWidgetItem):
        self.browser.load(QUrl(item.data(Qt.ItemDataRole.UserRole)))

    def _on_url_entered(self):
        url = self.url_bar.text().strip()
        if not url.startswith("http"):
            url = "https://" + url
        self.browser.load(QUrl(url))

    def _on_extract_clicked(self):
        url = self.browser.url().toString()
        site = detect_site(url)
        print(f"[extract] URL: {url}")
        print(f"[extract] Site detected: {site}")
        if site == "nyt":
            print("[extract] Running NYT JS...")
            self.browser.page().runJavaScript(
                NYT_JS, lambda r: self._on_js_result(r, url, "nyt")
            )
        elif site == "guardian":
            print("[extract] Running Guardian JS...")
            self.browser.page().runJavaScript(
                GUARDIAN_JS, lambda r: self._on_js_result(r, url, "guardian")
            )
        else:
            print("[extract] Unknown site, cannot extract")
            self.statusBar().showMessage("Unknown site - cannot extract from this page")

    def _on_js_result(self, result, url: str, site: str):
        print(f"[js_result] site={site}, result type={type(result).__name__}")
        if result is None:
            print("[js_result] result is None")
            self.statusBar().showMessage("No puzzle data found - navigate to a specific puzzle page")
            return
        try:
            data = json.loads(result) if isinstance(result, str) else result
            if site == "guardian":
                if isinstance(data, dict) and "debug" in data:
                    for line in data.get("debug", []):
                        print(f"[guardian] {line}")
                    data = data.get("data")
                    print(f"[guardian] data type: {type(data).__name__}, value: {str(data)[:200]}")
            if site == "nyt":
                puzzle_str, difficulty, title = extract_nyt(data, url)
            else:
                puzzle_str, difficulty, title = extract_guardian(data, url)
            self._show_save_dialog(puzzle_str, title, difficulty)
        except Exception as e:
            print(f"[js_result] Exception: {e}")
            self.statusBar().showMessage(f"Extraction failed: {e}")

    def _show_save_dialog(self, puzzle_str: str, title: str, difficulty: str):
        dlg = SavePuzzleDialog(puzzle_str, title, difficulty, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            title, difficulty, action = dlg.get_result()
            CustomPuzzleLibrary.add_puzzle(title, puzzle_str, difficulty)
            self.statusBar().showMessage(f"Saved: {title}")
            if action == "save_and_play":
                launch_player(title)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = FetchPuzzleWindow()
    window.show()
    sys.exit(app.exec())
