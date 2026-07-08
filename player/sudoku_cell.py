"""
Sudoku Cell Widget
Individual cell with triangle-based notes
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QPolygon, QBrush, QFont
from sudoku_constants import Colors


class SudokuCell(QWidget):
    """
    Individual Sudoku cell widget with triangle-based notes
    
    CELL STATES:
    1. Original number (is_initial=True, value!=0)
       - Cannot be altered
       - Grey background
       
    2. Manually entered number (is_initial=False, value!=0)
       - Can be cleared
       - White background
       - Bold/large when matches selected number
       
    3. Blue triangle, no notes (value=0, notes_enabled=False)
       - Number mode: click to enter number → State 2
       - Click triangle → State 4 (enable auto notes)
       
    4. Yellow triangle, auto notes (value=0, notes_enabled=True, notes_mode='auto')
       - Number mode: click to enter number → State 2
       - Note mode: edit candidates → State 5 (switches to manual)
       - Click triangle → State 3 (disable notes)
       
    5. Green triangle, manual notes (value=0, notes_enabled=True, notes_mode='manual')
       - Number mode: click to enter number → State 2
       - Note mode: edit candidates (stays in State 5)
       - Click triangle → State 4 (revert to auto)
    """
    def __init__(self, row, col, game_parent, parent=None):
        super().__init__(parent)
        self.row = row
        self.col = col
        self.game_parent = game_parent
        self.value = 0
        self.is_initial = False
        self.notes_enabled = False
        self.notes_mode = 'auto'  # 'auto' or 'manual'
        self.candidates = set()
        self.manual_candidates = set()
        self.is_candidate = False
        self.is_singleton = False
        self.is_error = False  # Tracking flag (always accurate)
        self.error_display_on = False  # Display flag (controls red shading)
        self.is_bold = False
        self.border_highlight = False
        self.highlight_pattern = False  # Cells forming a pattern (green)
        self.highlight_affected = False  # Cells with eliminations (yellow)
        self.highlight_excluded = False  # Cells excluded by filled numbers (pink)
        self.setMinimumSize(50, 50)
        self.setMouseTracking(True)
        
    def reset(self):
        """Reset cell to initial state for new puzzle"""
        self.value = 0
        self.is_initial = False
        self.notes_enabled = False
        self.notes_mode = 'auto'
        self.candidates.clear()
        self.manual_candidates.clear()
        self.is_candidate = False
        self.is_singleton = False
        self.is_error = False
        self.error_display_on = False
        self.is_bold = False
        self.border_highlight = False
        self.highlight_pattern = False
        self.highlight_affected = False
        self.highlight_excluded = False

    def set_value(self, value, is_initial=False):
        self.value = value
        self.is_initial = is_initial
        if value != 0:
            self.notes_enabled = False
            self.candidates.clear()
            self.manual_candidates.clear()
        self.update()
    
    def update_display(self, value):
        """Update display value without clearing notes (for refresh)"""
        old_value = self.value
        self.value = value
        
        # Only clear notes if we're actually placing a new number
        if value != 0 and old_value == 0:
            self.notes_enabled = False
            self.candidates.clear()
            self.manual_candidates.clear()
        
        self.update()
        
    def toggle_notes(self):
        """
        Toggle notes on/off or revert manual to auto
        State 3 (blue) → State 4 (yellow auto)
        State 4 (yellow auto) → State 3 (blue off)
        State 5 (green manual) → State 4 (yellow auto - revert)
        """
        if self.value == 0 and not self.is_initial:
            if self.notes_mode == 'manual':
                # State 5 → State 4: Revert manual to auto
                self.revert_to_auto_notes()
            elif self.notes_enabled:
                # State 4 → State 3: Turn off auto notes
                self.notes_enabled = False
                self.candidates.clear()
                self.update()
            else:
                # State 3 → State 4: Enable auto notes
                self.notes_enabled = True
                self.notes_mode = 'auto'
                self.calculate_candidates()
                self.update()
    
    def set_manual_notes(self):
        """Switch to manual note mode"""
        if self.value == 0 and not self.is_initial:
            self.notes_mode = 'manual'
            if not self.notes_enabled:
                self.notes_enabled = True
            # Copy current candidates to manual
            self.manual_candidates = self.candidates.copy()
            self.update()
    
    def toggle_manual_candidate(self, num):
        """Toggle a specific candidate in manual mode"""
        if self.notes_mode == 'manual':
            if num in self.manual_candidates:
                self.manual_candidates.remove(num)
            else:
                self.manual_candidates.add(num)
            self.update()
    
    def revert_to_auto_notes(self):
        """Revert from manual to auto notes"""
        self.notes_mode = 'auto'
        self.manual_candidates.clear()
        if self.notes_enabled:
            self.calculate_candidates()
        self.update()
            
    def calculate_candidates(self):
        """Calculate valid candidates for this cell"""
        if self.game_parent and self.value == 0:
            self.candidates = set()
            for num in range(1, 10):
                if self.game_parent.can_place_number(self.row, self.col, num):
                    self.candidates.add(num)
        
    def clear_notes(self):
        self.notes_enabled = False
        self.candidates.clear()
        self.manual_candidates.clear()
        self.update()
        
    def set_highlight(self, candidate=False, singleton=False, bold=False):
        """Set highlighting flags (not for errors - those use error_display_on)"""
        self.is_candidate = candidate
        self.is_singleton = singleton
        self.is_bold = bold
        self.update()
        
    def is_in_triangle(self, pos):
        """Check if click position is inside triangle"""
        if self.value != 0:
            return False
        triangle_size = int(self.width() * 0.35)
        return pos.x() <= triangle_size and pos.y() <= triangle_size
        
    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()
        
        if self.border_highlight:
            pen = QPen(QColor(*Colors.BORDER_HIGHLIGHT), 4)
            painter.setPen(pen)
            painter.drawRect(rect.adjusted(2, 2, -2, -2))
        
        # Background color - priority order
        if self.error_display_on:  # Use display flag, not tracking flag!
            painter.fillRect(rect, QColor(*Colors.BG_ERROR))
        elif self.highlight_pattern:
            painter.fillRect(rect, QColor(*Colors.BG_PATTERN))
        elif self.highlight_affected:
            painter.fillRect(rect, QColor(*Colors.BG_AFFECTED))
        elif self.highlight_excluded:
            painter.fillRect(rect, QColor(*Colors.BG_EXCLUDED))
        elif self.is_singleton:
            painter.fillRect(rect, QColor(*Colors.BG_SINGLETON))
        elif self.is_candidate:
            painter.fillRect(rect, QColor(*Colors.BG_CANDIDATE))
        elif self.is_initial:
            painter.fillRect(rect, QColor(*Colors.BG_INITIAL))
        else:
            painter.fillRect(rect, QColor(*Colors.BG_NORMAL))
        
        # Draw triangle - dynamically sized with three colors
        if self.value == 0 and not self.is_initial:
            triangle_size = int(self.width() * 0.35)
            
            if self.notes_enabled:
                if self.notes_mode == 'manual':
                    triangle_color = QColor(*Colors.TRIANGLE_MANUAL)  # Green
                else:
                    triangle_color = QColor(*Colors.TRIANGLE_AUTO)  # Yellow
            else:
                triangle_color = QColor(*Colors.TRIANGLE_OFF)  # Cyan
            
            painter.setBrush(QBrush(triangle_color))
            painter.setPen(Qt.PenStyle.NoPen)
            
            triangle = QPolygon([
                QPoint(2, 2),
                QPoint(triangle_size, 2),
                QPoint(2, triangle_size)
            ])
            painter.drawPolygon(triangle)
        
        # Draw value or notes
        if self.value != 0:
            # Number is displayed large and bold if it matches selected number
            if self.is_bold:
                font = QFont('Arial', 32, QFont.Weight.Black)
            else:
                font = QFont('Arial', 24, QFont.Weight.Bold)
            painter.setFont(font)
            painter.setPen(QColor(51, 51, 51))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(self.value))
        elif self.notes_enabled:
            # Use manual or auto candidates
            display_candidates = self.manual_candidates if self.notes_mode == 'manual' else self.candidates
            if display_candidates:
                font = QFont('Arial', 9)
                painter.setFont(font)
                painter.setPen(QColor(0, 0, 0))
                
                cell_width = rect.width() / 3
                cell_height = rect.height() / 3
                
                for num in range(1, 10):
                    if num in display_candidates:
                        grid_row = (num - 1) // 3
                        grid_col = (num - 1) % 3
                        x = rect.left() + grid_col * cell_width
                        y = rect.top() + grid_row * cell_height
                        painter.drawText(int(x), int(y), int(cell_width), int(cell_height),
                                       Qt.AlignmentFlag.AlignCenter, str(num))
        
    def mousePressEvent(self, event):
        """Handle mouse click on cell"""
        if self.game_parent:
            if self.is_in_triangle(event.pos()):
                self.toggle_notes()
            else:
                self.game_parent.handle_cell_click(self.row, self.col)
