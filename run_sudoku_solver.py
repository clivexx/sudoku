#!/usr/bin/env python3
"""
Sudoku Solver Research Tool
Step through puzzle solutions to test and refine hint techniques from sudoku_analyzer.py
"""

import sys
import os

# Setup paths
script_dir = os.path.dirname(os.path.abspath(__file__))
player_dir = os.path.join(script_dir, 'player')
shared_dir = os.path.join(script_dir, 'shared')
sys.path.insert(0, player_dir)
sys.path.insert(0, shared_dir)

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QMessageBox, QFrame, QTextEdit,
                             QGridLayout, QDialog, QRadioButton, QButtonGroup,
                             QScrollArea, QMenu, QPlainTextEdit, QLineEdit,
                             QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QKeyEvent, QAction

from sudoku_grid import SudokuGrid
from sudoku_game import SudokuGame
from sudoku_library import PuzzleLibrary, CustomPuzzleLibrary
from sudoku_solver import SudokuSolver
from sudoku_analyzer import SudokuAnalyzer


# Strategy descriptions for each technique type
STRATEGY_DESCRIPTIONS = {
    'last_remaining': "When only one empty cell remains in a house, fill the missing number",
    'box_hidden_single': "Scanning number by number reveals hidden singles in boxes",
    'rowcol_hidden_single': "Scanning rows/columns with few empty cells reveals hidden singles",
    'hidden_single': "Scanning number by number reveals hidden singles",
    'naked_single': "Noting potential candidates for empty cells reveals naked singles",
    'naked_pair': "Two cells in a house with the same two candidates form a naked pair",
    'naked_triple': "Three cells sharing exactly three candidates form a naked triple",
    'naked_quad': "Four cells sharing exactly four candidates form a naked quad",
    'hidden_pair': "Two candidates appearing in only two cells of a house form a hidden pair",
    'hidden_triple': "Three candidates appearing in only three cells form a hidden triple",
    'hidden_quad': "Four candidates appearing in only four cells form a hidden quad",
    'pointing_pair': "Candidates confined to one row/col within a box point to eliminations",
    'box_line_reduction': "Candidates confined to one box within a row/col allow eliminations",
    'xwing': "Two rows (or cols) with candidates in same two columns form an X-Wing",
    'swordfish': "Three rows with candidates in same three columns form a Swordfish",
    'jellyfish': "Four rows with candidates in same four columns form a Jellyfish",
    'xy_wing': "Three bivalue cells forming a Y pattern allow eliminations",
    'simple_coloring': "Coloring conjugate pairs reveals contradictions or eliminations",
    'forcing_chain': "Following chains of implications reveals forced values"
}


