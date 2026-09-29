import random

from model.board import Board, is_valid_placement


def select_empty_cell(board: Board) -> tuple[int, int] | None:
    for row in range(9):
        for col in range(9):
            if board.get_value(row, col) == 0:
                return row, col
    return None


def is_consistent(board: Board, row: int, col: int, value: int) -> bool:
    return is_valid_placement(board, row, col, value)


def fill_board(board: Board) -> bool:
    cell = select_empty_cell(board)
    if cell is None:
        return True

    row, col = cell
    values = list(range(1, 10))
    random.shuffle(values)

    for value in values:
        if is_consistent(board, row, col, value):
            board.set_value(row, col, value)
            if fill_board(board):
                return True
            board.set_value(row, col, 0)

    return False


def generate_full_board() -> Board:
    board = Board()
    if not fill_board(board):
        raise RuntimeError("Failed to generate a valid Sudoku board.")
    return board
