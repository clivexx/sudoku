#!/usr/bin/env python3
"""
Sudoku Player - Main Entry Point
Minimal working version - can be enhanced
"""

import sys
import os

# Add current directory and parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QMessageBox, QScrollArea, QFrame)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QKeyEvent

from sudoku_grid import SudokuGrid
from sudoku_game import SudokuGame
from shared.sudoku_library import PuzzleLibrary
from shared.sudoku_analyzer import SudokuAnalyzer


class MinimalPlayerWindow(QMainWindow):
    """Minimal playable Sudoku interface"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sudoku Player")
        self.resize(900, 700)
        
        # Create game logic
        self.game = SudokuGame()

        # Elimination mode state
        self.elimination_mode = False
        self.elimination_patterns = []  # List of hint dicts
        self.pattern_reveal_levels = []  # Reveal level (0-5) for each pattern

        # Create UI
        self.init_ui()
        
        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)
        
        # Load a puzzle
        self.load_puzzle()
    
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout()
        central.setLayout(main_layout)
        
        # Left panel
        left_panel = QVBoxLayout()
        
        title = QLabel("Sudoku Player")
        title.setFont(QFont('Arial', 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        left_panel.addWidget(title)
        
        self.timer_label = QLabel("00:00")
        self.timer_label.setFont(QFont('Arial', 14))
        self.timer_label.setAlignment(Qt.AlignCenter)
        left_panel.addWidget(self.timer_label)
        
        self.progress_label = QLabel("Progress: 0%")
        self.progress_label.setAlignment(Qt.AlignCenter)
        left_panel.addWidget(self.progress_label)
        
        # Buttons
        new_btn = QPushButton("New Puzzle")
        new_btn.clicked.connect(self.load_puzzle)
        left_panel.addWidget(new_btn)
        
        undo_btn = QPushButton("Undo")
        undo_btn.clicked.connect(self.undo)
        left_panel.addWidget(undo_btn)
        
        hint_btn = QPushButton("Get Hint")
        hint_btn.clicked.connect(self.show_hint)
        left_panel.addWidget(hint_btn)
        
        self.hint_label = QLabel("")
        self.hint_label.setWordWrap(True)
        self.hint_label.setStyleSheet("background-color: #E3F2FD; padding: 5px;")
        left_panel.addWidget(self.hint_label)

        # Elimination mode panel (hidden initially)
        self.elimination_panel = QFrame()
        self.elimination_panel.setFrameStyle(QFrame.StyledPanel)
        self.elimination_panel.setStyleSheet("background-color: #FFF3E0; border-radius: 5px;")
        elim_layout = QVBoxLayout(self.elimination_panel)
        elim_layout.setContentsMargins(5, 5, 5, 5)

        # Header with count and close button
        header_layout = QHBoxLayout()
        self.elim_count_label = QLabel("0 patterns found")
        self.elim_count_label.setFont(QFont('Arial', 10, QFont.Bold))
        header_layout.addWidget(self.elim_count_label)
        close_btn = QPushButton("X")
        close_btn.setMaximumSize(25, 25)
        close_btn.clicked.connect(self.exit_elimination_mode)
        header_layout.addWidget(close_btn)
        elim_layout.addLayout(header_layout)

        # Scrollable area for pattern list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(300)
        self.pattern_list_widget = QWidget()
        self.pattern_list_layout = QVBoxLayout(self.pattern_list_widget)
        self.pattern_list_layout.setSpacing(2)
        scroll_area.setWidget(self.pattern_list_widget)
        elim_layout.addWidget(scroll_area)

        self.elimination_panel.hide()
        left_panel.addWidget(self.elimination_panel)

        left_panel.addStretch()
        
        # Grid - pass window so cells can trigger display refresh
        self.grid = SudokuGrid(self)
        
        # Right panel - number buttons
        right_panel = QVBoxLayout()
        self.number_buttons = []
        for num in range(1, 10):
            btn = QPushButton(str(num))
            btn.setMinimumSize(60, 60)
            btn.setFont(QFont('Arial', 18, QFont.Bold))
            btn.clicked.connect(lambda checked, n=num: self.select_number(n))
            right_panel.addWidget(btn)
            self.number_buttons.append(btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(lambda: self.select_number(0))
        right_panel.addWidget(clear_btn)
        
        right_panel.addStretch()
        
        # Add panels to main layout
        main_layout.addLayout(left_panel, 1)
        main_layout.addWidget(self.grid, 3)
        main_layout.addLayout(right_panel, 1)
    
    def load_puzzle(self):
        """Load a puzzle from library"""
        # Try to get an Easy puzzle
        puzzle_str = PuzzleLibrary.select_puzzle('Easy')
        if not puzzle_str:
            # Try Medium
            puzzle_str = PuzzleLibrary.select_puzzle('Medium')

        if puzzle_str:
            self.start_new_puzzle(puzzle_str, 'Easy')
        else:
            QMessageBox.warning(self, "No Puzzles", "No puzzles available. Please generate some first.")

    def start_new_puzzle(self, puzzle_str, difficulty):
        """Single entry point for all new puzzle initialization"""
        # Reset game state
        self.game.start_game_from_string(puzzle_str, difficulty)

        # Reset all cells and set values
        for row in range(9):
            for col in range(9):
                cell = self.grid.cells[row][col]
                cell.reset()
                value = self.game.board[row][col]
                is_initial = (self.game.initial_board[row][col] != 0)
                cell.set_value(value, is_initial)

        # Reset UI state
        self.hint_label.setText("")
        self.update_button_styles()
        self.update_progress()

        # Exit elimination mode if active
        if self.elimination_mode:
            self.exit_elimination_mode()

    def refresh_grid(self):
        """Refresh cell values from game state (for undo, etc.)"""
        for row in range(9):
            for col in range(9):
                value = self.game.board[row][col]
                is_initial = (self.game.initial_board[row][col] != 0)
                self.grid.cells[row][col].set_value(value, is_initial)
    
    def select_number(self, num):
        """Select a number"""
        self.game.select_number(num)
        self.update_button_styles()
        self.update_cell_shading()
    
    def update_button_styles(self):
        """Update button appearance"""
        for i, btn in enumerate(self.number_buttons):
            num = i + 1
            if num == self.game.selected_number:
                btn.setStyleSheet("background-color: #FF6B6B; color: white;")
            else:
                btn.setStyleSheet("")

    def update_cell_shading(self):
        """Update cell shading based on selected number and singletons"""
        selected = self.game.selected_number
        for row in range(9):
            for col in range(9):
                cell = self.grid.cells[row][col]
                cell.is_candidate = False
                cell.is_singleton = False

                # Skip filled cells
                if self.game.board[row][col] != 0:
                    cell.update()
                    continue

                if self.game.shade_candidates:
                    # Check for singleton (only one candidate possible)
                    candidates = [n for n in range(1, 10)
                                  if self.game.can_place_number(row, col, n)]
                    if len(candidates) == 1:
                        cell.is_singleton = True
                    elif selected and selected != 0:
                        # Highlight cells where selected number can be placed
                        if self.game.can_place_number(row, col, selected):
                            cell.is_candidate = True

                cell.update()

    def can_place_number(self, row, col, num):
        """Delegate to game - used by cells for candidate calculation"""
        return self.game.can_place_number(row, col, num)

    def handle_cell_click(self, row, col):
        """Handle cell click - place number and refresh display"""
        if self.game.handle_cell_click(row, col):
            self.refresh_after_move()

    def refresh_after_move(self):
        """Refresh display after placing a number"""
        self.refresh_grid()
        self.update_cell_shading()
        self.update_progress()
        # Recalculate auto-notes if enabled
        if self.game.auto_notes_enabled:
            self.game.recalculate_affected_notes(self.grid.cells)
        # Exit elimination mode when a number is placed
        if self.elimination_mode:
            self.exit_elimination_mode()

    def enter_elimination_mode(self, patterns):
        """Enter elimination mode with found patterns"""
        self.elimination_mode = True
        self.elimination_patterns = patterns
        self.pattern_reveal_levels = [0] * len(patterns)  # All start at level 0
        self.pattern_row_widgets = []  # Store row widgets for updates

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
            label.setMinimumWidth(150)
            row_layout.addWidget(label, 1)

            more_btn = QPushButton("More")
            more_btn.setMaximumWidth(50)
            more_btn.clicked.connect(lambda checked, idx=i: self.reveal_pattern_more(idx))
            row_layout.addWidget(more_btn)

            self.pattern_list_layout.addWidget(row_widget)
            self.pattern_row_widgets.append({'widget': row_widget, 'label': label, 'button': more_btn})

        self.pattern_list_layout.addStretch()

        # Update display
        self.elim_count_label.setText(f"{len(patterns)} patterns found")
        self.hint_label.setText("")
        self.elimination_panel.show()

    def exit_elimination_mode(self):
        """Exit elimination mode, back to normal play"""
        self.elimination_mode = False
        self.elimination_patterns = []
        self.pattern_reveal_levels = []
        self.pattern_row_widgets = []
        self.hint_label.setText("")
        self.elimination_panel.hide()

    def reveal_pattern_more(self, pattern_idx):
        """Reveal more detail for a specific pattern"""
        if pattern_idx >= len(self.elimination_patterns):
            return

        # Increment reveal level (max 5)
        current_level = self.pattern_reveal_levels[pattern_idx]
        if current_level < 5:
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

        # Disable button at max level
        if level >= 5:
            row['button'].setEnabled(False)
            row['button'].setText("Done")

    def update_elimination_display(self):
        """Update the elimination mode UI"""
        if not self.elimination_mode:
            return
        # Refresh all pattern rows
        for i in range(len(self.elimination_patterns)):
            self.update_pattern_row(i)

    def undo(self):
        """Undo last move"""
        if self.game.undo():
            self.refresh_after_move()
    
    def show_hint(self):
        """Show a hint - placement hints first, then elimination patterns"""
        # If already in elimination mode, clicking hint does nothing
        # (user should use per-row "More" buttons)
        if self.elimination_mode:
            return

        # Check for placement hints first (singles)
        placement_hint = SudokuAnalyzer.find_placement_hint(self.game.board)
        if placement_hint:
            # Format and show placement hint
            message = SudokuAnalyzer._format_hint_level_1(placement_hint)
            self.hint_label.setText(message)
            if 'cell' in placement_hint:
                row, col = placement_hint['cell']
                self.grid.cells[row][col].border_highlight = True
                self.grid.cells[row][col].update()
            return

        # No placements available - find all elimination patterns
        patterns = SudokuAnalyzer.find_all_elimination_patterns(self.game.board)
        if patterns:
            self.enter_elimination_mode(patterns)
        else:
            self.hint_label.setText("No techniques available. The puzzle may require guessing.")
    
    def update_timer(self):
        """Update timer"""
        self.game.timer_seconds += 1
        mins = self.game.timer_seconds // 60
        secs = self.game.timer_seconds % 60
        self.timer_label.setText(f"{mins:02d}:{secs:02d}")
    
    def update_progress(self):
        """Update progress"""
        filled, total, percent = self.game.get_progress()
        self.progress_label.setText(f"Progress: {percent:.0f}% ({filled}/{total})")
        
        if self.game.is_complete():
            self.show_completion()
    
    def show_completion(self):
        """Show completion message"""
        self.game.mark_puzzle_solved()
        QMessageBox.information(self, "Congratulations!", 
            f"Puzzle solved!\n\nTime: {self.timer_label.text()}\nMoves: {self.game.move_count}")
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard input"""
        key = event.key()
        if Qt.Key_1 <= key <= Qt.Key_9:
            num = key - Qt.Key_0
            self.select_number(num)
        elif key in (Qt.Key_Delete, Qt.Key_Backspace):
            self.select_number(0)


def main():
    app = QApplication(sys.argv)
    window = MinimalPlayerWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
