"""
Sudoku Analyzer - Difficulty analysis and hint generation
Shared by both Player (hints) and Studio (difficulty classification)

Implements solving strategies in order of difficulty:
1. Hidden Singles (box, row/col)
2. Naked Singles
3. Naked Subsets (pairs, triples, quads)
4. Hidden Subsets (pairs, triples, quads)
5. Intersection techniques (pointing pairs, box/line reduction)
6. Fish techniques (X-Wing, Swordfish, Jellyfish)
7. Wing techniques (XY-Wing)
8. Coloring/Chain techniques (Simple Coloring, Forcing Chains)
"""

from itertools import combinations
from sudoku_solver import SudokuSolver


class SudokuAnalyzer:
    """Analyzes puzzles and generates progressive hints"""

    # =========================================================================
    # HELPER FUNCTIONS
    # =========================================================================

    @staticmethod
    def _get_house_cells(house_type, index):
        """
        Return list of (row, col) for cells in a house.
        house_type: 'row', 'col', or 'box'
        index: 0-8 for row/col, or (box_row, box_col) tuple for box
        """
        cells = []
        if house_type == 'row':
            for col in range(9):
                cells.append((index, col))
        elif house_type == 'col':
            for row in range(9):
                cells.append((row, index))
        elif house_type == 'box':
            box_row, box_col = index
            for i in range(3):
                for j in range(3):
                    cells.append((box_row * 3 + i, box_col * 3 + j))
        return cells

    @staticmethod
    def _get_box_index(row, col):
        """Return (box_row, box_col) for a cell"""
        return (row // 3, col // 3)

    @staticmethod
    def _cells_see_each_other(cell1, cell2):
        """Check if two cells are in the same house (can see each other)"""
        r1, c1 = cell1
        r2, c2 = cell2
        if r1 == r2:  # Same row
            return True
        if c1 == c2:  # Same column
            return True
        if r1 // 3 == r2 // 3 and c1 // 3 == c2 // 3:  # Same box
            return True
        return False

    @staticmethod
    def _get_shared_houses(cell1, cell2):
        """
        Return list of all houses shared by two cells.
        Each entry: (house_type, house_idx, cells_list)
        """
        r1, c1 = cell1
        r2, c2 = cell2
        shared = []

        if r1 == r2:  # Same row
            shared.append(('row', r1, SudokuAnalyzer._get_house_cells('row', r1)))
        if c1 == c2:  # Same column
            shared.append(('col', c1, SudokuAnalyzer._get_house_cells('col', c1)))
        if r1 // 3 == r2 // 3 and c1 // 3 == c2 // 3:  # Same box
            box_idx = (r1 // 3, c1 // 3)
            shared.append(('box', box_idx, SudokuAnalyzer._get_house_cells('box', box_idx)))

        return shared

    @staticmethod
    def _get_shared_houses_for_cells(cells):
        """
        Return list of all houses shared by ALL cells in the list.
        Each entry: (house_type, house_idx, cells_list)
        """
        if not cells:
            return []

        shared = []
        rows = set(r for r, c in cells)
        cols = set(c for r, c in cells)
        boxes = set((r // 3, c // 3) for r, c in cells)

        if len(rows) == 1:  # All cells in same row
            row = next(iter(rows))
            shared.append(('row', row, SudokuAnalyzer._get_house_cells('row', row)))
        if len(cols) == 1:  # All cells in same column
            col = next(iter(cols))
            shared.append(('col', col, SudokuAnalyzer._get_house_cells('col', col)))
        if len(boxes) == 1:  # All cells in same box
            box_idx = next(iter(boxes))
            shared.append(('box', box_idx, SudokuAnalyzer._get_house_cells('box', box_idx)))

        return shared

    @staticmethod
    def _format_shared_houses(shared_houses):
        """Format shared houses list into a location string."""
        parts = []
        for house_type, house_idx, _ in shared_houses:
            if house_type == 'row':
                parts.append(f"row {house_idx + 1}")
            elif house_type == 'col':
                parts.append(f"column {house_idx + 1}")
            elif house_type == 'box':
                parts.append(f"box ({house_idx[0] + 1},{house_idx[1] + 1})")
        return " & ".join(parts)

    @staticmethod
    def _get_common_peers(cells):
        """Get all cells that can see ALL cells in the list"""
        if not cells:
            return set()

        # Get peers of first cell
        first = cells[0]
        peers = set()

        # Add all cells in same row, col, box
        for col in range(9):
            peers.add((first[0], col))
        for row in range(9):
            peers.add((row, first[1]))
        box_row, box_col = first[0] // 3, first[1] // 3
        for i in range(3):
            for j in range(3):
                peers.add((box_row * 3 + i, box_col * 3 + j))

        # Remove the cell itself
        peers.discard(first)

        # Intersect with peers of remaining cells
        for cell in cells[1:]:
            cell_peers = set()
            for col in range(9):
                cell_peers.add((cell[0], col))
            for row in range(9):
                cell_peers.add((row, cell[1]))
            box_row, box_col = cell[0] // 3, cell[1] // 3
            for i in range(3):
                for j in range(3):
                    cell_peers.add((box_row * 3 + i, box_col * 3 + j))
            cell_peers.discard(cell)
            peers &= cell_peers

        # Remove the original cells
        for cell in cells:
            peers.discard(cell)

        return peers

    @staticmethod
    def _get_cell_candidates(candidates, row, col):
        """
        Get candidates for a cell, handling both dict formats:
        - {(row, col): set()} format from get_all_candidates
        - candidates[row][col] nested format
        """
        if isinstance(candidates, dict):
            return candidates.get((row, col), set())
        return set()

    # =========================================================================
    # HINT ENTRY POINTS
    # =========================================================================

    @staticmethod
    def get_next_hint(board, detail_level=1):
        """
        Get hint at specified detail level (1-5).
        Tries placement hints first, then elimination patterns.
        """
        # Try placement hints first
        hint = SudokuAnalyzer.find_placement_hint(board)

        # If no placement, try first elimination pattern
        if not hint:
            patterns = SudokuAnalyzer.find_all_elimination_patterns(board)
            if patterns:
                hint = patterns[0]

        if not hint:
            return {
                'type': 'none',
                'message': 'No techniques available. The puzzle may require guessing.'
            }

        # Build result with all relevant fields
        result = {
            'type': hint['type'],
            'message': ''
        }

        # Copy optional fields
        for key in ['number', 'numbers', 'cell', 'cells', 'location', 'eliminations']:
            if key in hint:
                result[key] = hint[key]

        # Format message based on detail level
        if detail_level == 1:
            result['message'] = SudokuAnalyzer._format_hint_level_1(hint)
        elif detail_level == 2:
            result['message'] = SudokuAnalyzer._format_hint_level_2(hint)
        elif detail_level == 3:
            result['message'] = SudokuAnalyzer._format_hint_level_3(hint)
        elif detail_level == 4:
            result['message'] = SudokuAnalyzer._format_hint_level_4(hint)
        else:
            result['message'] = SudokuAnalyzer._format_hint_level_5(hint)
            if hint.get('cell') and hint.get('number'):
                result['answer'] = hint['number']

        return result

    @staticmethod
    def find_placement_hint(board):
        """
        Check for placement hints (singles only).
        Returns first placement hint or None.
        """
        # Try box hidden singles first (easiest)
        hint = SudokuAnalyzer._find_box_hidden_single(board)
        if hint:
            return hint

        # Try row/col hidden singles (≤2 empty)
        hint = SudokuAnalyzer._find_rowcol_single_limited(board)
        if hint:
            return hint

        # Try all hidden singles
        hint = SudokuAnalyzer._find_any_hidden_single(board)
        if hint:
            return hint

        # Try naked singles
        hint = SudokuAnalyzer._find_naked_single(board)
        if hint:
            return hint

        return None

    @staticmethod
    def find_all_elimination_patterns(board):
        """
        Find ALL elimination patterns (everything except singles).
        Returns list of hint dicts.
        """
        candidates = SudokuSolver.get_all_candidates(board)
        all_hints = []

        # Naked subsets
        all_hints.extend(SudokuAnalyzer._find_naked_pair(board, candidates, find_all=True))
        all_hints.extend(SudokuAnalyzer._find_naked_triple(board, candidates, find_all=True))
        all_hints.extend(SudokuAnalyzer._find_naked_quad(board, candidates, find_all=True))

        # Hidden subsets
        all_hints.extend(SudokuAnalyzer._find_hidden_pair(board, candidates, find_all=True))
        all_hints.extend(SudokuAnalyzer._find_hidden_triple(board, candidates, find_all=True))
        all_hints.extend(SudokuAnalyzer._find_hidden_quad(board, candidates, find_all=True))

        # Intersection techniques
        all_hints.extend(SudokuAnalyzer._find_pointing_pair(board, candidates, find_all=True))
        all_hints.extend(SudokuAnalyzer._find_box_line_reduction(board, candidates, find_all=True))

        # Fish techniques
        all_hints.extend(SudokuAnalyzer._find_xwing(board, candidates, find_all=True))
        all_hints.extend(SudokuAnalyzer._find_swordfish(board, candidates, find_all=True))
        all_hints.extend(SudokuAnalyzer._find_jellyfish(board, candidates, find_all=True))

        # Uniqueness techniques
        all_hints.extend(SudokuAnalyzer._find_unique_rectangles(board, candidates, find_all=True))

        # Wing techniques
        all_hints.extend(SudokuAnalyzer._find_xy_wing(board, candidates, find_all=True))

        # Coloring/chain techniques
        all_hints.extend(SudokuAnalyzer._find_simple_coloring(board, candidates, find_all=True))
        all_hints.extend(SudokuAnalyzer._find_forcing_chain(board, candidates, find_all=True))

        return all_hints

    # =========================================================================
    # TECHNIQUE DETECTION METHODS
    # =========================================================================

    @staticmethod
    def _find_box_hidden_single(board):
        """Find first box hidden single"""
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
                        return {
                            'type': 'box_hidden_single',
                            'number': num,
                            'cell': possible_cells[0],
                            'location': f"box ({box_row+1},{box_col+1})"
                        }
        return None
    
    @staticmethod
    def _find_rowcol_single_limited(board):
        """Find hidden single in row/col with ≤2 empty"""
        for num in range(1, 10):
            # Check rows
            for row in range(9):
                empty_count = sum(1 for col in range(9) if board[row][col] == 0)
                if empty_count <= 2:
                    possible_cols = []
                    for col in range(9):
                        if board[row][col] == 0 and SudokuSolver.is_valid_placement(board, row, col, num):
                            possible_cols.append(col)
                    if len(possible_cols) == 1:
                        return {
                            'type': 'rowcol_hidden_single',
                            'number': num,
                            'cell': (row, possible_cols[0]),
                            'location': f"row {row+1}"
                        }
            
            # Check columns
            for col in range(9):
                empty_count = sum(1 for row in range(9) if board[row][col] == 0)
                if empty_count <= 2:
                    possible_rows = []
                    for row in range(9):
                        if board[row][col] == 0 and SudokuSolver.is_valid_placement(board, row, col, num):
                            possible_rows.append(row)
                    if len(possible_rows) == 1:
                        return {
                            'type': 'rowcol_hidden_single',
                            'number': num,
                            'cell': (possible_rows[0], col),
                            'location': f"column {col+1}"
                        }
        return None
    
    @staticmethod
    def _find_any_hidden_single(board):
        """Find any hidden single"""
        for num in range(1, 10):
            # Rows
            for row in range(9):
                possible_cols = [col for col in range(9) 
                                if board[row][col] == 0 and SudokuSolver.is_valid_placement(board, row, col, num)]
                if len(possible_cols) == 1:
                    return {
                        'type': 'hidden_single',
                        'number': num,
                        'cell': (row, possible_cols[0]),
                        'location': f"row {row+1}"
                    }
            
            # Columns
            for col in range(9):
                possible_rows = [row for row in range(9)
                                if board[row][col] == 0 and SudokuSolver.is_valid_placement(board, row, col, num)]
                if len(possible_rows) == 1:
                    return {
                        'type': 'hidden_single',
                        'number': num,
                        'cell': (possible_rows[0], col),
                        'location': f"column {col+1}"
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
                        return {
                            'type': 'hidden_single',
                            'number': num,
                            'cell': possible_cells[0],
                            'location': f"box ({box_row+1},{box_col+1})"
                        }
        return None
    
    @staticmethod
    def _find_naked_single(board):
        """Find cell with only one candidate"""
        for row in range(9):
            for col in range(9):
                if board[row][col] == 0:
                    candidates = SudokuSolver.get_candidates(board, row, col)
                    if len(candidates) == 1:
                        return {
                            'type': 'naked_single',
                            'number': list(candidates)[0],
                            'cell': (row, col),
                            'location': f"cell ({row+1},{col+1})"
                        }
        return None
    
    # =========================================================================
    # NAKED SUBSET TECHNIQUES
    # =========================================================================

    @staticmethod
    def _find_naked_pair(board, candidates, find_all=False):
        """
        Find naked pairs: two cells in a house with exactly the same 2 candidates.
        Returns hint dict (or None) if find_all=False, list of hints if find_all=True.
        Note: candidates is a dict with (row, col) tuples as keys.

        When a pair shares multiple houses (e.g., same row AND same box),
        eliminations from all shared houses are combined into a single hint.
        """
        results = [] if find_all else None
        seen_pairs = set()  # Track (cell1, cell2) tuples to avoid duplicates

        houses = []
        # Add all rows
        for row in range(9):
            houses.append(('row', row, SudokuAnalyzer._get_house_cells('row', row)))
        # Add all columns
        for col in range(9):
            houses.append(('col', col, SudokuAnalyzer._get_house_cells('col', col)))
        # Add all boxes
        for br in range(3):
            for bc in range(3):
                houses.append(('box', (br, bc), SudokuAnalyzer._get_house_cells('box', (br, bc))))

        for house_type, house_idx, cells in houses:
            # Get empty cells with their candidates
            empty_cells = [(r, c) for r, c in cells if board[r][c] == 0]

            # Need >2 empty cells for a pair to eliminate anything
            if len(empty_cells) <= 2:
                continue

            # Find cells with exactly 2 candidates
            pairs_cells = [(r, c) for r, c in empty_cells if len(candidates.get((r, c), set())) == 2]

            # Check all combinations of 2 such cells
            for (r1, c1), (r2, c2) in combinations(pairs_cells, 2):
                # Create canonical key for this pair (sorted)
                pair_key = tuple(sorted([(r1, c1), (r2, c2)]))
                if pair_key in seen_pairs:
                    continue

                cands1 = candidates.get((r1, c1), set())
                cands2 = candidates.get((r2, c2), set())

                if cands1 == cands2:
                    # Found a naked pair! Determine all shared houses
                    pair_nums = list(cands1)
                    shared_houses = SudokuAnalyzer._get_shared_houses((r1, c1), (r2, c2))

                    # Collect eliminations from ALL shared houses
                    eliminations = []
                    elim_set = set()  # Avoid duplicate eliminations

                    for sh_type, sh_idx, sh_cells in shared_houses:
                        sh_empty = [(r, c) for r, c in sh_cells if board[r][c] == 0]
                        # Check we have >2 empty cells for this house to matter
                        if len(sh_empty) <= 2:
                            continue
                        for r, c in sh_empty:
                            if (r, c) != (r1, c1) and (r, c) != (r2, c2):
                                cell_cands = candidates.get((r, c), set())
                                for num in pair_nums:
                                    if num in cell_cands and (r, c, num) not in elim_set:
                                        eliminations.append((r, c, num))
                                        elim_set.add((r, c, num))

                    if eliminations:
                        seen_pairs.add(pair_key)
                        # Build location string from all shared houses
                        location = SudokuAnalyzer._format_shared_houses(shared_houses)
                        hint = {
                            'type': 'naked_pair',
                            'numbers': pair_nums,
                            'cells': [(r1, c1), (r2, c2)],
                            'eliminations': eliminations,
                            'location': location
                        }
                        if find_all:
                            results.append(hint)
                        else:
                            return hint
        return results if find_all else None

    @staticmethod
    def _find_naked_triple(board, candidates, find_all=False):
        """
        Find naked triples: three cells in a house whose combined candidates
        are exactly 3 numbers. Each cell can have 2 or 3 of these candidates.

        When a triple shares multiple houses, eliminations from all are combined.
        """
        results = [] if find_all else None
        seen_combos = set()  # Track combos to avoid duplicates

        houses = []
        for row in range(9):
            houses.append(('row', row, SudokuAnalyzer._get_house_cells('row', row)))
        for col in range(9):
            houses.append(('col', col, SudokuAnalyzer._get_house_cells('col', col)))
        for br in range(3):
            for bc in range(3):
                houses.append(('box', (br, bc), SudokuAnalyzer._get_house_cells('box', (br, bc))))

        for house_type, house_idx, cells in houses:
            empty_cells = [(r, c) for r, c in cells if board[r][c] == 0]

            # Need >3 empty cells for a triple to eliminate anything
            if len(empty_cells) <= 3:
                continue

            # Find cells with 2-3 candidates
            potential_cells = [(r, c) for r, c in empty_cells
                               if 2 <= len(candidates.get((r, c), set())) <= 3]

            # Check all combinations of 3 cells
            for combo in combinations(potential_cells, 3):
                # Create canonical key for this combo (sorted)
                combo_key = tuple(sorted(combo))
                if combo_key in seen_combos:
                    continue

                combined = set()
                for r, c in combo:
                    combined |= candidates.get((r, c), set())

                if len(combined) == 3:
                    # Found a naked triple! Determine all shared houses
                    triple_nums = list(combined)
                    shared_houses = SudokuAnalyzer._get_shared_houses_for_cells(combo)

                    # Collect eliminations from ALL shared houses
                    eliminations = []
                    elim_set = set()

                    for sh_type, sh_idx, sh_cells in shared_houses:
                        sh_empty = [(r, c) for r, c in sh_cells if board[r][c] == 0]
                        if len(sh_empty) <= 3:
                            continue
                        for r, c in sh_empty:
                            if (r, c) not in combo:
                                cell_cands = candidates.get((r, c), set())
                                for num in triple_nums:
                                    if num in cell_cands and (r, c, num) not in elim_set:
                                        eliminations.append((r, c, num))
                                        elim_set.add((r, c, num))

                    if eliminations:
                        seen_combos.add(combo_key)
                        location = SudokuAnalyzer._format_shared_houses(shared_houses)
                        hint = {
                            'type': 'naked_triple',
                            'numbers': triple_nums,
                            'cells': list(combo),
                            'eliminations': eliminations,
                            'location': location
                        }
                        if find_all:
                            results.append(hint)
                        else:
                            return hint
        return results if find_all else None

    @staticmethod
    def _find_naked_quad(board, candidates, find_all=False):
        """
        Find naked quads: four cells in a house whose combined candidates
        are exactly 4 numbers.
        """
        results = [] if find_all else None
        houses = []
        for row in range(9):
            houses.append(('row', row, SudokuAnalyzer._get_house_cells('row', row)))
        for col in range(9):
            houses.append(('col', col, SudokuAnalyzer._get_house_cells('col', col)))
        for br in range(3):
            for bc in range(3):
                houses.append(('box', (br, bc), SudokuAnalyzer._get_house_cells('box', (br, bc))))

        for house_type, house_idx, cells in houses:
            empty_cells = [(r, c) for r, c in cells if board[r][c] == 0]

            # Need >4 empty cells for a quad to eliminate anything
            if len(empty_cells) <= 4:
                continue

            # Find cells with 2-4 candidates
            potential_cells = [(r, c) for r, c in empty_cells
                               if 2 <= len(candidates.get((r, c), set())) <= 4]

            # Check all combinations of 4 cells
            for combo in combinations(potential_cells, 4):
                combined = set()
                for r, c in combo:
                    combined |= candidates.get((r, c), set())

                if len(combined) == 4:
                    # Found a naked quad!
                    quad_nums = list(combined)
                    eliminations = []

                    for r, c in empty_cells:
                        if (r, c) not in combo:
                            cell_cands = candidates.get((r, c), set())
                            for num in quad_nums:
                                if num in cell_cands:
                                    eliminations.append((r, c, num))

                    if eliminations:
                        location = f"row {house_idx + 1}" if house_type == 'row' else \
                                   f"column {house_idx + 1}" if house_type == 'col' else \
                                   f"box ({house_idx[0] + 1},{house_idx[1] + 1})"
                        hint = {
                            'type': 'naked_quad',
                            'numbers': quad_nums,
                            'cells': list(combo),
                            'eliminations': eliminations,
                            'location': location
                        }
                        if find_all:
                            results.append(hint)
                        else:
                            return hint
        return results if find_all else None

    # =========================================================================
    # HIDDEN SUBSET TECHNIQUES
    # =========================================================================

    @staticmethod
    def _find_hidden_pair(board, candidates, find_all=False):
        """
        Find hidden pairs: two candidates that appear only in the same 2 cells
        within a house. Other candidates in those cells can be eliminated.

        When cells share multiple houses, location shows all shared houses.
        """
        results = [] if find_all else None
        seen_pairs = set()  # Track (cell1, cell2, n1, n2) to avoid duplicates

        houses = []
        for row in range(9):
            houses.append(('row', row, SudokuAnalyzer._get_house_cells('row', row)))
        for col in range(9):
            houses.append(('col', col, SudokuAnalyzer._get_house_cells('col', col)))
        for br in range(3):
            for bc in range(3):
                houses.append(('box', (br, bc), SudokuAnalyzer._get_house_cells('box', (br, bc))))

        for house_type, house_idx, cells in houses:
            empty_cells = [(r, c) for r, c in cells if board[r][c] == 0]

            # Build a map: number -> cells that can contain it
            num_to_cells = {n: [] for n in range(1, 10)}
            for r, c in empty_cells:
                for n in candidates.get((r, c), set()):
                    num_to_cells[n].append((r, c))

            # Find pairs of numbers that appear in exactly 2 cells (same cells)
            for n1, n2 in combinations(range(1, 10), 2):
                cells1 = num_to_cells[n1]
                cells2 = num_to_cells[n2]

                if len(cells1) == 2 and cells1 == cells2:
                    # These two numbers appear only in the same 2 cells
                    pair_cells = cells1
                    pair_nums = [n1, n2]

                    # Create canonical key (sorted cells + sorted numbers)
                    pair_key = (tuple(sorted(pair_cells)), tuple(sorted(pair_nums)))
                    if pair_key in seen_pairs:
                        continue

                    # Check for eliminations (other candidates in these cells)
                    eliminations = []
                    for r, c in pair_cells:
                        for n in candidates.get((r, c), set()):
                            if n not in pair_nums:
                                eliminations.append((r, c, n))

                    if eliminations:
                        seen_pairs.add(pair_key)
                        shared_houses = SudokuAnalyzer._get_shared_houses(pair_cells[0], pair_cells[1])
                        location = SudokuAnalyzer._format_shared_houses(shared_houses)
                        hint = {
                            'type': 'hidden_pair',
                            'numbers': pair_nums,
                            'cells': pair_cells,
                            'eliminations': eliminations,
                            'location': location
                        }
                        if find_all:
                            results.append(hint)
                        else:
                            return hint
        return results if find_all else None

    @staticmethod
    def _find_hidden_triple(board, candidates, find_all=False):
        """
        Find hidden triples: three candidates that appear only in the same 3 cells.

        When cells share multiple houses, location shows all shared houses.
        """
        results = [] if find_all else None
        seen_triples = set()  # Track (cells, numbers) to avoid duplicates

        houses = []
        for row in range(9):
            houses.append(('row', row, SudokuAnalyzer._get_house_cells('row', row)))
        for col in range(9):
            houses.append(('col', col, SudokuAnalyzer._get_house_cells('col', col)))
        for br in range(3):
            for bc in range(3):
                houses.append(('box', (br, bc), SudokuAnalyzer._get_house_cells('box', (br, bc))))

        for house_type, house_idx, cells in houses:
            empty_cells = [(r, c) for r, c in cells if board[r][c] == 0]

            # Build number -> cells map
            num_to_cells = {n: set() for n in range(1, 10)}
            for r, c in empty_cells:
                for n in candidates.get((r, c), set()):
                    num_to_cells[n].add((r, c))

            # Find triples of numbers that collectively appear in exactly 3 cells
            for n1, n2, n3 in combinations(range(1, 10), 3):
                combined_cells = num_to_cells[n1] | num_to_cells[n2] | num_to_cells[n3]

                if len(combined_cells) == 3:
                    # Each number must appear in at least 2 of these cells
                    if (len(num_to_cells[n1]) >= 2 and
                        len(num_to_cells[n2]) >= 2 and
                        len(num_to_cells[n3]) >= 2):

                        triple_cells = list(combined_cells)
                        triple_nums = [n1, n2, n3]

                        # Create canonical key
                        triple_key = (tuple(sorted(triple_cells)), tuple(sorted(triple_nums)))
                        if triple_key in seen_triples:
                            continue

                        # Eliminations: other candidates in these cells
                        eliminations = []
                        for r, c in triple_cells:
                            for n in candidates.get((r, c), set()):
                                if n not in triple_nums:
                                    eliminations.append((r, c, n))

                        if eliminations:
                            seen_triples.add(triple_key)
                            shared_houses = SudokuAnalyzer._get_shared_houses_for_cells(triple_cells)
                            location = SudokuAnalyzer._format_shared_houses(shared_houses)
                            hint = {
                                'type': 'hidden_triple',
                                'numbers': triple_nums,
                                'cells': triple_cells,
                                'eliminations': eliminations,
                                'location': location
                            }
                            if find_all:
                                results.append(hint)
                            else:
                                return hint
        return results if find_all else None

    @staticmethod
    def _find_hidden_quad(board, candidates, find_all=False):
        """
        Find hidden quads: four candidates that appear only in the same 4 cells.
        """
        results = [] if find_all else None
        houses = []
        for row in range(9):
            houses.append(('row', row, SudokuAnalyzer._get_house_cells('row', row)))
        for col in range(9):
            houses.append(('col', col, SudokuAnalyzer._get_house_cells('col', col)))
        for br in range(3):
            for bc in range(3):
                houses.append(('box', (br, bc), SudokuAnalyzer._get_house_cells('box', (br, bc))))

        for house_type, house_idx, cells in houses:
            empty_cells = [(r, c) for r, c in cells if board[r][c] == 0]

            # Build number -> cells map
            num_to_cells = {n: set() for n in range(1, 10)}
            for r, c in empty_cells:
                for n in candidates.get((r, c), set()):
                    num_to_cells[n].add((r, c))

            # Find quads of numbers that collectively appear in exactly 4 cells
            for nums in combinations(range(1, 10), 4):
                combined_cells = set()
                for n in nums:
                    combined_cells |= num_to_cells[n]

                if len(combined_cells) == 4:
                    # Each number must appear in at least 2 cells
                    if all(len(num_to_cells[n]) >= 2 for n in nums):
                        quad_cells = list(combined_cells)
                        quad_nums = list(nums)

                        eliminations = []
                        for r, c in quad_cells:
                            for n in candidates.get((r, c), set()):
                                if n not in quad_nums:
                                    eliminations.append((r, c, n))

                        if eliminations:
                            location = f"row {house_idx + 1}" if house_type == 'row' else \
                                       f"column {house_idx + 1}" if house_type == 'col' else \
                                       f"box ({house_idx[0] + 1},{house_idx[1] + 1})"
                            hint = {
                                'type': 'hidden_quad',
                                'numbers': quad_nums,
                                'cells': quad_cells,
                                'eliminations': eliminations,
                                'location': location
                            }
                            if find_all:
                                results.append(hint)
                            else:
                                return hint
        return results if find_all else None

    # =========================================================================
    # INTERSECTION TECHNIQUES
    # =========================================================================

    @staticmethod
    def _find_pointing_pair(board, candidates, find_all=False):
        """
        Find pointing pairs/triples: when all candidates for a number in a box
        are confined to a single row or column, eliminate that number from the
        rest of that row/column outside the box.
        """
        results = [] if find_all else None
        for num in range(1, 10):
            for br in range(3):
                for bc in range(3):
                    box_cells = SudokuAnalyzer._get_house_cells('box', (br, bc))
                    # Find cells in this box that can contain num
                    cells_with_num = [(r, c) for r, c in box_cells
                                      if board[r][c] == 0 and num in candidates.get((r, c), set())]

                    if len(cells_with_num) < 2:
                        continue

                    # Check if all are in the same row
                    rows = set(r for r, c in cells_with_num)
                    if len(rows) == 1:
                        row = list(rows)[0]
                        # Eliminate num from rest of this row outside the box
                        eliminations = []
                        for c in range(9):
                            if c // 3 != bc and board[row][c] == 0 and num in candidates.get((row, c), set()):
                                eliminations.append((row, c, num))

                        if eliminations:
                            hint = {
                                'type': 'pointing_pair',
                                'number': num,
                                'cells': cells_with_num,
                                'eliminations': eliminations,
                                'location': f"box ({br + 1},{bc + 1}) points along row {row + 1}"
                            }
                            if find_all:
                                results.append(hint)
                            else:
                                return hint

                    # Check if all are in the same column
                    cols = set(c for r, c in cells_with_num)
                    if len(cols) == 1:
                        col = list(cols)[0]
                        eliminations = []
                        for r in range(9):
                            if r // 3 != br and board[r][col] == 0 and num in candidates.get((r, col), set()):
                                eliminations.append((r, col, num))

                        if eliminations:
                            hint = {
                                'type': 'pointing_pair',
                                'number': num,
                                'cells': cells_with_num,
                                'eliminations': eliminations,
                                'location': f"box ({br + 1},{bc + 1}) points along column {col + 1}"
                            }
                            if find_all:
                                results.append(hint)
                            else:
                                return hint
        return results if find_all else None

    @staticmethod
    def _find_box_line_reduction(board, candidates, find_all=False):
        """
        Find box/line reductions: when all candidates for a number in a row/column
        are confined to a single box, eliminate that number from the rest of that box.
        """
        results = [] if find_all else None
        for num in range(1, 10):
            # Check rows
            for row in range(9):
                row_cells = [(row, c) for c in range(9)
                             if board[row][c] == 0 and num in candidates.get((row, c), set())]

                if len(row_cells) < 2:
                    continue

                # Check if all are in the same box
                boxes = set(c // 3 for r, c in row_cells)
                if len(boxes) == 1:
                    bc = list(boxes)[0]
                    br = row // 3
                    # Eliminate from rest of the box
                    eliminations = []
                    for r in range(br * 3, br * 3 + 3):
                        for c in range(bc * 3, bc * 3 + 3):
                            if r != row and board[r][c] == 0 and num in candidates.get((r, c), set()):
                                eliminations.append((r, c, num))

                    if eliminations:
                        hint = {
                            'type': 'box_line_reduction',
                            'number': num,
                            'cells': row_cells,
                            'eliminations': eliminations,
                            'location': f"row {row + 1} locked in box ({br + 1},{bc + 1})"
                        }
                        if find_all:
                            results.append(hint)
                        else:
                            return hint

            # Check columns
            for col in range(9):
                col_cells = [(r, col) for r in range(9)
                             if board[r][col] == 0 and num in candidates.get((r, col), set())]

                if len(col_cells) < 2:
                    continue

                boxes = set(r // 3 for r, c in col_cells)
                if len(boxes) == 1:
                    br = list(boxes)[0]
                    bc = col // 3
                    eliminations = []
                    for r in range(br * 3, br * 3 + 3):
                        for c in range(bc * 3, bc * 3 + 3):
                            if c != col and board[r][c] == 0 and num in candidates.get((r, c), set()):
                                eliminations.append((r, c, num))

                    if eliminations:
                        hint = {
                            'type': 'box_line_reduction',
                            'number': num,
                            'cells': col_cells,
                            'eliminations': eliminations,
                            'location': f"column {col + 1} locked in box ({br + 1},{bc + 1})"
                        }
                        if find_all:
                            results.append(hint)
                        else:
                            return hint
        return results if find_all else None

    # =========================================================================
    # FISH TECHNIQUES
    # =========================================================================

    @staticmethod
    def _find_xwing(board, candidates, find_all=False):
        """
        Find X-Wings: when a number appears in exactly 2 cells in each of 2 rows,
        and those cells are in the same 2 columns, eliminate from those columns.
        Also checks column-based X-Wings.
        """
        results = [] if find_all else None
        for num in range(1, 10):
            # Row-based X-Wing
            row_positions = {}
            for row in range(9):
                cols = [c for c in range(9) if board[row][c] == 0 and num in candidates.get((row, c), set())]
                if len(cols) == 2:
                    row_positions[row] = tuple(cols)

            # Find 2 rows with same column positions
            for r1, r2 in combinations(row_positions.keys(), 2):
                if row_positions[r1] == row_positions[r2]:
                    c1, c2 = row_positions[r1]
                    eliminations = []

                    # Eliminate from these columns in other rows
                    for r in range(9):
                        if r != r1 and r != r2:
                            if board[r][c1] == 0 and num in candidates.get((r, c1), set()):
                                eliminations.append((r, c1, num))
                            if board[r][c2] == 0 and num in candidates.get((r, c2), set()):
                                eliminations.append((r, c2, num))

                    if eliminations:
                        hint = {
                            'type': 'xwing',
                            'number': num,
                            'cells': [(r1, c1), (r1, c2), (r2, c1), (r2, c2)],
                            'eliminations': eliminations,
                            'location': f"rows {r1 + 1},{r2 + 1} cols {c1 + 1},{c2 + 1}"
                        }
                        if find_all:
                            results.append(hint)
                        else:
                            return hint

            # Column-based X-Wing
            col_positions = {}
            for col in range(9):
                rows = [r for r in range(9) if board[r][col] == 0 and num in candidates.get((r, col), set())]
                if len(rows) == 2:
                    col_positions[col] = tuple(rows)

            for c1, c2 in combinations(col_positions.keys(), 2):
                if col_positions[c1] == col_positions[c2]:
                    r1, r2 = col_positions[c1]
                    eliminations = []

                    for c in range(9):
                        if c != c1 and c != c2:
                            if board[r1][c] == 0 and num in candidates.get((r1, c), set()):
                                eliminations.append((r1, c, num))
                            if board[r2][c] == 0 and num in candidates.get((r2, c), set()):
                                eliminations.append((r2, c, num))

                    if eliminations:
                        hint = {
                            'type': 'xwing',
                            'number': num,
                            'cells': [(r1, c1), (r1, c2), (r2, c1), (r2, c2)],
                            'eliminations': eliminations,
                            'location': f"cols {c1 + 1},{c2 + 1} rows {r1 + 1},{r2 + 1}"
                        }
                        if find_all:
                            results.append(hint)
                        else:
                            return hint
        return results if find_all else None

    @staticmethod
    def _find_swordfish(board, candidates, find_all=False):
        """
        Find Swordfish patterns: 3 rows where a number appears in 2-3 columns each,
        and the union of columns is exactly 3.
        """
        results = [] if find_all else None
        for num in range(1, 10):
            # Row-based Swordfish
            row_cols = {}
            for row in range(9):
                cols = frozenset(c for c in range(9) if board[row][c] == 0 and num in candidates.get((row, c), set()))
                if 2 <= len(cols) <= 3:
                    row_cols[row] = cols

            for rows in combinations(row_cols.keys(), 3):
                combined_cols = set()
                for r in rows:
                    combined_cols |= row_cols[r]

                if len(combined_cols) == 3:
                    cols = list(combined_cols)
                    eliminations = []

                    # Eliminate from these columns in other rows
                    for r in range(9):
                        if r not in rows:
                            for c in cols:
                                if board[r][c] == 0 and num in candidates.get((r, c), set()):
                                    eliminations.append((r, c, num))

                    if eliminations:
                        cells = [(r, c) for r in rows for c in cols
                                 if board[r][c] == 0 and num in candidates.get((r, c), set())]
                        hint = {
                            'type': 'swordfish',
                            'number': num,
                            'cells': cells,
                            'eliminations': eliminations,
                            'location': f"rows {','.join(str(r+1) for r in rows)}"
                        }
                        if find_all:
                            results.append(hint)
                        else:
                            return hint

            # Column-based Swordfish
            col_rows = {}
            for col in range(9):
                rows = frozenset(r for r in range(9) if board[r][col] == 0 and num in candidates.get((r, col), set()))
                if 2 <= len(rows) <= 3:
                    col_rows[col] = rows

            for cols in combinations(col_rows.keys(), 3):
                combined_rows = set()
                for c in cols:
                    combined_rows |= col_rows[c]

                if len(combined_rows) == 3:
                    rows = list(combined_rows)
                    eliminations = []

                    for c in range(9):
                        if c not in cols:
                            for r in rows:
                                if board[r][c] == 0 and num in candidates.get((r, c), set()):
                                    eliminations.append((r, c, num))

                    if eliminations:
                        cells = [(r, c) for c in cols for r in rows
                                 if board[r][c] == 0 and num in candidates.get((r, c), set())]
                        hint = {
                            'type': 'swordfish',
                            'number': num,
                            'cells': cells,
                            'eliminations': eliminations,
                            'location': f"cols {','.join(str(c+1) for c in cols)}"
                        }
                        if find_all:
                            results.append(hint)
                        else:
                            return hint
        return results if find_all else None

    @staticmethod
    def _find_jellyfish(board, candidates, find_all=False):
        """
        Find Jellyfish patterns: 4 rows where a number appears in 2-4 columns each,
        and the union of columns is exactly 4.
        """
        results = [] if find_all else None
        for num in range(1, 10):
            # Row-based Jellyfish
            row_cols = {}
            for row in range(9):
                cols = frozenset(c for c in range(9) if board[row][c] == 0 and num in candidates.get((row, c), set()))
                if 2 <= len(cols) <= 4:
                    row_cols[row] = cols

            for rows in combinations(row_cols.keys(), 4):
                combined_cols = set()
                for r in rows:
                    combined_cols |= row_cols[r]

                if len(combined_cols) == 4:
                    cols = list(combined_cols)
                    eliminations = []

                    for r in range(9):
                        if r not in rows:
                            for c in cols:
                                if board[r][c] == 0 and num in candidates.get((r, c), set()):
                                    eliminations.append((r, c, num))

                    if eliminations:
                        cells = [(r, c) for r in rows for c in cols
                                 if board[r][c] == 0 and num in candidates.get((r, c), set())]
                        hint = {
                            'type': 'jellyfish',
                            'number': num,
                            'cells': cells,
                            'eliminations': eliminations,
                            'location': f"rows {','.join(str(r+1) for r in rows)}"
                        }
                        if find_all:
                            results.append(hint)
                        else:
                            return hint

            # Column-based Jellyfish
            col_rows = {}
            for col in range(9):
                rows = frozenset(r for r in range(9) if board[r][col] == 0 and num in candidates.get((r, col), set()))
                if 2 <= len(rows) <= 4:
                    col_rows[col] = rows

            for cols in combinations(col_rows.keys(), 4):
                combined_rows = set()
                for c in cols:
                    combined_rows |= col_rows[c]

                if len(combined_rows) == 4:
                    rows = list(combined_rows)
                    eliminations = []

                    for c in range(9):
                        if c not in cols:
                            for r in rows:
                                if board[r][c] == 0 and num in candidates.get((r, c), set()):
                                    eliminations.append((r, c, num))

                    if eliminations:
                        cells = [(r, c) for c in cols for r in rows
                                 if board[r][c] == 0 and num in candidates.get((r, c), set())]
                        hint = {
                            'type': 'jellyfish',
                            'number': num,
                            'cells': cells,
                            'eliminations': eliminations,
                            'location': f"cols {','.join(str(c+1) for c in cols)}"
                        }
                        if find_all:
                            results.append(hint)
                        else:
                            return hint
        return results if find_all else None


    # =========================================================================
    # UNIQUENESS TECHNIQUES
    # =========================================================================

    @staticmethod
    def _find_unique_rectangles(board, candidates, find_all=False):
        """
        Find Unique Rectangles: 4 unsolved cells forming a rectangle (2 rows x 2 cols)
        where all 4 share candidates {a, b}.  If 3+ cells have ONLY {a,b}, the puzzle
        would have 2 solutions, so the remaining cell(s) must use their extra candidates.

        Types handled:
          Type 1: 3 cells have exactly {a,b}, 1 roof cell has {a,b,+extras}
                  → eliminate a and b from the roof cell
          Type 2: 2 floor cells {a,b}, 2 roof cells each {a,b,x} (same x)
                  → eliminate x from all cells seeing both roof cells
          Type 4: 2 floor cells {a,b}, 2 roof cells {a,b,+extras};
                  in the house shared by the 2 roof cells, a (or b) appears
                  only in those 2 roof cells → eliminate the other value from them
        """
        results = [] if find_all else None
        seen = set()

        for r1, r2 in combinations(range(9), 2):
            for c1, c2 in combinations(range(9), 2):
                cells = [(r1, c1), (r1, c2), (r2, c1), (r2, c2)]

                # All 4 must be unsolved
                if any(board[r][c] != 0 for r, c in cells):
                    continue

                cell_cands = [candidates.get(cell, set()) for cell in cells]

                # Find candidates common to all 4 cells
                common = cell_cands[0].copy()
                for cc in cell_cands[1:]:
                    common &= cc
                if len(common) < 2:
                    continue

                for a, b in combinations(sorted(common), 2):
                    ab = frozenset({a, b})

                    # Cells with exactly {a,b} are floor; cells with {a,b,+} are roof
                    floor_cells = [cell for cell in cells if candidates.get(cell) == ab]
                    roof_cells  = [cell for cell in cells if candidates.get(cell) != ab]

                    if len(floor_cells) + len(roof_cells) != 4:
                        continue  # safety check

                    rect_key = (tuple(sorted(cells)), a, b)

                    # ----------------------------------------------------------
                    # Type 1: 3 floor, 1 roof → eliminate a and b from roof cell
                    # ----------------------------------------------------------
                    if len(floor_cells) == 3 and len(roof_cells) == 1:
                        t_key = rect_key + ('T1',)
                        if t_key not in seen:
                            target = roof_cells[0]
                            eliminations = [
                                (target[0], target[1], v) for v in (a, b)
                                if v in candidates.get(target, set())
                            ]
                            if eliminations:
                                seen.add(t_key)
                                hint = {
                                    'type': 'unique_rectangle',
                                    'ur_type': 1,
                                    'technique': 'unique_rectangle',
                                    'numbers': [a, b],
                                    'cells': cells,
                                    'eliminations': eliminations,
                                    'location': f"rows {r1+1},{r2+1} cols {c1+1},{c2+1}"
                                }
                                if find_all:
                                    results.append(hint)
                                else:
                                    return hint

                    # ----------------------------------------------------------
                    # Types 2 and 4: 2 floor, 2 roof
                    # ----------------------------------------------------------
                    elif len(floor_cells) == 2 and len(roof_cells) == 2:
                        R1, R2 = roof_cells
                        extra_R1 = candidates.get(R1, set()) - ab
                        extra_R2 = candidates.get(R2, set()) - ab

                        # Type 2: both roof cells have the same single extra candidate x
                        # → eliminate x from all cells that see both roof cells
                        if extra_R1 == extra_R2 and len(extra_R1) == 1:
                            x = next(iter(extra_R1))
                            t_key = rect_key + ('T2', x)
                            if t_key not in seen:
                                eliminations = [
                                    (r, c, x)
                                    for r in range(9) for c in range(9)
                                    if board[r][c] == 0
                                    and (r, c) not in cells
                                    and x in candidates.get((r, c), set())
                                    and SudokuAnalyzer._cells_see_each_other((r, c), R1)
                                    and SudokuAnalyzer._cells_see_each_other((r, c), R2)
                                ]
                                if eliminations:
                                    seen.add(t_key)
                                    hint = {
                                        'type': 'unique_rectangle',
                                        'ur_type': 2,
                                        'technique': 'unique_rectangle',
                                        'numbers': [a, b],
                                        'cells': cells,
                                        'eliminations': eliminations,
                                        'location': f"rows {r1+1},{r2+1} cols {c1+1},{c2+1}"
                                    }
                                    if find_all:
                                        results.append(hint)
                                    else:
                                        return hint

                        # Type 4: in a house shared by R1 and R2, one of {a,b} is
                        # locked to {R1,R2} → eliminate the other value from both
                        shared_houses = SudokuAnalyzer._get_shared_houses(R1, R2)
                        for _sh_type, _sh_idx, sh_cells in shared_houses:
                            sh_empty = [cell for cell in sh_cells if board[cell[0]][cell[1]] == 0]
                            for locked_val, elim_val in ((a, b), (b, a)):
                                others_with_locked = [
                                    cell for cell in sh_empty
                                    if cell not in cells
                                    and locked_val in candidates.get(cell, set())
                                ]
                                if not others_with_locked:
                                    eliminations = [
                                        (r, c, elim_val) for r, c in (R1, R2)
                                        if elim_val in candidates.get((r, c), set())
                                    ]
                                    if eliminations:
                                        t_key = rect_key + ('T4', locked_val)
                                        if t_key not in seen:
                                            seen.add(t_key)
                                            hint = {
                                                'type': 'unique_rectangle',
                                                'ur_type': 4,
                                                'technique': 'unique_rectangle',
                                                'numbers': [a, b],
                                                'cells': cells,
                                                'eliminations': eliminations,
                                                'location': f"rows {r1+1},{r2+1} cols {c1+1},{c2+1}"
                                            }
                                            if find_all:
                                                results.append(hint)
                                            else:
                                                return hint

        return results if find_all else None

    # =========================================================================
    # WING TECHNIQUES
    # =========================================================================

    @staticmethod
    def _find_xy_wing(board, candidates, find_all=False):
        """
        Find XY-Wings: A pivot cell with candidates {X,Y}, connected to:
        - Pincer 1 with candidates {X,Z}
        - Pincer 2 with candidates {Y,Z}
        All cells that see both pincers can have Z eliminated.
        """
        results = [] if find_all else None
        # Find all bivalue cells (cells with exactly 2 candidates)
        bivalue_cells = []
        for row in range(9):
            for col in range(9):
                if board[row][col] == 0 and len(candidates.get((row, col), set())) == 2:
                    bivalue_cells.append((row, col))

        for pivot in bivalue_cells:
            pr, pc = pivot
            pivot_cands = candidates.get((pr, pc), set())
            x, y = list(pivot_cands)

            # Find pincers that see the pivot
            pincers_x = []  # Cells with {X, Z}
            pincers_y = []  # Cells with {Y, Z}

            for cell in bivalue_cells:
                if cell == pivot:
                    continue
                if not SudokuAnalyzer._cells_see_each_other(pivot, cell):
                    continue

                cr, cc = cell
                cell_cands = candidates.get((cr, cc), set())

                if x in cell_cands and y not in cell_cands:
                    # This could be an X-pincer {X, Z}
                    pincers_x.append(cell)
                elif y in cell_cands and x not in cell_cands:
                    # This could be a Y-pincer {Y, Z}
                    pincers_y.append(cell)

            # Try all combinations of X-pincer and Y-pincer
            for pincer1 in pincers_x:
                for pincer2 in pincers_y:
                    if pincer1 == pincer2:
                        continue

                    p1_cands = candidates.get((pincer1[0], pincer1[1]), set())
                    p2_cands = candidates.get((pincer2[0], pincer2[1]), set())

                    # Find Z: the common candidate between pincers that's not X or Y
                    common = p1_cands & p2_cands
                    z_set = common - {x, y}

                    if len(z_set) == 1:
                        z = list(z_set)[0]

                        # Find cells that see both pincers and have Z
                        eliminations = []
                        for row in range(9):
                            for col in range(9):
                                if board[row][col] == 0:
                                    cell = (row, col)
                                    if cell != pivot and cell != pincer1 and cell != pincer2:
                                        if (SudokuAnalyzer._cells_see_each_other(cell, pincer1) and
                                            SudokuAnalyzer._cells_see_each_other(cell, pincer2)):
                                            if z in candidates.get((row, col), set()):
                                                eliminations.append((row, col, z))

                        if eliminations:
                            hint = {
                                'type': 'xy_wing',
                                'number': z,
                                'numbers': [x, y, z],
                                'cells': [pivot, pincer1, pincer2],
                                'eliminations': eliminations,
                                'location': f"pivot at ({pr+1},{pc+1})"
                            }
                            if find_all:
                                results.append(hint)
                            else:
                                return hint
        return results if find_all else None

    # =========================================================================
    # COLORING/CHAIN TECHNIQUES
    # =========================================================================

    @staticmethod
    def _find_simple_coloring(board, candidates, find_all=False):
        """
        Find simple coloring opportunities: For a single candidate, find chains of
        conjugate pairs and look for contradictions or eliminations.

        A conjugate pair is when a candidate appears in exactly 2 cells in a house.
        We color alternating cells in the chain and look for:
        1. Two same-colored cells in the same house (contradiction - opposite color is true)
        2. A cell that sees two opposite-colored cells (can eliminate the candidate)
        """
        results = [] if find_all else None
        for num in range(1, 10):
            # Build conjugate pair graph
            # Each cell is a node; edges connect conjugate pairs
            edges = []

            # Find conjugate pairs in rows
            for row in range(9):
                cells = [(row, c) for c in range(9)
                         if board[row][c] == 0 and num in candidates.get((row, c), set())]
                if len(cells) == 2:
                    edges.append((cells[0], cells[1]))

            # Find conjugate pairs in columns
            for col in range(9):
                cells = [(r, col) for r in range(9)
                         if board[r][col] == 0 and num in candidates.get((r, col), set())]
                if len(cells) == 2:
                    edges.append((cells[0], cells[1]))

            # Find conjugate pairs in boxes
            for br in range(3):
                for bc in range(3):
                    cells = []
                    for i in range(3):
                        for j in range(3):
                            r, c = br * 3 + i, bc * 3 + j
                            if board[r][c] == 0 and num in candidates.get((r, c), set()):
                                cells.append((r, c))
                    if len(cells) == 2:
                        edges.append((cells[0], cells[1]))

            if not edges:
                continue

            # Build adjacency list
            adj = {}
            for a, b in edges:
                if a not in adj:
                    adj[a] = []
                if b not in adj:
                    adj[b] = []
                if b not in adj[a]:
                    adj[a].append(b)
                if a not in adj[b]:
                    adj[b].append(a)

            # Find connected components and color them
            visited = set()
            for start in adj:
                if start in visited:
                    continue

                # BFS to color this component
                color = {}
                queue = [start]
                color[start] = 0

                while queue:
                    cell = queue.pop(0)
                    visited.add(cell)
                    for neighbor in adj.get(cell, []):
                        if neighbor not in color:
                            color[neighbor] = 1 - color[cell]
                            queue.append(neighbor)

                if len(color) < 2:
                    continue

                # Check for contradictions: two cells of same color in same house
                color_0 = [c for c, col in color.items() if col == 0]
                color_1 = [c for c, col in color.items() if col == 1]

                # Check color 0 for contradiction
                contradiction_0 = False
                for c1, c2 in combinations(color_0, 2):
                    if SudokuAnalyzer._cells_see_each_other(c1, c2):
                        contradiction_0 = True
                        break

                if contradiction_0:
                    # Color 0 is false, color 1 is true, eliminate from cells that see color 1
                    eliminations = []
                    for row in range(9):
                        for col in range(9):
                            cell = (row, col)
                            if board[row][col] == 0 and num in candidates.get((row, col), set()):
                                if cell not in color:
                                    # Check if it sees any color 1 cell
                                    for c1_cell in color_1:
                                        if SudokuAnalyzer._cells_see_each_other(cell, c1_cell):
                                            eliminations.append((row, col, num))
                                            break
                    # Also eliminate color 0 cells
                    for c0_cell in color_0:
                        eliminations.append((c0_cell[0], c0_cell[1], num))

                    if eliminations:
                        hint = {
                            'type': 'simple_coloring',
                            'number': num,
                            'cells': list(color.keys()),
                            'eliminations': eliminations,
                            'location': 'contradiction in color chain'
                        }
                        if find_all:
                            results.append(hint)
                        else:
                            return hint

                # Check color 1 for contradiction
                contradiction_1 = False
                for c1, c2 in combinations(color_1, 2):
                    if SudokuAnalyzer._cells_see_each_other(c1, c2):
                        contradiction_1 = True
                        break

                if contradiction_1:
                    eliminations = []
                    for row in range(9):
                        for col in range(9):
                            cell = (row, col)
                            if board[row][col] == 0 and num in candidates.get((row, col), set()):
                                if cell not in color:
                                    for c0_cell in color_0:
                                        if SudokuAnalyzer._cells_see_each_other(cell, c0_cell):
                                            eliminations.append((row, col, num))
                                            break
                    for c1_cell in color_1:
                        eliminations.append((c1_cell[0], c1_cell[1], num))

                    if eliminations:
                        hint = {
                            'type': 'simple_coloring',
                            'number': num,
                            'cells': list(color.keys()),
                            'eliminations': eliminations,
                            'location': 'contradiction in color chain'
                        }
                        if find_all:
                            results.append(hint)
                        else:
                            return hint

                # No contradiction - check for cells that see both colors
                for row in range(9):
                    for col in range(9):
                        cell = (row, col)
                        if board[row][col] == 0 and num in candidates.get((row, col), set()):
                            if cell in color:
                                continue

                            sees_0 = any(SudokuAnalyzer._cells_see_each_other(cell, c0)
                                        for c0 in color_0)
                            sees_1 = any(SudokuAnalyzer._cells_see_each_other(cell, c1)
                                        for c1 in color_1)

                            if sees_0 and sees_1:
                                hint = {
                                    'type': 'simple_coloring',
                                    'number': num,
                                    'cells': list(color.keys()),
                                    'eliminations': [(row, col, num)],
                                    'location': f"cell sees both colors"
                                }
                                if find_all:
                                    results.append(hint)
                                else:
                                    return hint
        return results if find_all else None

    @staticmethod
    def _find_forcing_chain(board, candidates, find_all=False, max_depth=2):
        """
        Find forcing chains: If placing a candidate leads to a contradiction.

        Only reports chains where contradiction occurs within max_depth steps,
        so the chain is human-followable.

        Depth 0: Initial placement directly empties a cell
        Depth 1: Initial placement forces one naked single, which empties a cell
        Depth 2: Two forced placements before contradiction
        """
        results = [] if find_all else None

        # Find bivalue cells
        bivalue_cells = []
        for row in range(9):
            for col in range(9):
                if board[row][col] == 0 and len(candidates.get((row, col), set())) == 2:
                    bivalue_cells.append((row, col))

        for start_cell in bivalue_cells:
            sr, sc = start_cell
            cand1, cand2 = list(candidates.get((sr, sc), set()))

            # Try placing cand1 and propagate
            result1, depth1, chain1 = SudokuAnalyzer._propagate_choice(board, candidates, sr, sc, cand1, max_depth)
            # Try placing cand2 and propagate
            result2, depth2, chain2 = SudokuAnalyzer._propagate_choice(board, candidates, sr, sc, cand2, max_depth)

            if result1 is None and depth1 <= max_depth:
                # cand1 leads to contradiction within depth limit
                hint = {
                    'type': 'forcing_chain',
                    'number': cand2,
                    'cell': start_cell,
                    'cells': [start_cell],
                    'eliminations': [(sr, sc, cand1)],
                    'location': f"forcing chain from ({sr+1},{sc+1})",
                    'depth': depth1,
                    'chain': chain1  # List of (row, col, value) placements leading to contradiction
                }
                if find_all:
                    results.append(hint)
                else:
                    return hint
            elif result2 is None and depth2 <= max_depth:
                # cand2 leads to contradiction within depth limit
                hint = {
                    'type': 'forcing_chain',
                    'number': cand1,
                    'cell': start_cell,
                    'cells': [start_cell],
                    'eliminations': [(sr, sc, cand2)],
                    'location': f"forcing chain from ({sr+1},{sc+1})",
                    'depth': depth2,
                    'chain': chain2
                }
                if find_all:
                    results.append(hint)
                else:
                    return hint

        return results if find_all else None

    @staticmethod
    def _propagate_choice(board, candidates, row, col, value, max_depth):
        """
        Propagate placing value at (row, col) and return resulting forced placements.

        Returns tuple: (result, depth, chain)
        - result: None if contradiction, else dict of {(row, col): value}
        - depth: Number of forced placements before contradiction (0 = immediate)
        - chain: List of (row, col, value) placements in order

        Stops propagating after max_depth forced placements.
        """
        # Make a copy of candidates
        new_cands = {}
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    new_cands[(r, c)] = set(candidates.get((r, c), set()))

        # Place the initial value
        result = {(row, col): value}
        chain = [(row, col, value)]
        new_cands[(row, col)] = set()

        # Remove from peers - check for immediate contradiction (depth 0)
        for c in range(9):
            if c != col and (row, c) in new_cands:
                new_cands[(row, c)].discard(value)
                if len(new_cands[(row, c)]) == 0 and board[row][c] == 0:
                    return (None, 0, chain)

        for r in range(9):
            if r != row and (r, col) in new_cands:
                new_cands[(r, col)].discard(value)
                if len(new_cands[(r, col)]) == 0 and board[r][col] == 0:
                    return (None, 0, chain)

        br, bc = row // 3, col // 3
        for i in range(3):
            for j in range(3):
                r, c = br * 3 + i, bc * 3 + j
                if (r, c) != (row, col) and (r, c) in new_cands:
                    new_cands[(r, c)].discard(value)
                    if len(new_cands[(r, c)]) == 0 and board[r][c] == 0:
                        return (None, 0, chain)

        # Propagate naked singles up to max_depth
        current_depth = 0
        changed = True
        while changed and current_depth < max_depth:
            changed = False
            for (r, c), cands in list(new_cands.items()):
                if board[r][c] == 0 and len(cands) == 1:
                    forced_val = list(cands)[0]
                    if (r, c) not in result:
                        result[(r, c)] = forced_val
                        chain.append((r, c, forced_val))
                        new_cands[(r, c)] = set()
                        changed = True
                        current_depth += 1

                        # Eliminate from peers (skip cells already in result)
                        for c2 in range(9):
                            if c2 != c and (r, c2) in new_cands and (r, c2) not in result:
                                new_cands[(r, c2)].discard(forced_val)
                                if len(new_cands[(r, c2)]) == 0 and board[r][c2] == 0:
                                    return (None, current_depth, chain)

                        for r2 in range(9):
                            if r2 != r and (r2, c) in new_cands and (r2, c) not in result:
                                new_cands[(r2, c)].discard(forced_val)
                                if len(new_cands[(r2, c)]) == 0 and board[r2][c] == 0:
                                    return (None, current_depth, chain)

                        br2, bc2 = r // 3, c // 3
                        for i in range(3):
                            for j in range(3):
                                r3, c3 = br2 * 3 + i, bc2 * 3 + j
                                if (r3, c3) != (r, c) and (r3, c3) in new_cands and (r3, c3) not in result:
                                    new_cands[(r3, c3)].discard(forced_val)
                                    if len(new_cands[(r3, c3)]) == 0 and board[r3][c3] == 0:
                                        return (None, current_depth, chain)

                        if current_depth >= max_depth:
                            break

        return (result, current_depth, chain)

    # =========================================================================
    # HINT FORMATTING METHODS
    # =========================================================================

    @staticmethod
    def _format_hint_level_1(hint):
        """Level 1: Just technique type"""
        type_messages = {
            'box_hidden_single': 'There are box hidden singles available',
            'rowcol_hidden_single': 'There are row/column hidden singles available',
            'hidden_single': 'There are hidden singles available',
            'naked_single': 'There are naked singles available',
            'naked_pair': 'There is a naked pair available',
            'naked_triple': 'There is a naked triple available',
            'naked_quad': 'There is a naked quad available',
            'hidden_pair': 'There is a hidden pair available',
            'hidden_triple': 'There is a hidden triple available',
            'hidden_quad': 'There is a hidden quad available',
            'pointing_pair': 'There is a pointing pair/triple available',
            'box_line_reduction': 'There is a box/line reduction available',
            'xwing': 'There is an X-Wing available',
            'swordfish': 'There is a Swordfish available',
            'jellyfish': 'There is a Jellyfish available',
            'xy_wing': 'There is an XY-Wing available',
            'simple_coloring': 'There is a simple coloring opportunity',
            'forcing_chain': 'There is a forcing chain available',
            'unique_rectangle': 'There is a Unique Rectangle available'
        }
        return type_messages.get(hint['type'], 'A technique is available')

    @staticmethod
    def _format_hint_level_2(hint):
        """Level 2: Technique + number(s)"""
        hint_type = hint['type']

        # Techniques with multiple numbers
        if hint_type in ('naked_pair', 'naked_triple', 'naked_quad',
                         'hidden_pair', 'hidden_triple', 'hidden_quad', 'xy_wing'):
            nums = hint.get('numbers', [])
            nums_str = ','.join(str(n) for n in sorted(nums))
            return f"{hint_type.replace('_', ' ').title()} with numbers {{{nums_str}}}"

        # Unique rectangle - show type number
        if hint_type == 'unique_rectangle':
            nums = hint.get('numbers', [])
            nums_str = ','.join(str(n) for n in sorted(nums))
            ur_type = hint.get('ur_type', '')
            return f"Unique Rectangle Type {ur_type} with numbers {{{nums_str}}}"

        # Forcing chain - show depth
        if hint_type == 'forcing_chain':
            depth = hint.get('depth', '?')
            return f"Forcing chain (depth {depth})"

        # Single-number techniques
        num = hint.get('number', '?')
        return f"Number {num} has a {hint_type.replace('_', ' ')}"

    @staticmethod
    def _format_hint_level_3(hint):
        """Level 3: Technique + number + location"""
        hint_type = hint['type']
        location = hint.get('location', '')

        # Techniques with eliminations (show what gets eliminated)
        if hint_type in ('naked_pair', 'naked_triple', 'naked_quad',
                         'hidden_pair', 'hidden_triple', 'hidden_quad',
                         'pointing_pair', 'box_line_reduction',
                         'xwing', 'swordfish', 'jellyfish',
                         'xy_wing', 'simple_coloring',
                         'unique_rectangle'):
            nums = hint.get('numbers', [hint.get('number')])
            if nums:
                nums_str = ','.join(str(n) for n in sorted(nums) if n)
                return f"{hint_type.replace('_', ' ').title()} ({nums_str}) in {location}"
            return f"{hint_type.replace('_', ' ').title()} in {location}"

        # Forcing chain - show depth and starting cell
        if hint_type == 'forcing_chain':
            depth = hint.get('depth', '?')
            row, col = hint.get('cell', (0, 0))
            return f"Forcing chain (depth {depth}) from cell ({row+1},{col+1})"

        # Single placement techniques
        num = hint.get('number', '?')
        return f"Number {num} has a {hint_type.replace('_', ' ')} in {location}"

    @staticmethod
    def _format_hint_level_4(hint):
        """Level 4: Show cell(s) involved"""
        hint_type = hint['type']

        # Techniques with multiple cells
        if 'cells' in hint and hint['cells']:
            cells = hint['cells']
            if hint_type in ('naked_pair', 'naked_triple', 'naked_quad',
                             'hidden_pair', 'hidden_triple', 'hidden_quad',
                             'xwing', 'swordfish', 'jellyfish',
                             'xy_wing', 'simple_coloring',
                             'unique_rectangle'):
                cells_str = ', '.join(f"({r+1},{c+1})" for r, c in cells[:4])
                if len(cells) > 4:
                    cells_str += f" + {len(cells) - 4} more"
                nums = hint.get('numbers', [hint.get('number')])
                nums_str = ','.join(str(n) for n in sorted(nums) if n)
                return f"{hint_type.replace('_', ' ').title()} ({nums_str}) at {cells_str}"

            elif hint_type in ('pointing_pair', 'box_line_reduction'):
                num = hint.get('number', '?')
                elims = hint.get('eliminations', [])
                if elims:
                    elim_cells = ', '.join(f"({r+1},{c+1})" for r, c, n in elims[:3])
                    return f"{hint_type.replace('_', ' ').title()}: {num} can be removed from {elim_cells}"
                return f"{hint_type.replace('_', ' ').title()} for {num}"

        # Forcing chain with depth info
        if hint_type == 'forcing_chain':
            if 'cell' in hint:
                row, col = hint['cell']
                num = hint.get('number', '?')
                depth = hint.get('depth', '?')
                return f"Forcing chain (depth {depth}): {num} must go in ({row+1},{col+1})"

        # Single cell techniques
        if 'cell' in hint:
            row, col = hint['cell']
            num = hint.get('number', '?')
            return f"Number {num} goes in cell ({row+1},{col+1})"

        return SudokuAnalyzer._format_hint_level_3(hint)

    @staticmethod
    def _format_hint_level_5(hint):
        """Level 5: Give complete answer with eliminations"""
        hint_type = hint['type']

        # Techniques that eliminate candidates
        if hint_type in ('naked_pair', 'naked_triple', 'naked_quad',
                         'hidden_pair', 'hidden_triple', 'hidden_quad',
                         'pointing_pair', 'box_line_reduction',
                         'xwing', 'swordfish', 'jellyfish',
                         'xy_wing', 'simple_coloring',
                         'unique_rectangle'):
            elims = hint.get('eliminations', [])
            if elims:
                elim_str = ', '.join(f"{n} from ({r+1},{c+1})" for r, c, n in elims[:5])
                if len(elims) > 5:
                    elim_str += f" + {len(elims) - 5} more"
                return f"Eliminate: {elim_str}"
            return SudokuAnalyzer._format_hint_level_4(hint)

        # Forcing chain with full chain description
        if hint_type == 'forcing_chain':
            chain = hint.get('chain', [])
            depth = hint.get('depth', 0)
            elims = hint.get('eliminations', [])

            if chain and elims:
                # Build chain description
                wrong_val = elims[0][2]  # The eliminated candidate
                chain_parts = []
                for r, c, v in chain:
                    chain_parts.append(f"{v} at ({r+1},{c+1})")
                chain_str = ' -> '.join(chain_parts)
                return f"If {wrong_val}: {chain_str} -> contradiction"

            if 'cell' in hint:
                row, col = hint['cell']
                num = hint.get('number', '?')
                return f"Place {num} in cell ({row+1},{col+1})"

        # Single placement techniques
        if 'cell' in hint:
            row, col = hint['cell']
            num = hint.get('number', '?')
            return f"Place {num} in cell ({row+1},{col+1})"

        return SudokuAnalyzer._format_hint_level_4(hint)
