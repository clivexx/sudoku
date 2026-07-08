#!/usr/bin/env python3
"""
Sudoku Puzzle Generator
Standalone application to generate and save puzzles to library
"""

import sys
import os
import random

# Setup paths
script_dir = os.path.dirname(os.path.abspath(__file__))
player_dir = os.path.join(script_dir, 'player')
shared_dir = os.path.join(script_dir, 'shared')
sys.path.insert(0, player_dir)
sys.path.insert(0, shared_dir)

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QSpinBox, QSlider, QProgressBar, 
                             QTextEdit, QCheckBox, QComboBox, QMessageBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

from sudoku_library import PuzzleLibrary
from sudoku_solver import SudokuSolver
from sudoku_analyzer import SudokuAnalyzer


class PuzzleGenerator:
    """Generates Sudoku puzzles"""
    
    @staticmethod
    def generate_solution():
        """Generate a valid Sudoku solution"""
        grid = [[0]*9 for _ in range(9)]
        
        def is_valid(grid, row, col, num):
            for x in range(9):
                if grid[row][x] == num or grid[x][col] == num:
                    return False
            start_row = (row // 3) * 3
            start_col = (col // 3) * 3
            for i in range(3):
                for j in range(3):
                    if grid[start_row + i][start_col + j] == num:
                        return False
            return True
        
        def solve(grid):
            for row in range(9):
                for col in range(9):
                    if grid[row][col] == 0:
                        numbers = list(range(1, 10))
                        random.shuffle(numbers)
                        for num in numbers:
                            if is_valid(grid, row, col, num):
                                grid[row][col] = num
                                if solve(grid):
                                    return True
                                grid[row][col] = 0
                        return False
            return True
        
        solve(grid)
        return grid
    
    @staticmethod
    def create_puzzle(solution, empty_cells):
        """Create puzzle by removing cells"""
        puzzle = [row[:] for row in solution]
        
        cells = [(r, c) for r in range(9) for c in range(9)]
        random.shuffle(cells)
        
        empty_count = 0
        
        for row, col in cells:
            if empty_count >= empty_cells:
                break
            
            if puzzle[row][col] != 0:
                saved_value = puzzle[row][col]
                puzzle[row][col] = 0
                
                # Check uniqueness
                if SudokuSolver.count_solutions(puzzle, max_count=2) == 1:
                    empty_count += 1
                else:
                    puzzle[row][col] = saved_value
        
        return puzzle
    
    @staticmethod
    def analyze_difficulty(puzzle):
        """Analyze puzzle difficulty using the analyzer"""
        # Use the analyzer to determine difficulty
        # This is a simplified version - you can enhance it
        empty_count = sum(1 for row in puzzle for cell in row if cell == 0)
        
        if empty_count <= 35:
            return 'Beginner'
        elif empty_count <= 40:
            return 'Easy'
        elif empty_count <= 50:
            return 'Medium'
        elif empty_count <= 55:
            return 'Hard'
        else:
            return 'Expert'


class GeneratorThread(QThread):
    """Background thread for generating puzzles"""
    
    progress_signal = pyqtSignal(dict)
    puzzle_found_signal = pyqtSignal(str, str)
    
    def __init__(self, target_difficulty, empty_cells, target_count, auto_save):
        super().__init__()
        self.target_difficulty = target_difficulty
        self.empty_cells = empty_cells
        self.target_count = target_count
        self.auto_save = auto_save
        self.running = True
        self.paused = False
        
        self.stats = {
            'attempts': 0,
            'beginner': 0,
            'easy': 0,
            'medium': 0,
            'hard': 0,
            'expert': 0,
            'saved': 0
        }
    
    def run(self):
        """Generate puzzles"""
        while self.running and self.stats['saved'] < self.target_count:
            if self.paused:
                self.msleep(100)
                continue
            
            # Generate solution and puzzle
            solution = PuzzleGenerator.generate_solution()
            puzzle = PuzzleGenerator.create_puzzle(solution, self.empty_cells)
            
            # Analyze difficulty
            difficulty = PuzzleGenerator.analyze_difficulty(puzzle)
            
            # Update stats
            self.stats['attempts'] += 1
            self.stats[difficulty.lower()] += 1
            
            # Save if matches target
            if difficulty == self.target_difficulty and self.auto_save:
                puzzle_str = ''.join(str(cell) for row in puzzle for cell in row)
                PuzzleLibrary.save_puzzle(difficulty, puzzle_str)
                self.stats['saved'] += 1
                self.puzzle_found_signal.emit(puzzle_str, difficulty)
            
            # Emit progress
            self.progress_signal.emit(self.stats.copy())
    
    def pause(self):
        self.paused = True
    
    def resume(self):
        self.paused = False
    
    def stop(self):
        self.running = False


class GeneratorWindow(QMainWindow):
    """Puzzle Generator Application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sudoku Puzzle Generator")
        self.resize(600, 500)
        
        self.generator_thread = None
        
        self.init_ui()
    
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        central.setLayout(layout)
        
        # Title
        title = QLabel("Sudoku Puzzle Generator")
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Target difficulty
        diff_layout = QHBoxLayout()
        diff_layout.addWidget(QLabel("Target Difficulty:"))
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(['Beginner', 'Easy', 'Medium', 'Hard', 'Expert'])
        self.difficulty_combo.setCurrentText('Easy')
        diff_layout.addWidget(self.difficulty_combo)
        layout.addLayout(diff_layout)
        
        # Empty cells slider
        empty_label = QLabel("Empty Cells:")
        empty_label_detail = QLabel("Beginner: 30-35 | Easy: 35-40 | Medium: 40-50 | Hard: 50-55 | Expert: 55-60")
        empty_label_detail.setStyleSheet("color: gray; font-size: 9px;")
        layout.addWidget(empty_label)
        layout.addWidget(empty_label_detail)
        
        slider_layout = QHBoxLayout()
        self.empty_slider = QSlider(Qt.Orientation.Horizontal)
        self.empty_slider.setMinimum(30)
        self.empty_slider.setMaximum(60)
        self.empty_slider.setValue(40)
        self.empty_slider.valueChanged.connect(self.update_empty_label)
        slider_layout.addWidget(self.empty_slider)
        
        self.empty_label = QLabel("40")
        self.empty_label.setMinimumWidth(30)
        slider_layout.addWidget(self.empty_label)
        
        layout.addLayout(slider_layout)
        
        # Target count
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("Target Count:"))
        self.count_spin = QSpinBox()
        self.count_spin.setMinimum(1)
        self.count_spin.setMaximum(10000)
        self.count_spin.setValue(100)
        count_layout.addWidget(self.count_spin)
        count_layout.addStretch()
        layout.addLayout(count_layout)
        
        # Auto-save checkbox
        self.autosave_check = QCheckBox("Automatically save matching puzzles to library")
        self.autosave_check.setChecked(True)
        layout.addWidget(self.autosave_check)
        
        # Status
        self.status_label = QLabel("Status: Ready")
        self.status_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # Stats display
        stats_label = QLabel("Statistics:")
        layout.addWidget(stats_label)
        
        self.stats_text = QTextEdit()
        self.stats_text.setMaximumHeight(120)
        self.stats_text.setReadOnly(True)
        self.stats_text.setFont(QFont('Courier', 9))
        layout.addWidget(self.stats_text)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Generation")
        self.start_btn.clicked.connect(self.start_generation)
        self.start_btn.setFont(QFont('Arial', 11, QFont.Weight.Bold))
        button_layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause_generation)
        self.pause_btn.setEnabled(False)
        button_layout.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_generation)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        layout.addLayout(button_layout)
        
        # Library stats button
        library_btn = QPushButton("View Library Statistics")
        library_btn.clicked.connect(self.show_library_stats)
        layout.addWidget(library_btn)
    
    def update_empty_label(self):
        self.empty_label.setText(str(self.empty_slider.value()))
    
    def start_generation(self):
        """Start background generation"""
        target_difficulty = self.difficulty_combo.currentText()
        empty_cells = self.empty_slider.value()
        target_count = self.count_spin.value()
        auto_save = self.autosave_check.isChecked()
        
        self.generator_thread = GeneratorThread(
            target_difficulty, empty_cells, target_count, auto_save
        )
        
        self.generator_thread.progress_signal.connect(self.update_progress)
        self.generator_thread.puzzle_found_signal.connect(self.puzzle_found)
        self.generator_thread.finished.connect(self.generation_finished)
        
        self.generator_thread.start()
        
        self.status_label.setText(f"Status: Generating {target_difficulty} puzzles...")
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
    
    def pause_generation(self):
        """Pause/resume generation"""
        if self.generator_thread:
            if self.generator_thread.paused:
                self.generator_thread.resume()
                self.pause_btn.setText("Pause")
                self.status_label.setText("Status: Generating...")
            else:
                self.generator_thread.pause()
                self.pause_btn.setText("Resume")
                self.status_label.setText("Status: Paused")
    
    def stop_generation(self):
        """Stop generation"""
        if self.generator_thread:
            self.generator_thread.stop()
            self.generator_thread.wait()
        self.generation_finished()
    
    def update_progress(self, stats):
        """Update progress display"""
        total = stats['attempts']
        saved = stats['saved']
        target = self.count_spin.value()
        
        self.progress_bar.setValue(int((saved / target) * 100))
        
        stats_text = f"Attempts: {total}\n\n"
        
        if total > 0:
            stats_text += f"Beginner: {stats['beginner']:4d} ({stats['beginner']/total*100:5.1f}%)\n"
            stats_text += f"Easy:     {stats['easy']:4d} ({stats['easy']/total*100:5.1f}%)\n"
            stats_text += f"Medium:   {stats['medium']:4d} ({stats['medium']/total*100:5.1f}%)\n"
            stats_text += f"Hard:     {stats['hard']:4d} ({stats['hard']/total*100:5.1f}%)\n"
            stats_text += f"Expert:   {stats['expert']:4d} ({stats['expert']/total*100:5.1f}%)\n"
        
        stats_text += f"\nSaved: {saved} / {target}"
        
        self.stats_text.setText(stats_text)
    
    def puzzle_found(self, puzzle_str, difficulty):
        """Called when matching puzzle is saved"""
        pass
    
    def generation_finished(self):
        """Called when generation completes"""
        self.status_label.setText("Status: Finished")
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        
        if self.generator_thread and self.generator_thread.stats['saved'] > 0:
            QMessageBox.information(self, "Generation Complete",
                f"Generated {self.generator_thread.stats['saved']} puzzles!\n" +
                f"Total attempts: {self.generator_thread.stats['attempts']}")
    
    def show_library_stats(self):
        """Show library statistics"""
        stats_text = "LIBRARY STATISTICS\n" + "="*40 + "\n\n"
        
        for difficulty in ['Beginner', 'Easy', 'Medium', 'Hard', 'Expert']:
            stats = PuzzleLibrary.get_stats(difficulty)
            stats_text += f"{difficulty:10s}: {stats['unsolved']:4d} unsolved, {stats['solved']:4d} solved ({stats['total']:4d} total)\n"
        
        QMessageBox.information(self, "Library Statistics", stats_text)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Sudoku Generator")
    
    window = GeneratorWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
