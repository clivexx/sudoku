"""
Sudoku Trainer - Puzzle Library Management
Handles loading, saving, and managing puzzles (both generated and custom)
"""

import os
import json
from datetime import datetime
from sudoku_constants import PUZZLE_FILES, CUSTOM_PUZZLES_FILE


class PuzzleLibrary:
    """Manages generated puzzle storage and retrieval"""
    
    @staticmethod
    def load_puzzles(difficulty):
        """Load puzzles from file with enhanced format"""
        filename = PUZZLE_FILES.get(difficulty)
        if not filename or not os.path.exists(filename):
            return []
        
        puzzles = []
        try:
            with open(filename, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parse: puzzle,status,date_added,date_solved,comment
                    parts = line.split(',')
                    
                    puzzle_data = {
                        'puzzle': parts[0],
                        'status': parts[1] if len(parts) > 1 else 'unsolved',
                        'date_added': parts[2] if len(parts) > 2 else '',
                        'date_solved': parts[3] if len(parts) > 3 else '',
                        'comment': parts[4] if len(parts) > 4 else ''
                    }
                    puzzles.append(puzzle_data)
        except Exception as e:
            print(f"Error loading puzzles: {e}")
        
        return puzzles
    
    @staticmethod
    def save_puzzle(difficulty, puzzle_str, status='unsolved', comment=''):
        """Save a puzzle to library with enhanced format"""
        filename = PUZZLE_FILES.get(difficulty)
        if not filename:
            return False
        
        try:
            # Create library directory if it doesn't exist
            dirname = os.path.dirname(filename)
            if dirname:  # Only if there's a directory component
                os.makedirs(dirname, exist_ok=True)
            
            date_added = datetime.now().strftime('%Y-%m-%d')
            date_solved = ''
            
            with open(filename, 'a') as f:
                f.write(f"{puzzle_str},{status},{date_added},{date_solved},{comment}\n")
            return True
        except Exception as e:
            print(f"Error saving puzzle: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def update_puzzle_status(difficulty, puzzle_str, status, solved=False):
        """Update puzzle status (mark as solved/unsolved)"""
        filename = PUZZLE_FILES.get(difficulty)
        if not filename or not os.path.exists(filename):
            return False
        
        try:
            puzzles = PuzzleLibrary.load_puzzles(difficulty)
            date_solved = datetime.now().strftime('%Y-%m-%d') if solved else ''
            
            with open(filename, 'w') as f:
                for p in puzzles:
                    if p['puzzle'] == puzzle_str:
                        p['status'] = status
                        if solved:
                            p['date_solved'] = date_solved
                    f.write(f"{p['puzzle']},{p['status']},{p['date_added']},{p['date_solved']},{p['comment']}\n")
            return True
        except Exception as e:
            print(f"Error updating puzzle status: {e}")
            return False
    
    @staticmethod
    def update_puzzle_comment(difficulty, puzzle_str, comment):
        """Update puzzle comment"""
        filename = PUZZLE_FILES.get(difficulty)
        if not filename or not os.path.exists(filename):
            return False
        
        try:
            puzzles = PuzzleLibrary.load_puzzles(difficulty)
            
            with open(filename, 'w') as f:
                for p in puzzles:
                    if p['puzzle'] == puzzle_str:
                        p['comment'] = comment
                    f.write(f"{p['puzzle']},{p['status']},{p['date_added']},{p['date_solved']},{p['comment']}\n")
            return True
        except Exception as e:
            print(f"Error updating puzzle comment: {e}")
            return False
    
    @staticmethod
    def replace_puzzle(difficulty, old_puzzle_str, new_puzzle_str):
        """Replace a solved puzzle with a new one"""
        filename = PUZZLE_FILES.get(difficulty)
        if not filename or not os.path.exists(filename):
            return False
        
        try:
            puzzles = PuzzleLibrary.load_puzzles(difficulty)
            date_added = datetime.now().strftime('%Y-%m-%d')
            
            with open(filename, 'w') as f:
                for p in puzzles:
                    if p['puzzle'] == old_puzzle_str:
                        # Replace with new puzzle
                        f.write(f"{new_puzzle_str},unsolved,{date_added},,\n")
                    else:
                        f.write(f"{p['puzzle']},{p['status']},{p['date_added']},{p['date_solved']},{p['comment']}\n")
            return True
        except Exception as e:
            print(f"Error replacing puzzle: {e}")
            return False
    
    @staticmethod
    def get_stats(difficulty):
        """Get library statistics"""
        puzzles = PuzzleLibrary.load_puzzles(difficulty)
        total = len(puzzles)
        unsolved = sum(1 for p in puzzles if p['status'] == 'unsolved')
        solved = total - unsolved
        return {'total': total, 'unsolved': unsolved, 'solved': solved}
    
    @staticmethod
    def select_puzzle(difficulty):
        """Select a puzzle (priority to unsolved)"""
        puzzles = PuzzleLibrary.load_puzzles(difficulty)
        if not puzzles:
            return None
        
        # Priority: unsolved first
        unsolved = [p for p in puzzles if p['status'] == 'unsolved']
        if unsolved:
            import random
            return random.choice(unsolved)['puzzle']
        
        # Fallback: random solved
        import random
        return random.choice(puzzles)['puzzle']


class CustomPuzzleLibrary:
    """Manages custom user-created puzzle storage (JSON-based)"""
    
    @staticmethod
    def load_all():
        """Load all custom puzzles"""
        if not os.path.exists(CUSTOM_PUZZLES_FILE):
            return {}
        
        try:
            with open(CUSTOM_PUZZLES_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading custom puzzles: {e}")
            return {}
    
    @staticmethod
    def save_all(puzzles):
        """Save all custom puzzles"""
        try:
            # Create library directory if it doesn't exist
            dirname = os.path.dirname(CUSTOM_PUZZLES_FILE)
            if dirname:  # Only if there's a directory component
                os.makedirs(dirname, exist_ok=True)
            
            with open(CUSTOM_PUZZLES_FILE, 'w') as f:
                json.dump(puzzles, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving custom puzzles: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def add_puzzle(title, puzzle_str, difficulty, comment=''):
        """Add a new custom puzzle"""
        puzzles = CustomPuzzleLibrary.load_all()
        
        # Ensure unique title
        original_title = title
        counter = 1
        while title in puzzles:
            title = f"{original_title} ({counter})"
            counter += 1
        
        puzzles[title] = {
            'puzzle': puzzle_str,
            'difficulty': difficulty,
            'status': 'unsolved',
            'date_added': datetime.now().strftime('%Y-%m-%d'),
            'date_solved': None,
            'comment': comment
        }
        
        return CustomPuzzleLibrary.save_all(puzzles)
    
    @staticmethod
    def update_puzzle(title, puzzle_data):
        """Update existing custom puzzle"""
        puzzles = CustomPuzzleLibrary.load_all()
        
        if title not in puzzles:
            return False
        
        puzzles[title].update(puzzle_data)
        return CustomPuzzleLibrary.save_all(puzzles)
    
    @staticmethod
    def rename_puzzle(old_title, new_title):
        """Rename a custom puzzle"""
        puzzles = CustomPuzzleLibrary.load_all()
        
        if old_title not in puzzles or new_title in puzzles:
            return False
        
        puzzles[new_title] = puzzles.pop(old_title)
        return CustomPuzzleLibrary.save_all(puzzles)
    
    @staticmethod
    def delete_puzzle(title):
        """Delete a custom puzzle"""
        puzzles = CustomPuzzleLibrary.load_all()
        
        if title not in puzzles:
            return False
        
        del puzzles[title]
        return CustomPuzzleLibrary.save_all(puzzles)
    
    @staticmethod
    def mark_solved(title):
        """Mark custom puzzle as solved"""
        puzzles = CustomPuzzleLibrary.load_all()
        
        if title not in puzzles:
            return False
        
        puzzles[title]['status'] = 'solved'
        puzzles[title]['date_solved'] = datetime.now().strftime('%Y-%m-%d')
        return CustomPuzzleLibrary.save_all(puzzles)
    
    @staticmethod
    def get_stats():
        """Get custom puzzle statistics"""
        puzzles = CustomPuzzleLibrary.load_all()
        total = len(puzzles)
        unsolved = sum(1 for p in puzzles.values() if p['status'] == 'unsolved')
        solved = total - unsolved
        return {'total': total, 'unsolved': unsolved, 'solved': solved}
