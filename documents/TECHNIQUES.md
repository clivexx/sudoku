# Sudoku Solving Techniques

This document describes the 18 solving techniques implemented in `shared/sudoku_analyzer.py`, organized by difficulty and type.

---

## Overview

Techniques fall into two categories:

- **Placement techniques** - Directly place a number in a cell (Singles)
- **Elimination techniques** - Remove candidates from cells, enabling future placements

The hint system tries techniques in difficulty order, returning the easiest applicable technique first.

---

## 1. Placement Techniques (Singles)

### 1.1 Box Hidden Single

**Theory:** If a number can only go in one cell within a 3x3 box, it must go there - even if that cell has other candidates.

**Example:** In box (1,1), the number 7 can only be placed in cell (2,3) because all other cells either contain numbers or see a 7 in their row/column.

**Implementation:** (`_find_box_hidden_single`)
- For each number 1-9 and each box
- Find all empty cells where that number is a valid placement
- If exactly one cell found, return that as the hint

```python
for num in range(1, 10):
    for box_row in range(3):
        for box_col in range(3):
            possible_cells = [cells where num is valid]
            if len(possible_cells) == 1:
                return hint
```

---

### 1.2 Row/Column Hidden Single (Limited)

**Theory:** Same as hidden single, but in a row or column. This variant only fires when the row/column has 2 or fewer empty cells - making it nearly as easy as a box hidden single visually.

**Implementation:** (`_find_rowcol_single_limited`)
- For each row/column with ≤2 empty cells
- Check if any number can only go in one position
- Return first such case

---

### 1.3 Any Hidden Single

**Theory:** A number that can only go in one cell within ANY house (row, column, or box) must go there.

**Implementation:** (`_find_any_hidden_single`)
- Checks all rows, then all columns, then all boxes
- For each house and each number, find valid positions
- Return if exactly one position exists

---

### 1.4 Naked Single

**Theory:** If a cell has only one candidate remaining (all other numbers eliminated by row/column/box constraints), that candidate must be the answer.

**Example:** Cell (5,5) can only contain 3 because 1,2,4,5,6,7,8,9 all appear in its row, column, or box.

**Implementation:** (`_find_naked_single`)
```python
for row in range(9):
    for col in range(9):
        if board[row][col] == 0:
            candidates = SudokuSolver.get_candidates(board, row, col)
            if len(candidates) == 1:
                return hint with that number
```

---

## 2. Naked Subset Techniques

These find groups of cells where N cells contain only N candidates combined, allowing elimination from other cells in the house.

### 2.1 Naked Pair

**Theory:** If two cells in a house both have exactly the same two candidates {A, B}, then A and B must go in those two cells (we don't know which goes where, but they're "locked"). Therefore, A and B can be eliminated from all other cells in that house.

**Example:** In row 3, cells (3,2) and (3,7) both have candidates {4, 9}. Remove 4 and 9 from all other cells in row 3.

**Implementation:** (`_find_naked_pair`)
- For each house (row/col/box)
- Find cells with exactly 2 candidates
- If two cells have identical candidate sets, check for eliminations in other cells
- Only reports if eliminations exist (house must have >2 empty cells)

```python
for (r1, c1), (r2, c2) in combinations(pairs_cells, 2):
    if candidates[(r1, c1)] == candidates[(r2, c2)]:
        # Found pair - check other cells for eliminations
```

---

### 2.2 Naked Triple

**Theory:** If three cells in a house have candidates that form a combined set of exactly 3 numbers, those three numbers are locked to those cells. Individual cells may have 2 or 3 of these candidates.

**Example:** Three cells have {1,2}, {2,3}, {1,3}. Combined = {1,2,3}. These three numbers must go in these three cells.

**Implementation:** (`_find_naked_triple`)
- Find cells with 2-3 candidates
- Check all combinations of 3 such cells
- If combined candidates = 3 numbers, eliminate from other cells

---

### 2.3 Naked Quad

**Theory:** Same principle extended to 4 cells with 4 combined candidates.

**Implementation:** (`_find_naked_quad`)
- Find cells with 2-4 candidates
- Check combinations of 4 cells
- Combined candidates must equal exactly 4

---

## 3. Hidden Subset Techniques

The "dual" of naked subsets - instead of looking at cells, look at where numbers can go.

### 3.1 Hidden Pair

**Theory:** If two numbers in a house can only appear in the same two cells, those cells must contain those numbers. All OTHER candidates in those two cells can be eliminated.

**Example:** In column 5, numbers 3 and 7 can only go in cells (2,5) and (6,5). Even if those cells have other candidates like {1,3,5,7,9}, we can remove 1, 5, 9 - leaving only {3,7}.

