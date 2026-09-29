from model.board import Board, box_indices


def test_board_initialization_and_set_value():
    board = Board()
    assert board.grid == [[0 for _ in range(9)] for _ in range(9)]

    board.set_value(0, 0, 5)
    assert board.get_value(0, 0) == 5
    assert board.is_complete() is False


def test_board_detects_duplicate_in_row_column_and_box():
    board = Board()
    board.set_value(0, 0, 1)
    board.set_value(0, 1, 1)
    assert board.is_valid() is False

    board = Board()
    board.set_value(0, 0, 1)
    board.set_value(1, 0, 1)
    assert board.is_valid() is False

    board = Board()
    board.set_value(0, 0, 1)
    board.set_value(1, 1, 1)
    assert board.is_valid() is False


def test_box_indices_and_neighbors():
    assert box_indices(0, 0) == [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)]
    assert box_indices(8, 8) == [(6, 6), (6, 7), (6, 8), (7, 6), (7, 7), (7, 8), (8, 6), (8, 7), (8, 8)]

    neighbors = Board.neighbors(0, 0)
    assert set(neighbors) == {(0, 1), (1, 0)}