class DifficultyDialog(QDialog):
    """Dialog for selecting puzzle difficulty"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Difficulty")
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("Select Puzzle Difficulty")
        title.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.button_group = QButtonGroup()

        self.beginner_radio = QRadioButton("Beginner")
        self.easy_radio = QRadioButton("Easy")
        self.medium_radio = QRadioButton("Medium")
        self.hard_radio = QRadioButton("Hard")
        self.expert_radio = QRadioButton("Expert")

        for radio in [self.beginner_radio, self.easy_radio, self.medium_radio,
                      self.hard_radio, self.expert_radio]:
            radio.setFont(QFont('Arial', 12))
            self.button_group.addButton(radio)
            layout.addWidget(radio)

        self.medium_radio.setChecked(True)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        self.play_custom_radio = QRadioButton("Play Custom Puzzle")
        self.play_custom_radio.setFont(QFont('Arial', 12))
        self.button_group.addButton(self.play_custom_radio)
        layout.addWidget(self.play_custom_radio)

        start_btn = QPushButton("Continue")
        start_btn.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        start_btn.clicked.connect(self.accept)
        layout.addWidget(start_btn)

        self.setLayout(layout)

    def get_difficulty(self):
        if self.beginner_radio.isChecked():
            return 'Beginner'
        elif self.easy_radio.isChecked():
            return 'Easy'
        elif self.medium_radio.isChecked():
            return 'Medium'
        elif self.hard_radio.isChecked():
            return 'Hard'
        elif self.expert_radio.isChecked():
            return 'Expert'
        elif self.play_custom_radio.isChecked():
            return 'play_custom'
        return 'Medium'


class EnterPuzzleDialog(QDialog):
    """Dialog for entering a custom puzzle string"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter Custom Puzzle")
        self.setModal(True)
        self.puzzle_string = None
        self.puzzle_title = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title_label = QLabel("Description/Title:")
        title_label.setFont(QFont('Arial', 11))
        layout.addWidget(title_label)

        self.title_input = QLineEdit()
        self.title_input.setFont(QFont('Arial', 11))
        self.title_input.setPlaceholderText("e.g., NY Times Hard #42")
        layout.addWidget(self.title_input)

        puzzle_label = QLabel("Puzzle (81 digits, 0 for empty):")
        puzzle_label.setFont(QFont('Arial', 11))
        layout.addWidget(puzzle_label)

        self.puzzle_input = QPlainTextEdit()
        font = QFont('Courier', 14)
        self.puzzle_input.setFont(font)
        from PyQt6.QtGui import QFontMetrics
        fm = QFontMetrics(font)
        char_width = fm.horizontalAdvance('0')
        self.puzzle_input.setFixedWidth(char_width * 9 + 12)
        self.puzzle_input.setFixedHeight(fm.height() * 10 + 10)
        self.puzzle_input.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.puzzle_input.setPlaceholderText("530070000\n600195000\n098000060\n...")
        self.puzzle_input.textChanged.connect(self.update_char_count)
        layout.addWidget(self.puzzle_input)

        self.char_count_label = QLabel("0 / 81 characters")
        self.char_count_label.setFont(QFont('Arial', 10))
        layout.addWidget(self.char_count_label)

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("Load & Save")
        self.ok_btn.setFont(QFont('Arial', 11, QFont.Weight.Bold))
        self.ok_btn.clicked.connect(self.validate_and_accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFont(QFont('Arial', 11))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.setMinimumWidth(300)

    def update_char_count(self):
        puzzle_str = self.get_puzzle_string()
        count = len(puzzle_str)
        self.char_count_label.setText(f"{count} / 81 characters")

    def get_puzzle_string(self) -> str:
        text = self.puzzle_input.toPlainText()
        return ''.join(c for c in text if c.isdigit())

    def validate_and_accept(self):
        title = self.title_input.text().strip()
        puzzle_str = self.get_puzzle_string()

        if not title:
            title = f"Puzzle {len(puzzle_str)}"

        if len(puzzle_str) != 81:
            QMessageBox.warning(self, "Invalid Input",
                f"Puzzle must have exactly 81 digits.\nCurrently: {len(puzzle_str)}")
            return

        board = []
        for i in range(9):
            row = [int(puzzle_str[i*9 + j]) for j in range(9)]
            board.append(row)

        solution_count = SudokuSolver.count_solutions(board, max_count=2)

        if solution_count == 0:
            QMessageBox.warning(self, "Invalid Puzzle", "This puzzle has no solution.")
            return
        elif solution_count > 1:
            QMessageBox.warning(self, "Invalid Puzzle", "This puzzle has multiple solutions.")
            return

        CustomPuzzleLibrary.add_puzzle(title, puzzle_str, 'Custom')

        self.puzzle_string = puzzle_str
        self.puzzle_title = title
        self.accept()

    def get_result(self):
        return self.puzzle_string, self.puzzle_title


class PlayCustomPuzzleDialog(QDialog):
    """Dialog for selecting a custom puzzle to play"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Custom Puzzle")
        self.setModal(True)
        self.selected_puzzle = None
        self.selected_title = None
        self.puzzles = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title_label = QLabel("Select a Custom Puzzle:")
        title_label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        layout.addWidget(title_label)

        self.puzzles = CustomPuzzleLibrary.load_all()

        self.puzzle_list = QListWidget()
        self.puzzle_list.setFont(QFont('Arial', 11))
        self.puzzle_list.itemDoubleClicked.connect(self.select_and_accept)

        if not self.puzzles:
            self.puzzle_list.addItem("(No custom puzzles saved)")
            self.puzzle_list.setEnabled(False)
        else:
            for title, data in self.puzzles.items():
                status = data.get('status', 'unsolved')
                status_marker = " [solved]" if status == 'solved' else ""
                item = QListWidgetItem(f"{title}{status_marker}")
                item.setData(Qt.ItemDataRole.UserRole, title)
                self.puzzle_list.addItem(item)
            self.puzzle_list.setCurrentRow(0)

        layout.addWidget(self.puzzle_list)

        btn_layout = QHBoxLayout()
        self.play_btn = QPushButton("Load")
        self.play_btn.setFont(QFont('Arial', 11, QFont.Weight.Bold))
        self.play_btn.clicked.connect(self.select_and_accept)
        self.play_btn.setEnabled(bool(self.puzzles))
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFont(QFont('Arial', 11))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.play_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.setMinimumWidth(350)
        self.setMinimumHeight(300)

    def select_and_accept(self):
        current = self.puzzle_list.currentItem()
        if current and self.puzzles:
            title = current.data(Qt.ItemDataRole.UserRole)
            if title and title in self.puzzles:
                self.selected_title = title
                self.selected_puzzle = self.puzzles[title]['puzzle']
                self.accept()

    def get_result(self):
        return self.selected_puzzle, self.selected_title


STATE_OVERVIEW = 'overview'
STATE_EXPLAIN = 'explain'
STATE_EXECUTE = 'execute'


class SudokuSolverWindow(QMainWindow):
    """Research tool for testing hint techniques"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sudoku Solver - Research Tool")
        self.resize(1150, 750)

        self.game = SudokuGame()

        # Working candidates - tracks eliminations across steps
        self.working_candidates = {}  # {(row, col): set of candidates}

        # Track which cells have had candidates revealed
        self.revealed_cells = set()  # {(row, col)}

        # Solver state
        self.state = STATE_OVERVIEW
        self.current_hint = None
        self.hints_applied = 0

        # Options
        self.show_raw_data = True
        self.auto_step = False
        self.auto_step_timer = QTimer()
        self.auto_step_timer.timeout.connect(self.on_step)

        self.init_ui()
        self.create_menu_bar()
        self.select_and_load_puzzle()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout()
        central.setLayout(main_layout)

        left_panel = QVBoxLayout()
        self.grid = SudokuGrid(self)
        left_panel.addWidget(self.grid)
        main_layout.addLayout(left_panel, 2)

        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)

        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        info_frame.setStyleSheet("background-color: #E3F2FD; border-radius: 5px;")
        info_layout = QVBoxLayout(info_frame)

        self.difficulty_label = QLabel("Difficulty: --")
        self.difficulty_label.setFont(QFont('Arial', 11, QFont.Weight.Bold))
        info_layout.addWidget(self.difficulty_label)

        self.progress_label = QLabel("Progress: 0/81 (0%)")
        self.progress_label.setFont(QFont('Arial', 10))
        info_layout.addWidget(self.progress_label)

        right_panel.addWidget(info_frame)

        strategy_frame = QFrame()
        strategy_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        strategy_frame.setStyleSheet("background-color: #E8F5E9; border-radius: 5px;")
        strategy_layout = QVBoxLayout(strategy_frame)

        strategy_title = QLabel("Strategy")
        strategy_title.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        strategy_layout.addWidget(strategy_title)

        self.strategy_label = QLabel("Load a puzzle to begin")
        self.strategy_label.setWordWrap(True)
        self.strategy_label.setFont(QFont('Arial', 10))
        self.strategy_label.setMinimumHeight(50)
        strategy_layout.addWidget(self.strategy_label)

        right_panel.addWidget(strategy_frame)

        self.raw_frame = QFrame()
        self.raw_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        self.raw_frame.setStyleSheet("background-color: #F5F5F5; border-radius: 5px;")
        raw_layout = QVBoxLayout(self.raw_frame)

        raw_title = QLabel("Hint Details (raw dict)")
        raw_title.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        raw_layout.addWidget(raw_title)

        self.raw_text = QTextEdit()
        self.raw_text.setReadOnly(True)
        self.raw_text.setFont(QFont('Courier', 9))
        self.raw_text.setMinimumHeight(120)
        self.raw_text.setMaximumHeight(160)
        raw_layout.addWidget(self.raw_text)

        right_panel.addWidget(self.raw_frame)

        format_frame = QFrame()
        format_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        format_frame.setStyleSheet("background-color: #FFF3E0; border-radius: 5px;")
        format_layout = QVBoxLayout(format_frame)

        format_title = QLabel("Formatted Text")
        format_title.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        format_layout.addWidget(format_title)

        self.format_text = QTextEdit()
        self.format_text.setReadOnly(True)
        self.format_text.setFont(QFont('Arial', 10))
        self.format_text.setMinimumHeight(100)
        self.format_text.setMaximumHeight(140)
        format_layout.addWidget(self.format_text)

        right_panel.addWidget(format_frame)

        right_panel.addStretch()
        main_layout.addLayout(right_panel, 2)

        bottom_layout = QHBoxLayout()

        self.step_btn = QPushButton("STEP (Enter)")
        self.step_btn.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        self.step_btn.setMinimumSize(120, 50)
        self.step_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        self.step_btn.clicked.connect(self.on_step)
        bottom_layout.addWidget(self.step_btn)

        self.hint_count_label = QLabel("Hints: 0")
        self.hint_count_label.setFont(QFont('Arial', 11))
        bottom_layout.addWidget(self.hint_count_label)

        self.state_label = QLabel("State: Overview")
        self.state_label.setFont(QFont('Arial', 11))
        bottom_layout.addWidget(self.state_label)

        bottom_layout.addStretch()

        self.status_label = QLabel("Press Enter or click STEP to begin")
        self.status_label.setFont(QFont('Arial', 10))
        self.status_label.setStyleSheet("color: #666;")
        bottom_layout.addWidget(self.status_label)

        main_v_layout = QVBoxLayout()
        h_container = QWidget()
        h_container.setLayout(main_layout)
        main_v_layout.addWidget(h_container)
        main_v_layout.addLayout(bottom_layout)
        central.setLayout(main_v_layout)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.on_step()
        else:
            super().keyPressEvent(event)

    def create_menu_bar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu('File')

        new_menu = QMenu('New Puzzle', self)
        for diff in ['Beginner', 'Easy', 'Medium', 'Hard', 'Expert']:
            action = new_menu.addAction(diff)
            action.triggered.connect(lambda checked, d=diff: self.load_puzzle_by_difficulty(d))
        file_menu.addMenu(new_menu)

        file_menu.addSeparator()

        enter_action = file_menu.addAction('Enter Custom Puzzle...')
        enter_action.triggered.connect(self.enter_custom_puzzle)

        select_custom_action = file_menu.addAction('Select Custom Puzzle...')
        select_custom_action.triggered.connect(self.select_custom_puzzle)

        file_menu.addSeparator()

        exit_action = file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut('Ctrl+Q')

        options_menu = menubar.addMenu('Options')

        self.show_raw_action = options_menu.addAction('Show Raw Hint Data')
        self.show_raw_action.setCheckable(True)
        self.show_raw_action.setChecked(True)
        self.show_raw_action.triggered.connect(self.toggle_raw_data)

        self.auto_step_action = options_menu.addAction('Auto-step Mode (2s)')
        self.auto_step_action.setCheckable(True)
        self.auto_step_action.setChecked(False)
        self.auto_step_action.triggered.connect(self.toggle_auto_step)

    def toggle_raw_data(self):
        self.show_raw_data = self.show_raw_action.isChecked()
        self.raw_frame.setVisible(self.show_raw_data)

    def toggle_auto_step(self):
        self.auto_step = self.auto_step_action.isChecked()
        if self.auto_step and self.state != STATE_OVERVIEW:
            self.auto_step_timer.start(2000)
        else:
            self.auto_step_timer.stop()

    def select_and_load_puzzle(self):
        dialog = DifficultyDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            choice = dialog.get_difficulty()
            if choice == 'play_custom':
                self.select_custom_puzzle()
            else:
                self.load_puzzle_by_difficulty(choice)

    def load_puzzle_by_difficulty(self, difficulty):
        puzzle_str = PuzzleLibrary.select_puzzle(difficulty)
        if not puzzle_str:
            QMessageBox.warning(self, "No Puzzles", f"No puzzles available for {difficulty}.")
            return
        self.load_puzzle(puzzle_str, difficulty)

    def enter_custom_puzzle(self):
        dialog = EnterPuzzleDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            puzzle_str, title = dialog.get_result()
            if puzzle_str:
                self.load_puzzle(puzzle_str, f'Custom: {title}')

    def select_custom_puzzle(self):
        dialog = PlayCustomPuzzleDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            puzzle_str, title = dialog.get_result()
            if puzzle_str:
                self.load_puzzle(puzzle_str, f'Custom: {title}')

    def load_puzzle(self, puzzle_str, difficulty):
        self.game.start_game_from_string(puzzle_str, difficulty)
        self.difficulty_label.setText(f"Difficulty: {difficulty}")

        self.working_candidates = {}
        for row in range(9):
            for col in range(9):
                if self.game.board[row][col] == 0:
                    cands = SudokuSolver.get_candidates(self.game.board, row, col)
                    self.working_candidates[(row, col)] = cands.copy()

        self.revealed_cells = set()
        self.state = STATE_OVERVIEW
        self.current_hint = None
        self.hints_applied = 0
        self.auto_step_timer.stop()

        self.refresh_grid()

        givens = sum(1 for r in range(9) for c in range(9) if self.game.initial_board[r][c] != 0)
        self.raw_text.setText(f"Puzzle loaded:\n  Givens: {givens}\n  Empty: {81 - givens}")
        self.format_text.setText("Press STEP (or Enter) to find the next hint.\n\n"
                                 "Highlighting:\n"
                                 "  Bold = excluding numbers\n"
                                 "  Green = target cell\n"
                                 "  Yellow = cells with eliminations\n"
                                 "  Pink = where number CAN'T go")
        self.strategy_label.setText("Press STEP to begin solving")
        self.update_display()

    def refresh_grid(self):
        for row in range(9):
            for col in range(9):
                value = self.game.board[row][col]
                is_initial = (self.game.initial_board[row][col] != 0)
                cell = self.grid.cells[row][col]
                cell.set_value(value, is_initial)
                cell.border_highlight = False
                cell.highlight_pattern = False
                cell.highlight_affected = False
                cell.highlight_excluded = False
                cell.is_singleton = False
                cell.is_candidate = False
                cell.is_bold = False

                # Show candidates only for revealed cells
                if (row, col) in self.revealed_cells and value == 0:
                    cell.notes_enabled = True
                    cell.notes_mode = 'auto'
                    cell.candidates = self.working_candidates.get((row, col), set()).copy()
                else:
                    cell.notes_enabled = False
                    cell.candidates.clear()

                cell.update()

    def update_display(self):
        filled, total, percent = self.game.get_progress()
        self.progress_label.setText(f"Progress: {filled}/{total} ({percent:.0f}%)")
        self.hint_count_label.setText(f"Hints: {self.hints_applied}")

        state_names = {STATE_OVERVIEW: 'Overview', STATE_EXPLAIN: 'Explain', STATE_EXECUTE: 'Execute'}
        self.state_label.setText(f"State: {state_names.get(self.state, self.state)}")

    def find_next_hint(self):
        board = self.game.board

        # 0. Last remaining cell in a house (easiest technique)
        hint = self._find_last_remaining(board)
        if hint:
            return hint

        # 1. Box hidden singles
        hint = self._find_box_hidden_single_with_context(board)
        if hint:
            return hint

        # 2. Row/col hidden singles (limited empty)
        hint = self._find_rowcol_single_limited_with_context(board)
        if hint:
            return hint

        # 3. Any hidden single
        hint = self._find_any_hidden_single_with_context(board)
        if hint:
            return hint

        # 4. Naked singles
        hint = self._find_naked_single_ordered(board)
        if hint:
            return hint

        # 5. Elimination techniques
        hint = self._find_elimination_pattern()
        if hint:
            return hint

        return None

    def _find_last_remaining(self, board):
        """Find houses with only one empty cell - fill the missing number"""
        # Check rows
        for row in range(9):
            empty_cells = [(row, col) for col in range(9) if board[row][col] == 0]
            if len(empty_cells) == 1:
                r, c = empty_cells[0]
                present = set(board[row][col] for col in range(9) if board[row][col] != 0)
                missing = (set(range(1, 10)) - present).pop()
                return {
                    'type': 'last_remaining',
                    'number': missing,
                    'cell': (r, c),
                    'location': f"row {row+1}",
                    'house_type': 'row'
                }

        # Check columns
        for col in range(9):
            empty_cells = [(row, col) for row in range(9) if board[row][col] == 0]
            if len(empty_cells) == 1:
                r, c = empty_cells[0]
                present = set(board[row][col] for row in range(9) if board[row][col] != 0)
                missing = (set(range(1, 10)) - present).pop()
                return {
                    'type': 'last_remaining',
                    'number': missing,
                    'cell': (r, c),
                    'location': f"column {col+1}",
                    'house_type': 'col'
                }

        # Check boxes
        for br in range(3):
            for bc in range(3):
                empty_cells = []
                present = set()
                for i in range(3):
                    for j in range(3):
                        r, c = br * 3 + i, bc * 3 + j
                        if board[r][c] == 0:
                            empty_cells.append((r, c))
                        else:
                            present.add(board[r][c])
                if len(empty_cells) == 1:
                    r, c = empty_cells[0]
                    missing = (set(range(1, 10)) - present).pop()
                    return {
                        'type': 'last_remaining',
                        'number': missing,
                        'cell': (r, c),
                        'location': f"box ({br+1},{bc+1})",
                        'house_type': 'box'
                    }

        return None

    def _find_relevant_excluders_for_box(self, board, target_row, target_col, num):
        """
        Find cells with 'num' that block rows/columns through the box.
        Returns (excluding_cells, excluded_cells) where excluded_cells includes
        ALL empty cells in the blocked rows/columns (cross-hatching pattern).
        """
        box_row_start = (target_row // 3) * 3
        box_col_start = (target_col // 3) * 3

        excluding_cells = []
        excluded_cells = []
        excluded_set = set()

        # Check each row in the box (except target's row)
        for row in range(box_row_start, box_row_start + 3):
            if row == target_row:
                continue
            # Is there a 'num' in this row outside the box?
            for c in range(9):
                if board[row][c] == num:
                    # This num blocks the entire row
                    if (row, c) not in excluding_cells:
                        excluding_cells.append((row, c))
                    # Shade ALL empty cells in this row
                    for shade_c in range(9):
                        if board[row][shade_c] == 0 and (row, shade_c) not in excluded_set:
                            excluded_cells.append((row, shade_c))
                            excluded_set.add((row, shade_c))
                    break

        # Check each column in the box (except target's column)
        for col in range(box_col_start, box_col_start + 3):
            if col == target_col:
                continue
            # Is there a 'num' in this column outside the box?
            for r in range(9):
                if board[r][col] == num:
                    # This num blocks the entire column
                    if (r, col) not in excluding_cells:
                        excluding_cells.append((r, col))
                    # Shade ALL empty cells in this column
                    for shade_r in range(9):
                        if board[shade_r][col] == 0 and (shade_r, col) not in excluded_set:
                            excluded_cells.append((shade_r, col))
                            excluded_set.add((shade_r, col))
                    break

        return excluding_cells, excluded_cells

    def _find_relevant_excluders_for_row(self, board, target_row, target_col, num):
        """
        Find cells with 'num' that block columns/boxes in the same row.
        Shades entire blocked columns or boxes (cross-hatching pattern).
        """
        excluding_cells = []
        excluded_cells = []
        excluded_set = set()
        blocked_cols = set()
        blocked_boxes = set()

        # For each other empty cell in the row
        for col in range(9):
            if col == target_col or board[target_row][col] != 0:
                continue

            # Check if this column is blocked by 'num'
            col_blocked = False
            for r in range(9):
                if board[r][col] == num:
                    if col not in blocked_cols:
                        blocked_cols.add(col)
                        if (r, col) not in excluding_cells:
                            excluding_cells.append((r, col))
                        # Shade ALL empty cells in this column
                        for shade_r in range(9):
                            if board[shade_r][col] == 0 and (shade_r, col) not in excluded_set:
                                excluded_cells.append((shade_r, col))
                                excluded_set.add((shade_r, col))
                    col_blocked = True
                    break

            # If not blocked by column, check if blocked by box
            if not col_blocked:
                box_r, box_c = (target_row // 3) * 3, (col // 3) * 3
                box_key = (box_r, box_c)
                for i in range(3):
                    for j in range(3):
                        r, c = box_r + i, box_c + j
                        if board[r][c] == num:
                            if box_key not in blocked_boxes:
                                blocked_boxes.add(box_key)
                                if (r, c) not in excluding_cells:
                                    excluding_cells.append((r, c))
                                # Shade ALL empty cells in this box
                                for bi in range(3):
                                    for bj in range(3):
                                        br, bc = box_r + bi, box_c + bj
                                        if board[br][bc] == 0 and (br, bc) not in excluded_set:
                                            excluded_cells.append((br, bc))
                                            excluded_set.add((br, bc))
                            break
                    else:
                        continue
                    break

        return excluding_cells, excluded_cells

    def _find_relevant_excluders_for_col(self, board, target_row, target_col, num):
        """
        Find cells with 'num' that block rows/boxes in the same column.
        Shades entire blocked rows or boxes (cross-hatching pattern).
        """
        excluding_cells = []
        excluded_cells = []
        excluded_set = set()
        blocked_rows = set()
        blocked_boxes = set()

        # For each other empty cell in the column
        for row in range(9):
            if row == target_row or board[row][target_col] != 0:
                continue

            # Check if this row is blocked by 'num'
            row_blocked = False
            for c in range(9):
                if board[row][c] == num:
                    if row not in blocked_rows:
                        blocked_rows.add(row)
                        if (row, c) not in excluding_cells:
                            excluding_cells.append((row, c))
                        # Shade ALL empty cells in this row
                        for shade_c in range(9):
                            if board[row][shade_c] == 0 and (row, shade_c) not in excluded_set:
                                excluded_cells.append((row, shade_c))
                                excluded_set.add((row, shade_c))
                    row_blocked = True
                    break

            # If not blocked by row, check if blocked by box
            if not row_blocked:
                box_r, box_c = (row // 3) * 3, (target_col // 3) * 3
                box_key = (box_r, box_c)
                for i in range(3):
                    for j in range(3):
                        r, c = box_r + i, box_c + j
                        if board[r][c] == num:
                            if box_key not in blocked_boxes:
                                blocked_boxes.add(box_key)
                                if (r, c) not in excluding_cells:
                                    excluding_cells.append((r, c))
                                # Shade ALL empty cells in this box
                                for bi in range(3):
                                    for bj in range(3):
                                        br, bc = box_r + bi, box_c + bj
                                        if board[br][bc] == 0 and (br, bc) not in excluded_set:
                                            excluded_cells.append((br, bc))
                                            excluded_set.add((br, bc))
                            break
                    else:
                        continue
                    break

        return excluding_cells, excluded_cells

    def _find_box_hidden_single_with_context(self, board):
        for num in range(1, 10):
            for box_row in range(3):
                for box_col in range(3):
                    possible_cells = []
                    for i in range(3):
                        for j in range(3):
                            row = box_row * 3 + i
                            col = box_col * 3 + j
                            if board[row][col] == 0 and SudokuSolver.is_valid_placement(board, row, col, num):
                                possible_cells.append((row, col))

                    if len(possible_cells) == 1:
                        target_row, target_col = possible_cells[0]
                        excluding_cells, excluded_cells = self._find_relevant_excluders_for_box(
                            board, target_row, target_col, num)

                        return {
                            'type': 'box_hidden_single',
                            'number': num,
                            'cell': possible_cells[0],
                            'location': f"box ({box_row+1},{box_col+1})",
                            'excluding_cells': excluding_cells,
                            'excluded_cells': excluded_cells
                        }
        return None

    def _find_rowcol_single_limited_with_context(self, board):
        for num in range(1, 10):
            for row in range(9):
                empty_count = sum(1 for col in range(9) if board[row][col] == 0)
                if empty_count <= 2:
                    possible_cols = [col for col in range(9)
                                     if board[row][col] == 0 and SudokuSolver.is_valid_placement(board, row, col, num)]
                    if len(possible_cols) == 1:
                        target_col = possible_cols[0]
                        excluding_cells, excluded_cells = self._find_relevant_excluders_for_row(
                            board, row, target_col, num)
                        return {
                            'type': 'rowcol_hidden_single',
                            'number': num,
                            'cell': (row, target_col),
                            'location': f"row {row+1}",
                            'excluding_cells': excluding_cells,
                            'excluded_cells': excluded_cells
                        }

            for col in range(9):
                empty_count = sum(1 for row in range(9) if board[row][col] == 0)
                if empty_count <= 2:
                    possible_rows = [row for row in range(9)
                                     if board[row][col] == 0 and SudokuSolver.is_valid_placement(board, row, col, num)]
                    if len(possible_rows) == 1:
                        target_row = possible_rows[0]
                        excluding_cells, excluded_cells = self._find_relevant_excluders_for_col(
                            board, target_row, col, num)
                        return {
                            'type': 'rowcol_hidden_single',
                            'number': num,
                            'cell': (target_row, col),
                            'location': f"column {col+1}",
                            'excluding_cells': excluding_cells,
                            'excluded_cells': excluded_cells
                        }
        return None

    def _find_any_hidden_single_with_context(self, board):
        for num in range(1, 10):
            # Rows
            for row in range(9):
                possible_cols = [col for col in range(9)
                                 if board[row][col] == 0 and SudokuSolver.is_valid_placement(board, row, col, num)]
                if len(possible_cols) == 1:
                    target_col = possible_cols[0]
                    excluding_cells, excluded_cells = self._find_relevant_excluders_for_row(
                        board, row, target_col, num)
                    return {
                        'type': 'hidden_single',
                        'number': num,
                        'cell': (row, target_col),
                        'location': f"row {row+1}",
                        'excluding_cells': excluding_cells,
                        'excluded_cells': excluded_cells
                    }

            # Columns
            for col in range(9):
                possible_rows = [row for row in range(9)
                                 if board[row][col] == 0 and SudokuSolver.is_valid_placement(board, row, col, num)]
                if len(possible_rows) == 1:
                    target_row = possible_rows[0]
                    excluding_cells, excluded_cells = self._find_relevant_excluders_for_col(
                        board, target_row, col, num)
                    return {
                        'type': 'hidden_single',
                        'number': num,
                        'cell': (target_row, col),
                        'location': f"column {col+1}",
                        'excluding_cells': excluding_cells,
                        'excluded_cells': excluded_cells
                    }

            # Boxes
            for box_row in range(3):
                for box_col in range(3):
                    possible_cells = []
                    for i in range(3):
                        for j in range(3):
                            row = box_row * 3 + i
                            col = box_col * 3 + j
                            if board[row][col] == 0 and SudokuSolver.is_valid_placement(board, row, col, num):
                                possible_cells.append((row, col))
                    if len(possible_cells) == 1:
                        target_row, target_col = possible_cells[0]
                        excluding_cells, excluded_cells = self._find_relevant_excluders_for_box(
                            board, target_row, target_col, num)
                        return {
                            'type': 'hidden_single',
                            'number': num,
                            'cell': possible_cells[0],
                            'location': f"box ({box_row+1},{box_col+1})",
                            'excluding_cells': excluding_cells,
                            'excluded_cells': excluded_cells
                        }
        return None

    def _find_naked_single_ordered(self, board):
        houses = []

        for row in range(9):
            cells = [(row, col) for col in range(9) if board[row][col] == 0]
            if cells:
                houses.append((len(cells), 'row', row, cells))

        for col in range(9):
            cells = [(row, col) for row in range(9) if board[row][col] == 0]
            if cells:
                houses.append((len(cells), 'col', col, cells))

        for br in range(3):
            for bc in range(3):
                cells = []
                for i in range(3):
                    for j in range(3):
                        r, c = br * 3 + i, bc * 3 + j
                        if board[r][c] == 0:
                            cells.append((r, c))
                if cells:
                    houses.append((len(cells), 'box', (br, bc), cells))

        houses.sort(key=lambda x: x[0])

        for empty_count, house_type, house_idx, cells in houses:
            for row, col in cells:
                cands = self.working_candidates.get((row, col), set())
                if len(cands) == 1:
                    num = list(cands)[0]
                    if house_type == 'row':
                        loc = f"row {house_idx + 1}"
                    elif house_type == 'col':
                        loc = f"column {house_idx + 1}"
                    else:
                        loc = f"box ({house_idx[0]+1},{house_idx[1]+1})"
                    return {
                        'type': 'naked_single',
                        'number': num,
                        'cell': (row, col),
                        'location': loc,
                        'house_type': house_type,
                        'house_index': house_idx,
                        'house_cells': cells
                    }

        return None

    def _find_elimination_pattern(self):
        board = self.game.board

        techniques = [
            ('naked_pair', SudokuAnalyzer._find_naked_pair),
            ('naked_triple', SudokuAnalyzer._find_naked_triple),
            ('naked_quad', SudokuAnalyzer._find_naked_quad),
            ('hidden_pair', SudokuAnalyzer._find_hidden_pair),
            ('hidden_triple', SudokuAnalyzer._find_hidden_triple),
            ('hidden_quad', SudokuAnalyzer._find_hidden_quad),
            ('pointing_pair', SudokuAnalyzer._find_pointing_pair),
            ('box_line_reduction', SudokuAnalyzer._find_box_line_reduction),
            ('xwing', SudokuAnalyzer._find_xwing),
            ('swordfish', SudokuAnalyzer._find_swordfish),
            ('jellyfish', SudokuAnalyzer._find_jellyfish),
            ('xy_wing', SudokuAnalyzer._find_xy_wing),
            ('simple_coloring', SudokuAnalyzer._find_simple_coloring),
            ('forcing_chain', SudokuAnalyzer._find_forcing_chain),
        ]

        for name, func in techniques:
            try:
                results = func(board, self.working_candidates, find_all=False)
                if results:
                    if isinstance(results, list):
                        for hint in results:
                            if self._has_valid_eliminations(hint):
                                return hint
                    elif isinstance(results, dict):
                        if self._has_valid_eliminations(results):
                            return results
            except Exception:
                pass

        return None

    def _has_valid_eliminations(self, hint):
        eliminations = hint.get('eliminations', [])
        for row, col, num in eliminations:
            if num in self.working_candidates.get((row, col), set()):
                return True
        return False

    def on_step(self):
        if self.state == STATE_OVERVIEW:
            hint = self.find_next_hint()
            if hint:
                self.current_hint = hint
                self.state = STATE_EXPLAIN
                self.show_explain()
            else:
                self.status_label.setText("No hints available - puzzle may need guessing")

        elif self.state == STATE_EXPLAIN:
            self.state = STATE_EXECUTE
            self.execute_hint()

        elif self.state == STATE_EXECUTE:
            hint = self.find_next_hint()
            if hint:
                self.current_hint = hint
                self.state = STATE_EXPLAIN
                self.show_explain()
            else:
                self.state = STATE_OVERVIEW
                self.clear_all_highlights()
                self.auto_step_timer.stop()

                if self.game.is_complete():
                    self.status_label.setText("Puzzle solved!")
                    QMessageBox.information(self, "Complete",
                        f"Puzzle solved in {self.hints_applied} hints!")
                else:
                    self.status_label.setText("No more hints available")

        self.update_display()

        if self.auto_step and self.state in (STATE_EXPLAIN, STATE_EXECUTE):
            self.auto_step_timer.start(2000)

    def show_explain(self):
        hint = self.current_hint
        if not hint:
            return

        hint_type = hint['type']

        strategy = STRATEGY_DESCRIPTIONS.get(hint_type, "Apply solving technique")
        self.strategy_label.setText(strategy)

        raw_lines = [f"  {k}: {v}" for k, v in hint.items()]
        self.raw_text.setText("Current hint:\n{\n" + "\n".join(raw_lines) + "\n}")

        formatted = [
            f"Level 1: {SudokuAnalyzer._format_hint_level_1(hint)}",
            f"Level 2: {SudokuAnalyzer._format_hint_level_2(hint)}",
            f"Level 3: {SudokuAnalyzer._format_hint_level_3(hint)}",
            f"Level 4: {SudokuAnalyzer._format_hint_level_4(hint)}",
            f"Level 5: {SudokuAnalyzer._format_hint_level_5(hint)}"
        ]
        self.format_text.setText("\n".join(formatted))

        self.status_label.setText(f"Explaining: {hint_type.replace('_', ' ').title()}")

        self.highlight_hint(hint)

    def highlight_hint(self, hint):
        self.clear_all_highlights()
        hint_type = hint['type']

        # For naked singles, reveal candidates in the house
        if hint_type == 'naked_single':
            house_cells = hint.get('house_cells', [])
            for r, c in house_cells:
                self.revealed_cells.add((r, c))
                cell = self.grid.cells[r][c]
                cell.notes_enabled = True
                cell.notes_mode = 'auto'
                cell.candidates = self.working_candidates.get((r, c), set()).copy()

        # For elimination techniques, reveal all candidates
        elif 'eliminations' in hint:
            for r in range(9):
                for c in range(9):
                    if self.game.board[r][c] == 0:
                        self.revealed_cells.add((r, c))
                        cell = self.grid.cells[r][c]
                        cell.notes_enabled = True
                        cell.notes_mode = 'auto'
                        cell.candidates = self.working_candidates.get((r, c), set()).copy()

        # Pattern cells (green) - for elimination techniques
        if 'cells' in hint:
            for r, c in hint['cells']:
                self.grid.cells[r][c].highlight_pattern = True

        # Target cell for placements (green)
        if 'cell' in hint:
            r, c = hint['cell']
            self.grid.cells[r][c].highlight_pattern = True

        # Excluding cells - make them BOLD instead of green
        if 'excluding_cells' in hint:
            for r, c in hint['excluding_cells']:
                self.grid.cells[r][c].is_bold = True

        # Excluded cells - where number CAN'T go (pink)
        if 'excluded_cells' in hint:
            for r, c in hint['excluded_cells']:
                self.grid.cells[r][c].highlight_excluded = True

        # Affected cells - cells with eliminations (yellow)
        if 'eliminations' in hint:
            for r, c, num in hint['eliminations']:
                self.grid.cells[r][c].highlight_affected = True

        # Update all cells
        for row in range(9):
            for col in range(9):
                self.grid.cells[row][col].update()

    def clear_all_highlights(self):
        for row in range(9):
            for col in range(9):
                cell = self.grid.cells[row][col]
                cell.highlight_pattern = False
                cell.highlight_affected = False
                cell.highlight_excluded = False
                cell.border_highlight = False
                cell.is_bold = False

                # Keep candidates visible only for revealed cells
                if (row, col) in self.revealed_cells and self.game.board[row][col] == 0:
                    cell.notes_enabled = True
                    cell.notes_mode = 'auto'
                    cell.candidates = self.working_candidates.get((row, col), set()).copy()
                else:
                    cell.notes_enabled = False
                    cell.candidates.clear()

                cell.update()

    def execute_hint(self, hint=None):
        if hint is None:
            hint = self.current_hint
        if not hint:
            return

        hint_type = hint['type']
        self.hints_applied += 1

        # Placement hints
        if hint_type in ('last_remaining', 'naked_single', 'hidden_single',
                         'box_hidden_single', 'rowcol_hidden_single', 'forcing_chain'):
            if 'cell' in hint and 'number' in hint:
                r, c = hint['cell']
                num = hint['number']
                self.game.board[r][c] = num

                if (r, c) in self.working_candidates:
                    del self.working_candidates[(r, c)]
                self.revealed_cells.discard((r, c))

                self._update_candidates_after_placement(r, c, num)

        # Elimination hints
        if 'eliminations' in hint:
            for r, c, num in hint['eliminations']:
                if (r, c) in self.working_candidates:
                    self.working_candidates[(r, c)].discard(num)

        self.refresh_grid()
        self.highlight_hint(hint)

        self.status_label.setText(f"Executed: {hint_type.replace('_', ' ').title()}")

    def _update_candidates_after_placement(self, placed_row, placed_col, num):
        for c in range(9):
            if (placed_row, c) in self.working_candidates:
                self.working_candidates[(placed_row, c)].discard(num)

        for r in range(9):
            if (r, placed_col) in self.working_candidates:
                self.working_candidates[(r, placed_col)].discard(num)

        box_row, box_col = (placed_row // 3) * 3, (placed_col // 3) * 3
        for i in range(3):
            for j in range(3):
                r, c = box_row + i, box_col + j
                if (r, c) in self.working_candidates:
                    self.working_candidates[(r, c)].discard(num)

    def handle_cell_click(self, row, col):
        pass

    def can_place_number(self, row, col, num):
        return self.game.can_place_number(row, col, num)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Sudoku Solver")
    window = SudokuSolverWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
