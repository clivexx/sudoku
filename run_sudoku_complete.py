#!/usr/bin/env python3
"""
Sudoku Player - Complete Enhanced Version
All original features + new modular architecture + hint system
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
                             QPushButton, QLabel, QMessageBox, QFrame, QListWidget,
                             QCheckBox, QGridLayout, QDialog, QRadioButton, QButtonGroup,
                             QScrollArea, QTextBrowser, QMenu, QLineEdit,
                             QListWidgetItem, QPlainTextEdit)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QKeyEvent, QAction

# Project root for loading help texts
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def load_help_texts():
    """Load help texts from help_texts.txt file"""
    help_file = os.path.join(PROJECT_ROOT, 'help_texts.txt')
    texts = {}
    if not os.path.exists(help_file):
        return texts

    try:
        with open(help_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse sections: [section_name] followed by content until next [section] or EOF
        import re
        sections = re.split(r'\n\[([^\]]+)\]\n', content)
        # sections[0] is content before first [section] (usually empty)
        # then alternates: section_name, content, section_name, content, ...
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                key = sections[i].strip().lower()
                value = sections[i + 1].strip()
                texts[key] = value
    except Exception:
        pass

    return texts

from sudoku_grid import SudokuGrid
from sudoku_game import SudokuGame
from sudoku_library import PuzzleLibrary, CustomPuzzleLibrary
from sudoku_solver import SudokuSolver
from sudoku_analyzer import SudokuAnalyzer


class PlacementHintDialog(QDialog):
    """Popup dialog for placement hints with progressive detail levels"""

    def __init__(self, hint, parent=None):
        super().__init__(parent)
        self.hint = hint
        self.parent_window = parent
        self.current_level = 1
        self.setWindowTitle("Placement Hint")
        self.setModal(True)
        self.setMinimumWidth(350)
        self.init_ui()
        self.update_display()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Title
        title = QLabel("Placement Hint")
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Hint text area
        self.hint_label = QLabel("")
        self.hint_label.setFont(QFont('Arial', 12))
        self.hint_label.setWordWrap(True)
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setMinimumHeight(80)
        self.hint_label.setStyleSheet("background-color: #E3F2FD; padding: 15px; border-radius: 5px;")
        layout.addWidget(self.hint_label)

        # Level indicator
        self.level_label = QLabel("Detail level: 1 of 5")
        self.level_label.setFont(QFont('Arial', 9))
        self.level_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.level_label.setStyleSheet("color: #666;")
        layout.addWidget(self.level_label)

        # Buttons
        button_layout = QHBoxLayout()

        self.more_btn = QPushButton("More")
        self.more_btn.setFont(QFont('Arial', 11))
        self.more_btn.clicked.connect(self.on_more)
        button_layout.addWidget(self.more_btn)

        self.return_btn = QPushButton("Return")
        self.return_btn.setFont(QFont('Arial', 11))
        self.return_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.return_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def update_display(self):
        """Update hint display based on current level"""
        if self.current_level == 1:
            text = SudokuAnalyzer._format_hint_level_1(self.hint)
        elif self.current_level == 2:
            text = SudokuAnalyzer._format_hint_level_2(self.hint)
        elif self.current_level == 3:
            text = SudokuAnalyzer._format_hint_level_3(self.hint)
        elif self.current_level == 4:
            text = SudokuAnalyzer._format_hint_level_4(self.hint)
        else:
            text = SudokuAnalyzer._format_hint_level_5(self.hint)

        self.hint_label.setText(text)
        self.level_label.setText(f"Detail level: {self.current_level} of 5")

        # Update button state at max level
        if self.current_level >= 5:
            self.more_btn.setEnabled(False)

        # Highlight cell at level 4+
        if self.current_level >= 4 and 'cell' in self.hint and self.parent_window:
            row, col = self.hint['cell']
            self.parent_window.grid.cells[row][col].border_highlight = True
            self.parent_window.grid.cells[row][col].update()

    def on_more(self):
        """Increase detail level"""
        if self.current_level < 5:
            self.current_level += 1
            self.update_display()


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
        
        self.easy_radio.setChecked(True)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # Custom puzzle options
        self.add_custom_radio = QRadioButton("Add Custom Puzzle")
        self.play_custom_radio = QRadioButton("Play Custom Puzzle")

        for radio in [self.add_custom_radio, self.play_custom_radio]:
            radio.setFont(QFont('Arial', 12))
            self.button_group.addButton(radio)
            layout.addWidget(radio)

        start_btn = QPushButton("Continue")
        start_btn.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        start_btn.clicked.connect(self.accept)
        layout.addWidget(start_btn)

        self.setLayout(layout)

    def get_difficulty(self):
        """Return selected difficulty or custom action"""
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
        elif self.add_custom_radio.isChecked():
            return 'add_custom'
        elif self.play_custom_radio.isChecked():
            return 'play_custom'
        else:
            return 'Easy'


class AddCustomPuzzleDialog(QDialog):
    """Dialog for entering a custom puzzle"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Custom Puzzle")
        self.setModal(True)
        self.puzzle_string = None
        self.puzzle_title = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title input
        title_label = QLabel("Description/Title:")
        title_label.setFont(QFont('Arial', 11))
        layout.addWidget(title_label)

        self.title_input = QLineEdit()
        self.title_input.setFont(QFont('Arial', 11))
        self.title_input.setPlaceholderText("e.g., NY Times Hard #42")
        layout.addWidget(self.title_input)

        # Puzzle input (9x9 grid as text)
        puzzle_label = QLabel("Puzzle (81 digits, 0 for empty):")
        puzzle_label.setFont(QFont('Arial', 11))
        layout.addWidget(puzzle_label)

        self.puzzle_input = QPlainTextEdit()
        font = QFont('Courier', 14)
        self.puzzle_input.setFont(font)
        # Calculate width for exactly 9 characters
        from PyQt6.QtGui import QFontMetrics
        fm = QFontMetrics(font)
        char_width = fm.horizontalAdvance('0')
        # Width for 9 chars + minimal internal padding (forces wrap after 9)
        self.puzzle_input.setFixedWidth(char_width * 9 + 12)
        self.puzzle_input.setFixedHeight(fm.height() * 10 + 10)
        self.puzzle_input.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.puzzle_input.setPlaceholderText("530070000\n600195000\n098000060\n...")
        self.puzzle_input.textChanged.connect(self.update_char_count)
        layout.addWidget(self.puzzle_input)

        # Character count
        self.char_count_label = QLabel("0 / 81 characters")
        self.char_count_label.setFont(QFont('Arial', 10))
        layout.addWidget(self.char_count_label)

        # Buttons
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("Add Puzzle")
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
        """Extract digits from text, stripping whitespace/newlines"""
        text = self.puzzle_input.toPlainText()
        # Keep only digits
        return ''.join(c for c in text if c.isdigit())

    def validate_and_accept(self):
        """Validate puzzle string and accept if valid"""
        title = self.title_input.text().strip()
        puzzle_str = self.get_puzzle_string()

        # Check title
        if not title:
            QMessageBox.warning(self, "Invalid Input", "Please enter a description/title.")
            return

        # Check length (get_puzzle_string already filters to digits only)
        if len(puzzle_str) != 81:
            QMessageBox.warning(self, "Invalid Input",
                f"Puzzle must have exactly 81 digits.\nCurrently: {len(puzzle_str)}")
            return

        # Convert to board for validation
        board = []
        for i in range(9):
            row = [int(puzzle_str[i*9 + j]) for j in range(9)]
            board.append(row)

        # Check solvability
        solution_count = SudokuSolver.count_solutions(board, max_count=2)

        if solution_count == 0:
            QMessageBox.warning(self, "Invalid Puzzle",
                "This puzzle has no solution.")
            return
        elif solution_count > 1:
            QMessageBox.warning(self, "Invalid Puzzle",
                "This puzzle has multiple solutions.")
            return

        # Valid puzzle - save it
        self.puzzle_string = puzzle_str
        self.puzzle_title = title
        self.accept()

    def get_result(self):
        """Return the validated puzzle string and title"""
        return self.puzzle_string, self.puzzle_title


