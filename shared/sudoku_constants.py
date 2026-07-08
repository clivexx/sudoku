"""
Sudoku Trainer - Constants and Configuration
Shared constants used across all modules
"""

import os

# Project root directory (parent of 'shared')
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LIBRARY_DIR = os.path.join(_PROJECT_DIR, 'library')

# File paths
PUZZLE_FILES = {
    'Beginner': os.path.join(_LIBRARY_DIR, 'puzzles_beginner.txt'),
    'Easy': os.path.join(_LIBRARY_DIR, 'puzzles_easy.txt'),
    'Medium': os.path.join(_LIBRARY_DIR, 'puzzles_medium.txt'),
    'Hard': os.path.join(_LIBRARY_DIR, 'puzzles_hard.txt'),
    'Expert': os.path.join(_LIBRARY_DIR, 'puzzles_expert.txt')
}
CUSTOM_PUZZLES_FILE = os.path.join(_LIBRARY_DIR, 'puzzles_custom.json')

# Difficulty parameters
DIFFICULTY_EMPTY_RANGES = {
    'Beginner': (30, 35),
    'Easy': (35, 40),
    'Medium': (40, 50),
    'Hard': (50, 60),
    'Expert': (60, 65)
}

# Colors
class Colors:
    # Triangle colors
    TRIANGLE_OFF = (150, 220, 255)      # Bright cyan
    TRIANGLE_AUTO = (255, 255, 100)     # Bright yellow
    TRIANGLE_MANUAL = (100, 255, 100)   # Bright green
    
    # Cell backgrounds
    BG_ERROR = (255, 182, 198)          # Light red
    BG_SINGLETON = (80, 180, 80)        # Green
    BG_CANDIDATE = (144, 238, 144)      # Light green
    BG_INITIAL = (240, 240, 240)        # Light gray
    BG_NORMAL = (255, 255, 255)         # White
    BG_PATTERN = (144, 238, 144)        # Light green - cells forming the pattern
    BG_AFFECTED = (255, 255, 150)       # Light yellow - cells with eliminations
    BG_EXCLUDED = (255, 220, 220)       # Light pink - cells excluded by pattern
    
    # Other
    BORDER_HIGHLIGHT = (255, 20, 147)   # Deep pink
    SELECTED_BUTTON = (255, 107, 107)   # Red
    NORMAL_BUTTON = (224, 224, 224)     # Gray

# UI Dimensions
CELL_MIN_SIZE = 50
TRIANGLE_SIZE_RATIO = 0.35

# Fonts
FONT_TITLE = ('Arial', 20)
FONT_CELL_VALUE = ('Arial', 24)
FONT_CELL_VALUE_BOLD = ('Arial', 32)
FONT_CANDIDATE = ('Arial', 9)
FONT_BUTTON = ('Arial', 18)
FONT_LABEL = ('Arial', 10)

# Default values
DEFAULT_TARGET_PUZZLES = 100
DEFAULT_EMPTY_CELLS = 40
