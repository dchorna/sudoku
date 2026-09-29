from generator.board_generator import generate_full_board


def test_generate_full_board_returns_valid_complete_board():
    board = generate_full_board()

    assert board.is_complete() is True
    assert board.is_valid() is True
    assert len(board.grid) == 9
    assert all(len(row) == 9 for row in board.grid)