class PlayCustomPuzzleDialog(QDialog):
    """Dialog for selecting a custom puzzle to play"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Play Custom Puzzle")
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

        # Load puzzles
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

        # Buttons
        btn_layout = QHBoxLayout()
        self.play_btn = QPushButton("Play")
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
        """Select current item and accept"""
        current = self.puzzle_list.currentItem()
        if current and self.puzzles:
            title = current.data(Qt.ItemDataRole.UserRole)
            if title and title in self.puzzles:
                self.selected_title = title
                self.selected_puzzle = self.puzzles[title]['puzzle']
                self.accept()

    def get_result(self):
        """Return the selected puzzle string and title"""
        return self.selected_puzzle, self.selected_title


class SudokuPlayerWindow(QMainWindow):
    """Complete Sudoku Player with all features"""
    
    def __init__(self, skip_dialog=False):
        super().__init__()
        self.setWindowTitle("Sudoku Trainer")
        self.resize(1200, 800)
        
        # Create game logic
        self.game = SudokuGame()
        
        # UI state
        self.note_mode = False  # False = number mode, True = note mode

        # Elimination mode state
        self.elimination_mode = False
        self.elimination_patterns = []
        self.pattern_reveal_levels = []
        self.pattern_masked = []  # Track which patterns are masked
        self.pattern_row_widgets = []

        # Help system
        self.help_texts = load_help_texts()
        self.help_visible = False

        # UI references (will be set in init_ui)
        self.grid = None
        self.number_buttons = []
        
        # Create UI
        self.init_ui()
        self.create_menu_bar()
        
        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)
        
        # Start with difficulty selection
        if not skip_dialog:
            self.select_and_start_game()
    
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout()
        central.setLayout(main_layout)
        
        top_layout = QHBoxLayout()
        
        # ============ LEFT PANEL ============
        left_panel = QVBoxLayout()
        left_panel.setSpacing(8)

        # ===== TITLE =====
        title = QLabel("Sudoku Trainer")
        title.setFont(QFont('Arial', 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_panel.addWidget(title)

        # ===== STATS ROW =====
        stats_layout = QHBoxLayout()
        self.timer_label = QLabel("00:00")
        self.timer_label.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        stats_layout.addWidget(self.timer_label)

        self.moves_label = QLabel("Moves: 0")
        self.moves_label.setFont(QFont('Arial', 10))
        stats_layout.addWidget(self.moves_label)

        self.hints_label = QLabel("Hints: 0")
        self.hints_label.setFont(QFont('Arial', 10))
        stats_layout.addWidget(self.hints_label)

        left_panel.addLayout(stats_layout)

        # ===== PROGRESS =====
        self.progress_label = QLabel("Progress: 0% (0/81)")
        self.progress_label.setFont(QFont('Arial', 9))
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_panel.addWidget(self.progress_label)

        # ===== DIFFICULTY =====
        self.difficulty_label = QLabel("Difficulty: Unknown")
        self.difficulty_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        self.difficulty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_panel.addWidget(self.difficulty_label)

        # ===== SEPARATOR =====
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        left_panel.addWidget(separator)

        # ===== GET HINT BUTTON =====
        get_hint_btn = QPushButton("Get Hint")
        get_hint_btn.setFont(QFont('Arial', 11, QFont.Weight.Bold))
        get_hint_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        get_hint_btn.clicked.connect(self.show_hint)
        left_panel.addWidget(get_hint_btn)

        # ===== HINT LABEL (for placement hints) =====
        self.hint_label = QLabel("")
        self.hint_label.setWordWrap(True)
        self.hint_label.setStyleSheet("background-color: #E3F2FD; padding: 5px; border-radius: 3px;")
        left_panel.addWidget(self.hint_label)

        # ===== ELIMINATION MODE PANEL (hidden initially) =====
        self.elimination_panel = QFrame()
        self.elimination_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        self.elimination_panel.setStyleSheet("background-color: #FFF3E0; border-radius: 5px;")
        elim_layout = QVBoxLayout(self.elimination_panel)
        elim_layout.setContentsMargins(5, 5, 5, 5)

        # Header with count and close button
        header_layout = QHBoxLayout()
        self.elim_count_label = QLabel("0 patterns found")
        self.elim_count_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        header_layout.addWidget(self.elim_count_label)
        close_btn = QPushButton("X")
        close_btn.setMaximumSize(25, 25)
        close_btn.clicked.connect(self.exit_elimination_mode)
        header_layout.addWidget(close_btn)
        elim_layout.addLayout(header_layout)

        # Scrollable area for pattern list (taller)
        self.elim_scroll_area = QScrollArea()
        self.elim_scroll_area.setWidgetResizable(True)
        self.elim_scroll_area.setMinimumHeight(250)
        self.elim_scroll_area.setMaximumHeight(350)
        self.pattern_list_widget = QWidget()
        self.pattern_list_layout = QVBoxLayout(self.pattern_list_widget)
        self.pattern_list_layout.setSpacing(2)
        self.elim_scroll_area.setWidget(self.pattern_list_widget)
        elim_layout.addWidget(self.elim_scroll_area)

        self.elimination_panel.hide()
        left_panel.addWidget(self.elimination_panel)

        # ===== HELP PANEL (hidden initially) =====
        self.help_panel = QFrame()
        self.help_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        self.help_panel.setStyleSheet("background-color: #E8F5E9; border-radius: 5px;")
        help_layout = QVBoxLayout(self.help_panel)
        help_layout.setContentsMargins(5, 5, 5, 5)

        # Help header with toggle button
        help_header = QHBoxLayout()
        help_title = QLabel("Help")
        help_title.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        help_header.addWidget(help_title)
        help_header.addStretch()
        self.help_toggle_btn = QPushButton("OFF")
        self.help_toggle_btn.setMaximumWidth(40)
        self.help_toggle_btn.setCheckable(True)
        self.help_toggle_btn.clicked.connect(self.toggle_help)
        help_header.addWidget(self.help_toggle_btn)
        help_layout.addLayout(help_header)

        # Help text browser
        self.help_browser = QTextBrowser()
        self.help_browser.setMaximumHeight(120)
        self.help_browser.setOpenExternalLinks(True)
        self.help_browser.hide()
        help_layout.addWidget(self.help_browser)

        left_panel.addWidget(self.help_panel)

        # ===== CONTROLS ROW: Undo + Show Errors =====
        controls_row = QHBoxLayout()
        undo_btn = QPushButton("Undo")
        undo_btn.setMaximumWidth(60)
        undo_btn.clicked.connect(self.undo)
        undo_btn.setShortcut("Ctrl+Z")
        controls_row.addWidget(undo_btn)

        self.show_errors_cb = QCheckBox("Show Errors")
        self.show_errors_cb.stateChanged.connect(self.toggle_show_errors_checkbox)
        controls_row.addWidget(self.show_errors_cb)
        controls_row.addStretch()
        left_panel.addLayout(controls_row)

        # ===== SAVED POSITIONS: Title row with Save/Load buttons =====
        bookmarks_header = QHBoxLayout()
        bookmarks_label = QLabel("Saved Positions:")
        bookmarks_label.setFont(QFont('Arial', 9))
        bookmarks_header.addWidget(bookmarks_label)
        bookmarks_header.addStretch()

        save_btn = QPushButton("Save")
        save_btn.setMaximumWidth(45)
        save_btn.clicked.connect(self.save_bookmark)
        bookmarks_header.addWidget(save_btn)

        load_btn = QPushButton("Load")
        load_btn.setMaximumWidth(45)
        load_btn.clicked.connect(self.load_bookmark)
        bookmarks_header.addWidget(load_btn)

        left_panel.addLayout(bookmarks_header)

        # ===== BOOKMARKS LIST =====
        self.bookmarks_list = QListWidget()
        self.bookmarks_list.setMaximumHeight(100)
        self.bookmarks_list.itemDoubleClicked.connect(self.on_bookmark_selected)
        left_panel.addWidget(self.bookmarks_list)

        left_panel.addStretch()
        
        # ============ CENTER - GRID ============
        self.grid = SudokuGrid(self)  # Pass UI as parent, not game
        
        # ============ RIGHT PANEL ============
        right_panel = QVBoxLayout()
        right_panel.setSpacing(5)
        
        # NUMBER buttons (3x3 grid)
        num_label = QLabel("Numbers:")
        num_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        right_panel.addWidget(num_label)
        
        num_grid = QGridLayout()
        num_grid.setSpacing(5)
        self.number_buttons = []
        
        for num in range(1, 10):
            btn = QPushButton(str(num))
            btn.setMinimumSize(60, 60)
            btn.setFont(QFont('Arial', 18, QFont.Weight.Bold))
            btn.clicked.connect(lambda checked, n=num: self.select_number_button(n))
            row = (num - 1) // 3
            col = (num - 1) % 3
            num_grid.addWidget(btn, row, col)
            self.number_buttons.append(btn)
        
        right_panel.addLayout(num_grid)
        
        clear_btn = QPushButton("Clear")
        clear_btn.setMinimumHeight(40)
        clear_btn.clicked.connect(lambda: self.select_number_button(0))
        right_panel.addWidget(clear_btn)
        
        # NOTE buttons (3x3 grid)
        note_label = QLabel("Notes:")
        note_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        right_panel.addWidget(note_label)
        
        note_grid = QGridLayout()
        note_grid.setSpacing(5)
        self.note_buttons = []
        
        for num in range(1, 10):
            btn = QPushButton(str(num))
            btn.setMinimumSize(60, 60)
            btn.setFont(QFont('Arial', 18, QFont.Weight.Bold))
            btn.clicked.connect(lambda checked, n=num: self.select_note_button(n))
            row = (num - 1) // 3
            col = (num - 1) % 3
            note_grid.addWidget(btn, row, col)
            self.note_buttons.append(btn)
        
        right_panel.addLayout(note_grid)

        right_panel.addStretch()
        
        # Add all panels to top layout
        top_layout.addLayout(left_panel, 1)
        top_layout.addWidget(self.grid, 3)
        top_layout.addLayout(right_panel, 1)
        
        main_layout.addLayout(top_layout)
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # ===== GAME MENU =====
        game_menu = menubar.addMenu('Game')

        new_action = game_menu.addAction('New Puzzle')
        new_action.triggered.connect(self.select_and_start_game)
        new_action.setShortcut('Ctrl+N')

        restart_action = game_menu.addAction('Restart Puzzle')
        restart_action.triggered.connect(self.restart_puzzle)
        restart_action.setShortcut('Ctrl+R')

        game_menu.addSeparator()

        exit_action = game_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut('Ctrl+Q')

        # ===== OPTIONS MENU =====
        options_menu = menubar.addMenu('Options')

        self.auto_notes_action = options_menu.addAction('Auto Notes')
        self.auto_notes_action.setCheckable(True)
        self.auto_notes_action.setChecked(False)
        self.auto_notes_action.triggered.connect(self.toggle_auto_notes)

        options_menu.addSeparator()

        self.shade_candidates_action = options_menu.addAction('Shade Candidates')
        self.shade_candidates_action.setCheckable(True)
        self.shade_candidates_action.setChecked(False)
        self.shade_candidates_action.triggered.connect(self.toggle_shade_candidates)

        self.highlight_naked_singles_action = options_menu.addAction('Highlight Naked Singles')
        self.highlight_naked_singles_action.setCheckable(True)
        self.highlight_naked_singles_action.setChecked(False)
        self.highlight_naked_singles_action.triggered.connect(self.toggle_highlight_naked_singles)

        self.highlight_hidden_singles_action = options_menu.addAction('Highlight Hidden Singles')
        self.highlight_hidden_singles_action.setCheckable(True)
        self.highlight_hidden_singles_action.setChecked(False)
        self.highlight_hidden_singles_action.triggered.connect(self.toggle_highlight_hidden_singles)

        # ===== HELP MENU =====
        help_menu = menubar.addMenu('Help')

        about_action = help_menu.addAction('About')
        about_action.triggered.connect(self.show_about)
    
    # ========================================
    # GAME FLOW
    # ========================================
    
    def select_and_start_game(self):
        """Show difficulty selection and start game"""
        dialog = DifficultyDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            choice = dialog.get_difficulty()

            if choice == 'add_custom':
                self.add_custom_puzzle()
            elif choice == 'play_custom':
                self.play_custom_puzzle()
            else:
                self.start_new_game(choice)

    def add_custom_puzzle(self):
        """Show dialog to add a custom puzzle"""
        dialog = AddCustomPuzzleDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            puzzle_str, title = dialog.get_result()
            if puzzle_str and title:
                # Save to library
                CustomPuzzleLibrary.add_puzzle(title, puzzle_str, 'Custom')

                # Ask if user wants to play it now
                reply = QMessageBox.question(self, "Puzzle Added",
                    f"'{title}' has been saved.\n\nPlay it now?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)

                if reply == QMessageBox.StandardButton.Yes:
                    self.start_custom_game(puzzle_str, title)

    def play_custom_puzzle(self):
        """Show dialog to select and play a custom puzzle"""
        dialog = PlayCustomPuzzleDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            puzzle_str, title = dialog.get_result()
            if puzzle_str:
                self.start_custom_game(puzzle_str, title)

    def start_custom_game(self, puzzle_str: str, title: str):
        """Start a game with a custom puzzle"""
        self.game.start_game_from_string(puzzle_str, 'Custom')
        self.difficulty_label.setText(f"Custom: {title}")
        self.reset_for_new_puzzle()
    
    def start_new_game(self, difficulty):
        """Start a new game"""
        puzzle_str = PuzzleLibrary.select_puzzle(difficulty)
        
        if not puzzle_str:
            QMessageBox.warning(self, "No Puzzles",
                f"No puzzles available for {difficulty}.\n" +
                "Please add puzzles to the library file.")
            return
        
        self.game.start_game_from_string(puzzle_str, difficulty)
        self.difficulty_label.setText(f"Difficulty: {difficulty}")
        self.reset_for_new_puzzle()

    def restart_puzzle(self):
        """Restart the current puzzle with confirmation"""
        if not self.game.current_puzzle_string:
            QMessageBox.information(self, "No Puzzle", "No puzzle to restart.")
            return

        reply = QMessageBox.question(
            self, "Restart Puzzle",
            "Are you sure you want to restart this puzzle?\nAll progress will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.game.start_game_from_string(
                self.game.current_puzzle_string,
                self.game.current_difficulty
            )
            self.reset_for_new_puzzle()

    def reset_for_new_puzzle(self):
        """Reset all UI state for a new puzzle - single entry point"""
        # Reset UI mode
        self.note_mode = False

        # Exit elimination mode if active
        if self.elimination_mode:
            self.exit_elimination_mode()

        # Reset timer display
        self.timer_label.setText("00:00")

        # Clear bookmarks
        self.bookmarks_list.clear()

        # Reset all cells and refresh from game state
        for row in range(9):
            for col in range(9):
                cell = self.grid.cells[row][col]
                cell.reset()  # Clear all flags
                value = self.game.board[row][col]
                is_initial = (self.game.initial_board[row][col] != 0)
                cell.set_value(value, is_initial)

        # Update all displays
        self.update_button_styles()
        self.update_number_counters()
        self.update_candidate_highlighting()
        self.update_stats()
        self.update_progress()

    def refresh_grid(self):
        """Refresh all cells from game state (preserves UI mode)"""
        for row in range(9):
            for col in range(9):
                cell = self.grid.cells[row][col]
                value = self.game.board[row][col]
                is_initial = (self.game.initial_board[row][col] != 0)
                cell.set_value(value, is_initial)
                cell.border_highlight = False
                cell.is_singleton = False
                cell.is_candidate = False
                cell.update()

        self.update_button_styles()
        self.update_number_counters()
        self.update_candidate_highlighting()
    
    # ========================================
    # NUMBER AND NOTE BUTTON SELECTION
    # ========================================
    
    def select_number_button(self, num):
        """
        Click a NUMBER button:
        - If different number: select it + switch to number mode
        - If same number: deselect + neutral mode
        - If Clear (0): deselect + neutral mode
        """
        if num == 0 or (self.game.selected_number == num and not self.note_mode):
            # Deselect - go to neutral
            self.game.selected_number = None
            self.note_mode = False
        else:
            # Select this number in number mode
            self.game.selected_number = num
            self.note_mode = False
        
        self.update_button_styles()
        self.update_bold_numbers()
        self.update_candidate_highlighting()
    
    def select_note_button(self, num):
        """
        Click a NOTE button:
        - If different number: select it + switch to note mode
        - If same number: deselect + neutral mode
        """
        if self.game.selected_number == num and self.note_mode:
            # Deselect - go to neutral
            self.game.selected_number = None
            self.note_mode = False
        else:
            # Select this number in note mode
            self.game.selected_number = num
            self.note_mode = True
        
        self.update_button_styles()
        self.update_bold_numbers()
        self.update_candidate_highlighting()
    
    def update_button_styles(self):
        """Update number and note button appearance"""
        selected_num = self.game.selected_number
        
        # Update NUMBER buttons
        for i, btn in enumerate(self.number_buttons):
            num = i + 1
            if selected_num == num and not self.note_mode:
                # This number selected in number mode
                btn.setStyleSheet("background-color: #FF6B6B; color: white; font-weight: bold;")
            else:
                btn.setStyleSheet("background-color: #E0E0E0;")
        
        # Update NOTE buttons
        for i, btn in enumerate(self.note_buttons):
            num = i + 1
            if selected_num == num and self.note_mode:
                # This number selected in note mode
                btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
            else:
                btn.setStyleSheet("background-color: #E0E0E0;")
    
    def handle_cell_click(self, row, col):
        """Handle cell click from grid - routes to appropriate handler"""
        if self.note_mode:
            # Note mode - toggle manual note
            self.handle_note_click(row, col)
        else:
            # Number mode - place number
            self.handle_number_click(row, col)
    
    def handle_number_click(self, row, col):
        """Handle clicking a cell in number mode"""
        # Let game handle the logic
        if self.game.handle_cell_click(row, col):
            # Exit elimination mode when a number is placed
            if self.elimination_mode:
                self.exit_elimination_mode()

            # Update the cell display (preserves notes if they're hidden)
            cell = self.grid.cells[row][col]
            cell.update_display(self.game.board[row][col])

            # Recalculate notes if enabled
            self.recalculate_affected_notes()

            # Update bold display for the number that was just placed/cleared
            self.update_bold_numbers()

            # Auto-update error flags (always, even if not visible)
            self.update_error_flags()

            # Recalculate all shading (hint borders, candidates, naked singles)
            self.recalculate_all_shading()

            # Update UI
            self.update_stats()
            self.update_number_counters()
            self.update_progress()

            # If show errors is on, update the display
            if self.game.show_errors:
                self.update_error_display()
    
    def handle_note_click(self, row, col):
        """
        Handle clicking a cell in note mode
        State 4 (yellow auto) + edit → State 5 (green manual)
        State 5 (green manual) + edit → stays State 5
        """
        cell = self.grid.cells[row][col]
        
        # Can't edit notes on initial cells or filled cells
        if cell.is_initial or cell.value != 0:
            return
        
        # If no number selected, do nothing in note mode
        if self.game.selected_number is None or self.game.selected_number == 0:
            return
        
        # Make sure notes are enabled and in manual mode
        if not cell.notes_enabled:
            # State 3 → State 5: Go directly to manual mode with empty candidates
            cell.notes_enabled = True
            cell.notes_mode = 'manual'
            cell.manual_candidates.clear()
        elif cell.notes_mode == 'auto':
            # State 4 → State 5: Copy current auto candidates to manual
            cell.set_manual_notes()
        
        # Toggle the specific candidate (in State 5)
        cell.toggle_manual_candidate(self.game.selected_number)
    
    def can_place_number(self, row, col, num):
        """Delegate to game - needed by cells for candidate calculation"""
        return self.game.can_place_number(row, col, num)
    
    def update_number_counters(self):
        """Show remaining count on buttons"""
        for i, btn in enumerate(self.number_buttons):
            num = i + 1
            count = self.game.count_remaining(num)
            if count > 0:
                btn.setText(f"{num}\n({count})")
            else:
                btn.setText(str(num))
    
    def update_bold_numbers(self):
        """Make selected number bold on grid"""
        for row in range(9):
            for col in range(9):
                cell = self.grid.cells[row][col]
                if self.game.selected_number and cell.value == self.game.selected_number:
                    cell.is_bold = True
                else:
                    cell.is_bold = False
                cell.update()
    
    def update_candidate_highlighting(self):
        """Highlight valid placement cells, naked singles, and hidden singles"""
        shade_candidates = self.game.shade_candidates
        highlight_naked_singles = self.highlight_naked_singles_action.isChecked()
        highlight_hidden_singles = self.highlight_hidden_singles_action.isChecked()
        selected_num = self.game.selected_number

        # Pre-compute hidden singles for selected number if needed
        hidden_single_cells = set()
        if selected_num and highlight_hidden_singles:
            hidden_single_cells = self._find_hidden_single_cells(selected_num)

        for row in range(9):
            for col in range(9):
                cell = self.grid.cells[row][col]
                cell.is_singleton = False
                cell.is_candidate = False

                if selected_num and selected_num != 0:
                    if self.game.can_place_number(row, col, selected_num):
                        possible_count = sum(1 for n in range(1, 10) if self.game.can_place_number(row, col, n))

                        # Naked single: only one candidate possible in this cell
                        if possible_count == 1 and highlight_naked_singles:
                            cell.is_singleton = True
                        # Hidden single: number can only go here in some house
                        elif (row, col) in hidden_single_cells and highlight_hidden_singles:
                            cell.is_singleton = True
                        elif shade_candidates:
                            # Regular candidate shading
                            cell.is_candidate = True

                cell.update()

    def _find_hidden_single_cells(self, num):
        """Find cells where num is a hidden single (only place in row/col/box)"""
        hidden_cells = set()

        # Check rows
        for row in range(9):
            valid_cols = [col for col in range(9) if self.game.can_place_number(row, col, num)]
            if len(valid_cols) == 1:
                hidden_cells.add((row, valid_cols[0]))

        # Check columns
        for col in range(9):
            valid_rows = [row for row in range(9) if self.game.can_place_number(row, col, num)]
            if len(valid_rows) == 1:
                hidden_cells.add((valid_rows[0], col))

        # Check boxes
        for box_row in range(3):
            for box_col in range(3):
                valid_cells = []
                for r in range(box_row * 3, box_row * 3 + 3):
                    for c in range(box_col * 3, box_col * 3 + 3):
                        if self.game.can_place_number(r, c, num):
                            valid_cells.append((r, c))
                if len(valid_cells) == 1:
                    hidden_cells.add(valid_cells[0])

        return hidden_cells
    
    # ========================================
    # MOVES AND UNDO
    # ========================================
    
    def undo(self):
        """Undo last move"""
        if self.game.undo():
            self.refresh_grid()
            self.recalculate_affected_notes()
            self.update_stats()
            self.update_progress()

            # Auto-update error flags
            self.update_error_flags()

            # Recalculate all shading
            self.recalculate_all_shading()

            # If show errors is on, update the display
            if self.game.show_errors:
                self.update_error_display()
    
    # ========================================
    # AUTO NOTES
    # ========================================
    
    def toggle_auto_notes(self):
        """Toggle auto notes (from menu)"""
        enabled = self.game.toggle_auto_notes(self.grid.cells)

        # Sync menu checkmark with actual state
        self.auto_notes_action.setChecked(enabled)

        # Update all cells
        for row in range(9):
            for col in range(9):
                self.grid.cells[row][col].update()
    
    def recalculate_affected_notes(self):
        """Recalculate notes after a move"""
        self.game.recalculate_affected_notes(self.grid.cells)
        for row in range(9):
            for col in range(9):
                self.grid.cells[row][col].update()
    
    # ========================================
    # HINTS
    # ========================================

    def show_hint(self):
        """Show a hint - placement hints in popup, elimination patterns in panel"""
        # If already in elimination mode, do nothing (use per-row buttons)
        if self.elimination_mode:
            return

        # Clear any existing hint highlights
        self.clear_hint_borders()

        # Increment hint count
        self.game.hint_count += 1
        self.update_stats()

        # Check for placement hints first (singles)
        placement_hint = SudokuAnalyzer.find_placement_hint(self.game.board)
        if placement_hint:
            # Show placement hint in popup dialog
            self.hint_label.setText("")
            dialog = PlacementHintDialog(placement_hint, self)
            dialog.exec()
            # Clear highlight when dialog closes
            self.clear_hint_borders()
            return

        # No placements available - find all elimination patterns
        all_patterns = SudokuAnalyzer.find_all_elimination_patterns(self.game.board)
        # Filter to only patterns with new eliminations
        filtered_patterns = self._filter_redundant_patterns(all_patterns)
        if filtered_patterns:
            self.enter_elimination_mode(filtered_patterns)
        else:
            self.hint_label.setText("No techniques available. The puzzle may require guessing.")

    def _filter_redundant_patterns(self, patterns):
        """
        Filter patterns to only include those that eliminate candidates
        not already eliminated by earlier patterns in the list.
        """
        if not patterns:
            return []

        # Build working set of candidates for each cell
        # Key: (row, col), Value: set of candidate numbers
        from sudoku_solver import SudokuSolver
        working_candidates = {}
        for row in range(9):
            for col in range(9):
                if self.game.board[row][col] == 0:
                    cands = set()
                    for num in range(1, 10):
                        if self.game.can_place_number(row, col, num):
                            cands.add(num)
                    working_candidates[(row, col)] = cands

        filtered = []
        for pattern in patterns:
            eliminations = pattern.get('eliminations', [])
            if not eliminations:
                continue

            # Check if this pattern eliminates any candidates still in working set
            new_eliminations = []
            for (row, col, num) in eliminations:
                cell_cands = working_candidates.get((row, col), set())
                if num in cell_cands:
                    new_eliminations.append((row, col, num))

            if new_eliminations:
                # This pattern has at least one new elimination - keep it
                filtered.append(pattern)

                # Apply eliminations to working candidates
                for (row, col, num) in new_eliminations:
                    working_candidates[(row, col)].discard(num)

        return filtered

    def enter_elimination_mode(self, patterns):
        """Enter elimination mode with found patterns"""
        self.elimination_mode = True
        self.elimination_patterns = patterns
        self.pattern_reveal_levels = [0] * len(patterns)
        self.pattern_masked = [False] * len(patterns)
        self.pattern_row_widgets = []

        # Clear old pattern rows
        while self.pattern_list_layout.count():
            item = self.pattern_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Create a row for each pattern
        for i, pattern in enumerate(patterns):
            row_widget = QFrame()
            row_widget.setStyleSheet("background-color: #FFFFFF; border-radius: 3px; padding: 2px;")
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(3, 2, 3, 2)

            label = QLabel("Pattern")
            label.setWordWrap(True)
            label.setMinimumWidth(120)
            row_layout.addWidget(label, 1)

            more_btn = QPushButton("More")
            more_btn.setMaximumWidth(45)
            more_btn.clicked.connect(lambda checked, idx=i: self.reveal_pattern_more(idx))
            row_layout.addWidget(more_btn)

            mask_btn = QPushButton("Hide")
            mask_btn.setMaximumWidth(45)
            mask_btn.clicked.connect(lambda checked, idx=i: self.toggle_pattern_mask(idx))
            row_layout.addWidget(mask_btn)

            self.pattern_list_layout.addWidget(row_widget)
            self.pattern_row_widgets.append({
                'widget': row_widget,
                'label': label,
                'more_btn': more_btn,
                'mask_btn': mask_btn,
                'index': i
            })

        self.pattern_list_layout.addStretch()

        # Update display
        self.elim_count_label.setText(f"{len(patterns)} patterns found")
        self.hint_label.setText("")
        self.elimination_panel.show()

        # Update help if visible
        self.update_help_content()

    def exit_elimination_mode(self):
        """Exit elimination mode, back to normal play"""
        self.elimination_mode = False
        self.elimination_patterns = []
        self.pattern_reveal_levels = []
        self.pattern_masked = []
        self.pattern_row_widgets = []
        self.hint_label.setText("")
        self.elimination_panel.hide()
        self.clear_hint_borders()
        self.update_help_content()

    def reveal_pattern_more(self, pattern_idx):
        """Reveal more detail for a specific pattern, or reset if at max"""
        if pattern_idx >= len(self.elimination_patterns):
            return

        current_level = self.pattern_reveal_levels[pattern_idx]
        if current_level >= 5:
            # Reset back to "Pattern"
            self.pattern_reveal_levels[pattern_idx] = 0
        else:
            # Increment reveal level
            self.pattern_reveal_levels[pattern_idx] = current_level + 1

        self.update_pattern_row(pattern_idx)

    def update_pattern_row(self, pattern_idx):
        """Update a single pattern row based on its reveal level"""
        if pattern_idx >= len(self.pattern_row_widgets):
            return

        pattern = self.elimination_patterns[pattern_idx]
        level = self.pattern_reveal_levels[pattern_idx]
        row = self.pattern_row_widgets[pattern_idx]

        # Get formatted text based on level
        if level == 0:
            text = "Pattern"
        elif level == 1:
            text = SudokuAnalyzer._format_hint_level_1(pattern)
        elif level == 2:
            text = SudokuAnalyzer._format_hint_level_2(pattern)
        elif level == 3:
            text = SudokuAnalyzer._format_hint_level_3(pattern)
        elif level == 4:
            text = SudokuAnalyzer._format_hint_level_4(pattern)
        else:  # level 5
            text = SudokuAnalyzer._format_hint_level_5(pattern)

        row['label'].setText(text)

        # Update button text based on level
        if level >= 5:
            row['more_btn'].setText("Done")
        else:
            row['more_btn'].setText("More")

        # Update help with technique info if at level 2+
        if level >= 2 and 'technique' in pattern:
            self.update_help_content(pattern['technique'])

    def toggle_pattern_mask(self, pattern_idx):
        """Toggle mask state for a pattern and reorder the list"""
        if pattern_idx >= len(self.pattern_masked):
            return

        # Toggle masked state
        self.pattern_masked[pattern_idx] = not self.pattern_masked[pattern_idx]

        # Update button text
        row = self.pattern_row_widgets[pattern_idx]
        if self.pattern_masked[pattern_idx]:
            row['mask_btn'].setText("Show")
            row['widget'].setStyleSheet("background-color: #E0E0E0; border-radius: 3px; padding: 2px;")
        else:
            row['mask_btn'].setText("Hide")
            row['widget'].setStyleSheet("background-color: #FFFFFF; border-radius: 3px; padding: 2px;")

        # Reorder: unmasked first, then masked
        self.reorder_pattern_list()

    def reorder_pattern_list(self):
        """Reorder pattern rows: unmasked first, then masked"""
        # Remove all widgets from layout (but don't delete them)
        while self.pattern_list_layout.count():
            self.pattern_list_layout.takeAt(0)

        # Sort: unmasked (False) before masked (True)
        sorted_rows = sorted(
            self.pattern_row_widgets,
            key=lambda r: self.pattern_masked[r['index']]
        )

        # Re-add in sorted order
        for row in sorted_rows:
            self.pattern_list_layout.addWidget(row['widget'])

        self.pattern_list_layout.addStretch()

        # Update count display
        masked_count = sum(self.pattern_masked)
        total = len(self.pattern_masked)
        if masked_count > 0:
            self.elim_count_label.setText(f"{total} patterns ({masked_count} hidden)")
        else:
            self.elim_count_label.setText(f"{total} patterns found")

    def highlight_hint_cell(self, cell):
        """Highlight a cell from the hint system"""
        row, col = cell
        self.clear_hint_borders()
        self.grid.cells[row][col].border_highlight = True
        self.grid.cells[row][col].update()

    def clear_hint_borders(self):
        """Clear all hint highlighting"""
        for row in range(9):
            for col in range(9):
                self.grid.cells[row][col].border_highlight = False
                self.grid.cells[row][col].update()

    # ========================================
    # HELP SYSTEM
    # ========================================

    def toggle_help(self):
        """Toggle help panel visibility"""
        self.help_visible = self.help_toggle_btn.isChecked()
        if self.help_visible:
            self.help_toggle_btn.setText("ON")
            self.help_browser.show()
            self.update_help_content()
        else:
            self.help_toggle_btn.setText("OFF")
            self.help_browser.hide()

    def update_help_content(self, technique_key=None):
        """Update help text based on current context or specific technique"""
        if not self.help_visible:
            return

        # If a specific technique is provided, show its help
        if technique_key:
            key = technique_key.lower().replace(' ', '_').replace('-', '_')
            text = self.help_texts.get(key, f"No help available for '{technique_key}'.")
            self.help_browser.setText(text)
            return

        # Default help based on game state
        if self.elimination_mode:
            self.help_browser.setText(
                "You're viewing elimination patterns. Click 'More' to reveal "
                "details about each pattern. Use the mask button to hide patterns "
                "you're not interested in."
            )
        else:
            filled, total, percent = self.game.get_progress()
            if percent < 30:
                text = self.help_texts.get('getting_started',
                    "Look for cells where only one number can go (naked singles) "
                    "or numbers that can only go in one place in a row, column, or box (hidden singles)."
                )
            elif percent < 70:
                text = self.help_texts.get('mid_game',
                    "As the puzzle progresses, you may need more advanced techniques. "
                    "Use the Get Hint button if you're stuck."
                )
            else:
                text = self.help_texts.get('end_game',
                    "You're close to finishing! Look carefully for any remaining singles."
                )
            self.help_browser.setText(text)

    def show_about(self):
        """Show About dialog"""
        about_text = """<h2>Sudoku Trainer</h2>
