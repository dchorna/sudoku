from __future__ import annotations

from typing import Iterable

from model.board import Board


def normalize_board(board: Board | list[list[int]]) -> Board:
    if isinstance(board, Board):
        return board.copy()
    return Board(board)


def adjacent_wall_relation(walls: dict[tuple[tuple[int, int], tuple[int, int]], bool], a: tuple[int, int], b: tuple[int, int]) -> bool | None:
    if (a, b) in walls:
        return walls[(a, b)]
    if (b, a) in walls:
        return walls[(b, a)]
    return None


def candidate_values(board: Board, row: int, col: int, walls: dict[tuple[tuple[int, int], tuple[int, int]], bool] | None = None) -> list[int]:
    if board.get_value(row, col) != 0:
        return []

    values: list[int] = []
    for value in range(1, 10):
        if any(board.get_value(row, idx) == value for idx in range(9) if idx != col):
            continue
        if any(board.get_value(idx, col) == value for idx in range(9) if idx != row):
            continue

        box_row_start = (row // 3) * 3
        box_col_start = (col // 3) * 3
        if any(
            board.get_value(r, c) == value
            for r in range(box_row_start, box_row_start + 3)
            for c in range(box_col_start, box_col_start + 3)
            if (r, c) != (row, col)
        ):
            continue

        if walls:
            valid = True
            for neighbor_row, neighbor_col in Board.neighbors(row, col):
                neighbor_value = board.get_value(neighbor_row, neighbor_col)
                if neighbor_value == 0:
                    continue
                relation = adjacent_wall_relation(walls, (row, col), (neighbor_row, neighbor_col))
                if relation is None:
                    continue
                diff = abs(value - neighbor_value)
                if relation and diff != 1:
                    valid = False
                    break
                if not relation and diff == 1:
                    valid = False
                    break
            if not valid:
                continue

        values.append(value)

    return values


def select_mrv_cell(board: Board, walls: dict[tuple[tuple[int, int], tuple[int, int]], bool] | None = None) -> tuple[int, int] | None:
    best_cell = None
    best_candidates: list[int] | None = None

    for row in range(9):
        for col in range(9):
            if board.get_value(row, col) != 0:
                continue
            candidates = candidate_values(board, row, col, walls)
            if not candidates:
                return row, col
            if best_candidates is None or len(candidates) < len(best_candidates):
                best_cell = (row, col)
                best_candidates = candidates

    return best_cell


def _search(board: Board, walls: dict[tuple[tuple[int, int], tuple[int, int]], bool] | None = None) -> Board | None:
    if not board.is_valid_with_walls(walls):
        return None
    if board.is_complete():
        return board

    cell = select_mrv_cell(board, walls)
    if cell is None:
        return board

    row, col = cell
    for value in candidate_values(board, row, col, walls):
        board.set_value(row, col, value)
        if board.is_valid_with_walls(walls):
            result = _search(board, walls)
            if result is not None:
                return result
        board.set_value(row, col, 0)

    return None


def solve_board(board: Board | list[list[int]], walls: dict[tuple[tuple[int, int], tuple[int, int]], bool] | None = None) -> Board | None:
    working_board = normalize_board(board)
    if not working_board.is_valid_with_walls(walls):
        return None
    return _search(working_board, walls)
