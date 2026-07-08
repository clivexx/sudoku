"""
Sudoku Solver - Basic solving algorithms and validation
Shared by both Player and Studio applications
"""

class SudokuSolver:
    """Basic Sudoku solving and validation algorithms"""
    
    @staticmethod
    def solve(puzzle):
        """
        Solve a Sudoku puzzle using backtracking
        Returns: solved board or None if unsolvable
        """
        board = [row[:] for row in puzzle]
        
        def is_valid(grid, row, col, num):
            # Check row
            for x in range(9):
                if grid[row][x] == num:
                    return False
            
            # Check column
            for x in range(9):
                if grid[x][col] == num:
                    return False
            
            # Check 3x3 box
            start_row = (row // 3) * 3
            start_col = (col // 3) * 3
            for i in range(3):
                for j in range(3):
                    if grid[start_row + i][start_col + j] == num:
                        return False
            
            return True
        
        def solve_recursive(grid):
            for row in range(9):
                for col in range(9):
                    if grid[row][col] == 0:
                        for num in range(1, 10):
                            if is_valid(grid, row, col, num):
                                grid[row][col] = num
                                if solve_recursive(grid):
                                    return True
                                grid[row][col] = 0
                        return False
            return True
        
        if solve_recursive(board):
            return board
        return None
    
    @staticmethod
    def is_valid_placement(board, row, col, num):
        """Check if number can be placed in cell"""
        # Check row
        for x in range(9):
            if board[row][x] == num:
                return False
        
        # Check column
        for x in range(9):
            if board[x][col] == num:
                return False
        
        # Check 3x3 box
        start_row = (row // 3) * 3
        start_col = (col // 3) * 3
        for i in range(3):
            for j in range(3):
                if board[start_row + i][start_col + j] == num:
                    return False
        
        return True
    
    @staticmethod
    def count_solutions(puzzle, max_count=2):
        """
        Count number of solutions up to max_count
        Used to verify puzzle has unique solution
        """
        count = [0]
        
        def solve(grid):
            if count[0] >= max_count:
                return
            
            # Find cell with minimum candidates (MRV heuristic)
            min_candidates = 10
            best_cell = None
            best_nums = []
            
            for row in range(9):
                for col in range(9):
                    if grid[row][col] == 0:
                        candidates = []
                        for num in range(1, 10):
                            if SudokuSolver.is_valid_placement(grid, row, col, num):
                                candidates.append(num)
                        
                        if len(candidates) < min_candidates:
                            min_candidates = len(candidates)
                            best_cell = (row, col)
                            best_nums = candidates
            
            # No empty cells - found a solution
            if best_cell is None:
                count[0] += 1
                return
            
            # Dead end - no valid numbers
            if min_candidates == 0:
                return
            
            # Try each candidate
            row, col = best_cell
            for num in best_nums:
                grid[row][col] = num
                solve(grid)
                grid[row][col] = 0
        
        work_grid = [row[:] for row in puzzle]
        solve(work_grid)
        return count[0]
    
    @staticmethod
    def is_complete(board):
        """Check if board is completely filled"""
        return all(board[r][c] != 0 for r in range(9) for c in range(9))
    
    @staticmethod
    def get_candidates(board, row, col):
        """Get all valid candidates for a cell"""
        if board[row][col] != 0:
            return set()
        
        candidates = set()
        for num in range(1, 10):
            if SudokuSolver.is_valid_placement(board, row, col, num):
                candidates.add(num)
        
        return candidates
    
    @staticmethod
    def get_all_candidates(board):
        """Get candidates for all empty cells"""
        candidates = {}
        for row in range(9):
            for col in range(9):
                if board[row][col] == 0:
                    candidates[(row, col)] = SudokuSolver.get_candidates(board, row, col)
        return candidates