<p><b>Version:</b> 1.0</p>
<p>An interactive Sudoku player with hints, notes, and puzzle library.</p>

<p><b>Features:</b></p>
<ul>
<li>Multiple difficulty levels</li>
<li>Auto and manual note modes</li>
<li>18 solving techniques with progressive hints</li>
<li>Save and load positions</li>
<li>Error checking</li>
</ul>

<p><b>Credits:</b></p>
<p>Developed with PyQt5<br>
Puzzle library and solving techniques</p>

<p>&copy; 2026</p>
"""
        QMessageBox.about(self, "About Sudoku Trainer", about_text)

    # ========================================
    # BOOKMARKS
    # ========================================
    
    def save_bookmark(self):
        """Save current position"""
        # Save notes state too
        notes_state = {}
        for row in range(9):
            for col in range(9):
                cell = self.grid.cells[row][col]
                if cell.notes_enabled:
                    notes_state[(row, col)] = {
                        'enabled': True,
                        'mode': cell.notes_mode,
                        'candidates': cell.candidates.copy(),
                        'manual_candidates': cell.manual_candidates.copy()
                    }
        
        name = self.game.save_bookmark()
        self.bookmarks_list.addItem(name)
        
        # Store notes state in bookmark
        if self.game.bookmarks:
            self.game.bookmarks[-1]['notes_state'] = notes_state
    
    def load_bookmark(self):
        """Load last bookmark"""
        if not self.game.bookmarks:
            return
        
        index = len(self.game.bookmarks) - 1
        if self.game.load_bookmark(index):
            # Restore notes
            bookmark = self.game.bookmarks[index]
            notes_state = bookmark.get('notes_state', {})
            
            # Clear all notes first
            for row in range(9):
                for col in range(9):
                    cell = self.grid.cells[row][col]
                    cell.notes_enabled = False
                    cell.candidates.clear()
                    cell.manual_candidates.clear()
            
            # Restore saved notes
            for (row, col), state in notes_state.items():
                cell = self.grid.cells[row][col]
                cell.notes_enabled = state['enabled']
                cell.notes_mode = state.get('mode', 'auto')
                cell.candidates = state['candidates'].copy()
                cell.manual_candidates = state.get('manual_candidates', set()).copy()
            
            self.refresh_grid()
            self.update_stats()
            self.update_progress()
    
    def on_bookmark_selected(self, item):
        """Load selected bookmark"""
        index = self.bookmarks_list.row(item)
        if self.game.load_bookmark(index):
            # Restore notes
            bookmark = self.game.bookmarks[index]
            notes_state = bookmark.get('notes_state', {})
            
            for row in range(9):
                for col in range(9):
                    cell = self.grid.cells[row][col]
                    if (row, col) in notes_state:
                        state = notes_state[(row, col)]
                        cell.notes_enabled = state['enabled']
                        cell.notes_mode = state.get('mode', 'auto')
                        cell.candidates = state['candidates'].copy()
                        cell.manual_candidates = state.get('manual_candidates', set()).copy()
                    else:
                        cell.notes_enabled = False
                        cell.candidates.clear()
                        cell.manual_candidates.clear()
            
            self.refresh_grid()
            self.update_stats()
            self.update_progress()
    
    # ========================================
    # VALIDATION
    # ========================================
    
    def toggle_show_errors_checkbox(self, state):
        """Toggle show errors from checkbox"""
        self.game.show_errors = (Qt.CheckState(state) == Qt.CheckState.Checked)
        self.update_error_display()
    
    def toggle_shade_candidates(self):
        """Toggle candidate shading"""
        self.game.toggle_shade_candidates()
        self.update_candidate_highlighting()

    def toggle_highlight_naked_singles(self):
        """Toggle naked singles highlighting"""
        # State is tracked by the action's checked state
        self.update_candidate_highlighting()

    def toggle_highlight_hidden_singles(self):
        """Toggle hidden singles highlighting"""
        # State is tracked by the action's checked state
        self.update_candidate_highlighting()

    def recalculate_all_shading(self):
        """Recalculate all shading after a placement"""
        self.clear_hint_borders()
        self.update_candidate_highlighting()
    
    def update_error_flags(self):
        """
        Update error tracking flags (not display!)
        This keeps the error state accurate at all times
        Display is controlled separately by update_error_display()
        """
        errors = self.game.get_errors()
        for row in range(9):
            for col in range(9):
                cell = self.grid.cells[row][col]
                # Set tracking flag only - don't touch display flag
                cell.is_error = (row, col) in errors
    
    def update_error_display(self):
        """
        Update error highlighting visibility based on show_errors state
        Error tracking flags (is_error) are already set by update_error_flags()
        This just controls whether they're visible (error_display_on)
        """
        for row in range(9):
            for col in range(9):
                cell = self.grid.cells[row][col]
                if self.game.show_errors:
                    # Copy tracking flag to display flag
                    cell.error_display_on = cell.is_error
                else:
                    # Hide errors (but keep tracking)
                    cell.error_display_on = False
                cell.update()
    
    # ========================================
    # STATS AND PROGRESS
    # ========================================
    
    def update_stats(self):
        """Update stats labels"""
        self.moves_label.setText(f"Moves: {self.game.move_count}")
        self.hints_label.setText(f"Hints: {self.game.hint_count}")
    
    def update_progress(self):
        """Update progress"""
        filled, total, percent = self.game.get_progress()
        self.progress_label.setText(f"Progress: {percent:.0f}% ({filled}/{total})")
        
        if self.game.is_complete():
            self.show_completion()
    
    def update_timer(self):
        """Update timer"""
        self.game.timer_seconds += 1
        mins = self.game.timer_seconds // 60
        secs = self.game.timer_seconds % 60
        self.timer_label.setText(f"{mins:02d}:{secs:02d}")
    
    def show_completion(self):
        """Show completion message"""
        self.timer.stop()
        self.game.mark_puzzle_solved()
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Congratulations!")
        msg.setText(f"🎉 Puzzle Solved! 🎉\n\n" +
                   f"Time: {self.timer_label.text()}\n" +
                   f"Moves: {self.game.move_count}\n" +
                   f"Hints: {self.game.hint_count}")
        
        replay_btn = msg.addButton("Replay", QMessageBox.ButtonRole.ActionRole)
        new_btn = msg.addButton("New Puzzle", QMessageBox.ButtonRole.ActionRole)
        msg.addButton(QMessageBox.StandardButton.Ok)
        
        msg.exec()
        
        if msg.clickedButton() == replay_btn:
            if self.game.current_puzzle_string:
                self.game.start_game_from_string(
                    self.game.current_puzzle_string,
                    self.game.current_difficulty
                )
                self.refresh_grid()
                self.update_stats()
                self.update_progress()
                self.timer.start(1000)
        elif msg.clickedButton() == new_btn:
            self.select_and_start_game()
            self.timer.start(1000)
        else:
            self.timer.start(1000)
    
    # ========================================
    # KEYBOARD
    # ========================================
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard input"""
        key = event.key()
        if Qt.Key.Key_1 <= key <= Qt.Key.Key_9:
            num = key - Qt.Key.Key_0
            self.select_number_button(num)
        elif key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace, Qt.Key.Key_0):
            self.select_number_button(0)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--puzzle", type=str, default=None,
                        help="Load a custom puzzle by name and skip the selection screen")
    args, _ = parser.parse_known_args()

    app = QApplication(sys.argv)
    app.setApplicationName("Sudoku Trainer")

    window = SudokuPlayerWindow(skip_dialog=bool(args.puzzle))
    window.show()

    if args.puzzle:
        puzzles = CustomPuzzleLibrary.load_all()
        if args.puzzle in puzzles:
            puzzle_str = puzzles[args.puzzle]["puzzle"]
            window.start_custom_game(puzzle_str, args.puzzle)
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(window, "Puzzle Not Found",
                                f"No custom puzzle named {chr(39)}{args.puzzle}{chr(39)}.")

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
