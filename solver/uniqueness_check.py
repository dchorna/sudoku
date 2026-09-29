from __future__ import annotations

from model.board import Board
from solver.solver import candidate_values, select_mrv_cell


def _count_solutions(board: Board, walls: dict[tuple[tuple[int, int], tuple[int, int]], bool] | None = None, limit: int = 2) -> int:
    if not board.is_valid_with_walls(walls):
        return 0

    if board.is_complete():
        return 1

    cell = select_mrv_cell(board, walls)
    if cell is None:
        return 1

    row, col = cell
    count = 0

    for value in candidate_values(board, row, col, walls):
        board.set_value(row, col, value)
        if board.is_valid_with_walls(walls):
            count += _count_solutions(board, walls, limit - count if count else limit)
            if count >= limit:
                board.set_value(row, col, 0)
                return count
        board.set_value(row, col, 0)

    return count


def has_unique_solution(board: Board | list[list[int]], walls: dict[tuple[tuple[int, int], tuple[int, int]], bool] | None = None) -> bool:
    working_board = Board(board) if not isinstance(board, Board) else board.copy()
    return _count_solutions(working_board, walls, limit=2) == 1


def count_solutions(board: Board | list[list[int]], walls: dict[tuple[tuple[int, int], tuple[int, int]], bool] | None = None, limit: int = 2) -> int:
    working_board = Board(board) if not isinstance(board, Board) else board.copy()
    return _count_solutions(working_board, walls, limit=limit)
