"""
Sudoku Game Logic
Game state management, moves, hints, validation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from sudoku_solver import SudokuSolver
from sudoku_analyzer import SudokuAnalyzer
from sudoku_library import PuzzleLibrary


class SudokuGame:
    """Core game logic - no UI"""
    
    def __init__(self):
        # Board state
        self.board = [[0]*9 for _ in range(9)]
        self.solution = [[0]*9 for _ in range(9)]
        self.initial_board = [[0]*9 for _ in range(9)]
        self.current_puzzle_string = None
        self.current_difficulty = None
        
        # Game state
        self.selected_number = None
        self.move_count = 0
        self.hint_count = 0
        self.timer_seconds = 0
        
        # Settings
        self.auto_notes_enabled = False
        self.show_errors = False
        self.shade_candidates = False
        
        # History and bookmarks
        self.history = []
        self.bookmarks = []
        
        # Hints
        self.hints_list = []  # For UI hints panel
        
    def start_game_from_string(self, puzzle_str, difficulty=None):
        """Start game from 81-digit string"""
        # Convert string to board
        board = []
        for i in range(9):
            row = [int(puzzle_str[i*9 + j]) for j in range(9)]
            board.append(row)
        
        self.initial_board = board
        self.board = [row[:] for row in board]
        self.current_puzzle_string = puzzle_str
        self.current_difficulty = difficulty
        
        # Generate solution
        self.solution = SudokuSolver.solve(board)
        
        # Reset state
        self.selected_number = None
        self.move_count = 0
        self.hint_count = 0
        self.timer_seconds = 0
        self.history = []
        self.bookmarks = []

        # Reset display settings
        self.show_errors = False
        
        return True
    
    def handle_cell_click(self, row, col):
        """Handle placing a number in a cell"""
        if self.initial_board[row][col] != 0:
            return False  # Can't modify initial cells
            
        if self.selected_number is None:
            return False  # No number selected
        
        # Save move for undo
        move = {
            'row': row,
            'col': col,
            'old_value': self.board[row][col],
            'new_value': None
        }
        
        # Place or clear number
        if self.selected_number == 0:
            self.board[row][col] = 0
            move['new_value'] = 0
        else:
            self.board[row][col] = self.selected_number
            move['new_value'] = self.selected_number
        
        self.history.append(move)
        self.move_count += 1
        
        # DON'T clear selection - we want bold to persist!
        
        return True
    
    def select_number(self, num):
        """Select a number (0 = clear)"""
        if self.selected_number == num:
            self.selected_number = None
        else:
            self.selected_number = num
        return self.selected_number
    
    def can_place_number(self, row, col, num):
        """Check if number can be placed in cell"""
        if self.board[row][col] != 0:
            return False
        if self.initial_board[row][col] != 0:
            return False
            
        # Check row
        for x in range(9):
            if self.board[row][x] == num:
                return False
        
        # Check column
        for x in range(9):
            if self.board[x][col] == num:
                return False
        
        # Check 3x3 box
        start_row = (row // 3) * 3
        start_col = (col // 3) * 3
        for i in range(3):
            for j in range(3):
                if self.board[start_row + i][start_col + j] == num:
                    return False
        
        return True
    
    def undo(self):
        """Undo last move"""
        if not self.history:
            return False
            
        move = self.history.pop()
        row, col = move['row'], move['col']
        self.board[row][col] = move['old_value']
        self.move_count -= 1
        
        return True
    
    def save_bookmark(self):
        """Save current position"""
        bookmark = {
            'name': f"Position {len(self.bookmarks) + 1} (Move {self.move_count})",
            'board': [row[:] for row in self.board],
            'move_count': self.move_count,
            'history_length': len(self.history)
        }
        self.bookmarks.append(bookmark)
        return bookmark['name']
    
    def load_bookmark(self, index):
        """Load a saved position"""
        if 0 <= index < len(self.bookmarks):
            bookmark = self.bookmarks[index]
            self.board = [row[:] for row in bookmark['board']]
            self.move_count = bookmark['move_count']
            # Truncate history
            self.history = self.history[:bookmark['history_length']]
            return True
        return False
    
    def is_complete(self):
        """Check if puzzle is solved correctly"""
        for row in range(9):
            for col in range(9):
                if self.board[row][col] != self.solution[row][col]:
                    return False
        return True
    
    def get_errors(self):
        """Get list of cells with errors"""
        errors = []
        for row in range(9):
            for col in range(9):
                if self.board[row][col] != 0 and self.initial_board[row][col] == 0:
                    if self.board[row][col] != self.solution[row][col]:
                        errors.append((row, col))
        return errors
    
    def get_progress(self):
        """Get completion progress"""
        filled = sum(1 for row in range(9) for col in range(9) if self.board[row][col] != 0)
        return filled, 81, (filled / 81) * 100
    
    def count_remaining(self, num):
        """Count how many of a number can still be placed"""
        count = 9
        for row in range(9):
            for col in range(9):
                if self.board[row][col] == num or self.initial_board[row][col] == num:
                    count -= 1
        return count
    
    # ============================================================
    # AUTO NOTES
    # ============================================================
    
    def toggle_auto_notes(self, grid_cells):
        """Toggle auto notes on all cells"""
        self.auto_notes_enabled = not self.auto_notes_enabled
        
        if self.auto_notes_enabled:
            # Enable notes on all empty cells
            for row in range(9):
                for col in range(9):
                    if self.board[row][col] == 0 and self.initial_board[row][col] == 0:
                        grid_cells[row][col].notes_enabled = True
                        grid_cells[row][col].calculate_candidates()
        else:
            # Disable all notes
            for row in range(9):
                for col in range(9):
                    grid_cells[row][col].notes_enabled = False
                    grid_cells[row][col].candidates.clear()
        
        return self.auto_notes_enabled
    
    def recalculate_affected_notes(self, grid_cells):
        """Recalculate notes after a move"""
        for row in range(9):
            for col in range(9):
                if grid_cells[row][col].notes_enabled and grid_cells[row][col].notes_mode == 'auto':
                    grid_cells[row][col].calculate_candidates()
    
    # ============================================================
    # VALIDATION
    # ============================================================
    
    def toggle_show_errors(self):
        """Toggle error display"""
        self.show_errors = not self.show_errors
        return self.show_errors
    
    def toggle_shade_candidates(self):
        """Toggle candidate shading"""
        self.shade_candidates = not self.shade_candidates
        return self.shade_candidates
    
    # ============================================================
    # COMPLETION
    # ============================================================
    
    def mark_puzzle_solved(self):
        """Mark puzzle as solved in library"""
        if self.current_puzzle_string and self.current_difficulty:
            PuzzleLibrary.update_puzzle_status(
                self.current_difficulty,
                self.current_puzzle_string,
                'solved',
                solved=True
            )
