from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

BoardCell = Tuple[int, int]
BoardGrid = List[List[int]]


def box_indices(row: int, col: int) -> list[BoardCell]:
    box_row_start = (row // 3) * 3
    box_col_start = (col // 3) * 3
    return [
        (r, c)
        for r in range(box_row_start, box_row_start + 3)
        for c in range(box_col_start, box_col_start + 3)
    ]


class Board:
    def __init__(self, grid: Sequence[Sequence[int]] | None = None):
        if grid is None:
            self.grid: BoardGrid = [[0 for _ in range(9)] for _ in range(9)]
            return

        rows = [list(row) for row in grid]
        if len(rows) != 9 or any(len(row) != 9 for row in rows):
            raise ValueError("Board must be a 9x9 grid.")

        self.grid = rows

    def copy(self) -> "Board":
        return Board([row[:] for row in self.grid])

    def get_value(self, row: int, col: int) -> int:
        return self.grid[row][col]

    def set_value(self, row: int, col: int, value: int) -> None:
        if not 0 <= row < 9 or not 0 <= col < 9:
            raise IndexError("Cell coordinates are out of bounds.")
        if value < 0 or value > 9:
            raise ValueError("Cell value must be between 0 and 9.")
        self.grid[row][col] = value

    def is_complete(self) -> bool:
        return all(value != 0 for row in self.grid for value in row)

    def is_valid(self) -> bool:
        return self._all_rows_valid() and self._all_cols_valid() and self._all_boxes_valid()

    def is_valid_with_walls(self, walls: dict[tuple[tuple[int, int], tuple[int, int]], bool] | None = None) -> bool:
        if not self.is_valid():
            return False
        if not walls:
            return True

        for (a, b), has_wall in walls.items():
            value_a = self.get_value(*a)
            value_b = self.get_value(*b)
            if value_a == 0 or value_b == 0:
                continue
            diff = abs(value_a - value_b)
            if has_wall and diff != 1:
                return False
            if not has_wall and diff == 1:
                return False
        return True

    def _all_rows_valid(self) -> bool:
        for row in self.grid:
            seen = set()
            for value in row:
                if value == 0:
                    continue
                if value in seen:
                    return False
                seen.add(value)
        return True

    def _all_cols_valid(self) -> bool:
        for col in range(9):
            seen = set()
            for row in range(9):
                value = self.grid[row][col]
                if value == 0:
                    continue
                if value in seen:
                    return False
                seen.add(value)
        return True

    def _all_boxes_valid(self) -> bool:
        for row in range(0, 9, 3):
            for col in range(0, 9, 3):
                seen = set()
                for r in range(row, row + 3):
                    for c in range(col, col + 3):
                        value = self.grid[r][c]
                        if value == 0:
                            continue
                        if value in seen:
                            return False
                        seen.add(value)
        return True

    @staticmethod
    def neighbors(row: int, col: int) -> list[BoardCell]:
        candidates = [
            (row, col - 1),
            (row, col + 1),
            (row - 1, col),
            (row + 1, col),
        ]
        return [(r, c) for r, c in candidates if 0 <= r < 9 and 0 <= c < 9]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Board):
            return NotImplemented
        return self.grid == other.grid

    def __repr__(self) -> str:
        return f"Board({self.grid!r})"


def is_valid_placement(
    board: Board, 
    row: int, 
    col: int, 
    value: int, 
    walls: dict[tuple[tuple[int, int], tuple[int, int]], bool] | None = None
) -> bool:
    if value == 0:
        return True

    # 1. Класичні перевірки (рядок, стовпець, квадрат)
    if board.get_value(row, col) != 0 and board.get_value(row, col) != value:
        return False

    for index in range(9):
        if index != col and board.get_value(row, index) == value:
            return False
    for index in range(9):
        if index != row and board.get_value(index, col) == value:
            return False

    for r, c in box_indices(row, col):
        if (r, c) != (row, col) and board.get_value(r, c) == value:
            return False

    # 2. Перевірка перегородок (якщо вони передані для другого режиму)
    if walls:
        for r, c in Board.neighbors(row, col):
            neighbor_value = board.get_value(r, c)
            if neighbor_value == 0:
                continue  # Сусід ще порожній, конфлікту поки немає
            
            # Перевіряємо наявність перегородки між поточною клітинкою та сусідом
            has_wall = walls.get(((row, col), (r, c)))
            if has_wall is not None:
                diff = abs(value - neighbor_value)
                
                # Якщо є перегородка, різниця має бути рівно 1
                if has_wall and diff != 1:
                    return False
                # Якщо перегородки немає, різниця НЕ може бути 1
                if not has_wall and diff == 1:
                    return False

    return True