**Implementation:** (`_find_hidden_pair`)
```python
# Build map: number -> cells that can contain it
num_to_cells = {n: [] for n in range(1, 10)}
for cell in empty_cells:
    for n in candidates[cell]:
        num_to_cells[n].append(cell)

# Find two numbers appearing in exactly the same 2 cells
for n1, n2 in combinations(range(1, 10), 2):
    if len(num_to_cells[n1]) == 2 and num_to_cells[n1] == num_to_cells[n2]:
        # Eliminate other candidates from these cells
```

---

### 3.2 Hidden Triple

**Theory:** Three numbers that collectively appear in exactly 3 cells. Eliminate other candidates from those cells.

**Implementation:** (`_find_hidden_triple`)
- Requires each number to appear in at least 2 of the 3 cells (otherwise it's a simpler pattern)

---

### 3.3 Hidden Quad

**Theory:** Four numbers in exactly 4 cells.

**Implementation:** (`_find_hidden_quad`)
- Same approach, combinations of 4 numbers

---

## 4. Intersection Techniques

These exploit the overlap between boxes and rows/columns.

### 4.1 Pointing Pair/Triple

**Theory:** If all candidates for a number within a box are confined to a single row or column, that number can be eliminated from the rest of that row/column outside the box.

**Example:** In box (1,1), number 5 can only go in cells (1,1), (1,2), (1,3) - all in row 1. Since one of these must be 5, eliminate 5 from all other cells in row 1 (columns 4-9).

**Implementation:** (`_find_pointing_pair`)
```python
for num in range(1, 10):
    for each box:
        cells_with_num = [cells in box that can contain num]
        rows = set(r for r, c in cells_with_num)
        if len(rows) == 1:
            # All in same row - eliminate from rest of row outside box
        # Same check for columns
```

---

### 4.2 Box/Line Reduction

**Theory:** The inverse of pointing pairs. If all candidates for a number in a row/column are confined to a single box, eliminate that number from the rest of the box.

**Example:** In row 4, number 8 can only go in cells (4,4), (4,5), (4,6) - all in box (2,2). Eliminate 8 from other cells in that box.

**Implementation:** (`_find_box_line_reduction`)
- For each row, check if all positions for a number fall in one box
- Same for columns

---

## 5. Fish Techniques

Fish patterns exploit the constraint that each number appears exactly once per row and column.

### 5.1 X-Wing

**Theory:** If a number appears in exactly 2 cells in each of 2 rows, and those cells align in the same 2 columns, then the number must occupy the corners of this rectangle. Eliminate from other cells in those columns.

**Visual:**
```
Row 3:  . X . . X .    X marks where number can go
Row 7:  . X . . X .
        Col 2  Col 5

Eliminate from cols 2 and 5 in all other rows.
```

**Implementation:** (`_find_xwing`)
```python
# Row-based X-Wing
row_positions = {}
for row in range(9):
    cols = [c where num is candidate in (row, c)]
    if len(cols) == 2:
        row_positions[row] = tuple(cols)

# Find two rows with same column positions
for r1, r2 in combinations(row_positions.keys(), 2):
    if row_positions[r1] == row_positions[r2]:
        # Eliminate from these columns in other rows
```

Also checks column-based X-Wings (2 columns, same 2 rows).

---

### 5.2 Swordfish

**Theory:** Extension of X-Wing to 3 rows. If a number appears in 2-3 columns in each of 3 rows, and the union of columns is exactly 3, eliminate from those columns in other rows.

**Implementation:** (`_find_swordfish`)
- Find rows where number appears in 2-3 columns
- Check combinations of 3 rows
- If combined columns = 3, eliminate from those columns elsewhere

---

### 5.3 Jellyfish

**Theory:** Extension to 4 rows/columns.

**Implementation:** (`_find_jellyfish`)
- Same pattern, 4 rows with combined 4 columns (or vice versa)

---

## 6. Wing Techniques

### 6.1 XY-Wing

**Theory:** Uses three bivalue cells (cells with exactly 2 candidates) in a specific pattern:
- Pivot cell with candidates {X, Y}
- Pincer 1 (sees pivot) with candidates {X, Z}
- Pincer 2 (sees pivot) with candidates {Y, Z}

If pivot = X, then pincer 1 = Z.
If pivot = Y, then pincer 2 = Z.
Either way, one of the pincers contains Z.

Therefore: Any cell that sees BOTH pincers cannot contain Z.

**Example:**
```
Pivot (5,5): {3, 7}
Pincer 1 (5,2): {3, 9}  - shares row with pivot
Pincer 2 (8,5): {7, 9}  - shares column with pivot

Cell (8,2) sees both pincers -> eliminate 9
```

**Implementation:** (`_find_xy_wing`)
```python
for pivot in bivalue_cells:
    x, y = pivot candidates
    pincers_x = [cells with {X, Z} that see pivot]
    pincers_y = [cells with {Y, Z} that see pivot]

    for pincer1 in pincers_x:
        for pincer2 in pincers_y:
            z = common candidate between pincers (not X or Y)
            # Eliminate Z from cells seeing both pincers
```

---

## 7. Coloring/Chain Techniques

### 7.1 Simple Coloring

**Theory:** For a single candidate number, build chains of "conjugate pairs" - pairs of cells in a house where the number can only go in those two cells. In such a pair, exactly one cell will contain the number.

Color alternating cells in the chain (say, blue and green). Then:
1. **Contradiction:** If two same-colored cells see each other, that color is impossible - eliminate the candidate from all cells of that color.
2. **Trap:** If an uncolored cell sees both colors, eliminate the candidate - one color must be true, so that cell can't have it.

**Implementation:** (`_find_simple_coloring`)
```python
# Build conjugate pair graph
edges = []
for each house:
    cells = [cells where num is candidate]
    if len(cells) == 2:
        edges.append((cells[0], cells[1]))

# BFS to color connected components
for start in nodes:
    color[start] = 0
    for each neighbor:
        color[neighbor] = 1 - color[current]

# Check for contradictions (same color sees itself)
for c1, c2 in combinations(color_0, 2):
    if cells_see_each_other(c1, c2):
        # Contradiction - color_0 is false

# Check for traps (uncolored cell sees both colors)
for cell not in chain:
    if sees_color_0 and sees_color_1:
        # Eliminate candidate from cell
```

---

### 7.2 Forcing Chain

**Theory:** For a bivalue cell, assume each candidate in turn and propagate the consequences. If one assumption leads to a contradiction, the other must be true. If both assumptions lead to the same conclusion about another cell, that conclusion is certain.

**Implementation:** (`_find_forcing_chain` and `_propagate_choice`)

```python
for start_cell in bivalue_cells:
    cand1, cand2 = candidates of start_cell

    result1 = propagate_choice(cand1)  # None if contradiction
    result2 = propagate_choice(cand2)

    if result1 is None:
        # cand1 leads to contradiction, cand2 must be true
        return elimination hint for cand1

    if result2 is None:
        # cand2 leads to contradiction
        return elimination hint for cand2

    # Check if both paths agree on some cell
    for cell in result1 and result2:
        if result1[cell] == result2[cell]:
            # Both paths force same value - it's certain
```

The `_propagate_choice` function:
1. Places the assumed value
2. Eliminates from all peers
3. Recursively propagates any resulting naked singles
4. Returns None on contradiction (cell loses all candidates)
5. Has depth limit of 10 to prevent infinite recursion

---

## Technique Difficulty Order

The hint system tries techniques in this order (easiest first):

1. Box Hidden Single
2. Row/Col Hidden Single (limited)
3. Any Hidden Single
4. Naked Single
5. Naked Pair
6. Naked Triple
7. Naked Quad
8. Hidden Pair
9. Hidden Triple
10. Hidden Quad
11. Pointing Pair/Triple
12. Box/Line Reduction
13. X-Wing
14. Swordfish
15. Jellyfish
16. XY-Wing
17. Simple Coloring
18. Forcing Chain

---

## Data Structures

**Board:** 9x9 list of lists, 0 = empty cell

**Candidates:** Dictionary with `(row, col)` tuple keys and `set` values
```python
candidates = {
    (0, 0): {1, 4, 7},
    (0, 1): {2, 3},
    ...
}
# Access: candidates.get((r, c), set())
```

**Hint return format:**
```python
{
    'type': 'technique_name',
    'number': int,           # For single-number techniques
    'numbers': [int, ...],   # For multi-number techniques
    'cell': (row, col),      # For placement hints
    'cells': [(r, c), ...],  # Pattern cells
    'eliminations': [(r, c, num), ...],  # What to remove
    'location': str          # Human-readable location
}
```

---

## Not Yet Implemented

- **Unique Rectangles** - Exploit the requirement that valid puzzles have unique solutions
- **Finned Fish** - X-Wing/Swordfish with extra "fin" cells
- **ALS (Almost Locked Sets)** - Advanced chain techniques
- **Nice Loops** - General chain/loop patterns
