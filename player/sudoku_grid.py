"""
Sudoku Grid Widget
9x9 grid container with proper box borders
"""

from PyQt6.QtWidgets import QFrame, QWidget, QGridLayout, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen
from sudoku_cell import SudokuCell


class SudokuGrid(QFrame):
    """Sudoku grid with proper borders"""
    def __init__(self, game_parent, parent=None):
        super().__init__(parent)
        self.game_parent = game_parent
        self.cells = []
        self.setup_grid()
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)
        self.setLineWidth(4)
        
    def setup_grid(self):
        layout = QGridLayout()
        layout.setSpacing(1)
        layout.setContentsMargins(0, 0, 0, 0)
        
        for row in range(9):
            cell_row = []
            for col in range(9):
                cell = SudokuCell(row, col, self.game_parent, self)
                
                left_margin = 3 if col % 3 == 0 and col > 0 else 0
                top_margin = 3 if row % 3 == 0 and row > 0 else 0
                
                container = QWidget()
                container_layout = QVBoxLayout()
                container_layout.setContentsMargins(left_margin, top_margin, 0, 0)
                container_layout.setSpacing(0)
                container_layout.addWidget(cell)
                container.setLayout(container_layout)
                
                layout.addWidget(container, row, col)
                cell_row.append(cell)
            self.cells.append(cell_row)
            
        self.setLayout(layout)
        
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        border = 4
        inner_width = width - 2 * border
        inner_height = height - 2 * border
        
        cell_width = inner_width / 9
        cell_height = inner_height / 9
        
        # Thin lines
        pen = QPen(Qt.GlobalColor.black, 1)
        painter.setPen(pen)
        for i in range(1, 9):
            if i % 3 != 0:
                x = border + int(i * cell_width)
                painter.drawLine(x, border, x, height - border)
                y = border + int(i * cell_height)
                painter.drawLine(border, y, width - border, y)
        
        # Thick lines for 3x3 boxes
        pen = QPen(Qt.GlobalColor.black, 4)
        painter.setPen(pen)
        for i in [3, 6]:
            x = border + int(i * cell_width)
            painter.drawLine(x, border, x, height - border)
            y = border + int(i * cell_height)
            painter.drawLine(border, y, width - border, y)
