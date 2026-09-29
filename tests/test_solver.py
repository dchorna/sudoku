from generator.board_generator import generate_full_board
from generator.wall_generator import compute_walls
from solver.solver import solve_board


def test_solve_board_without_walls_recovers_generated_solution():
    original = generate_full_board()
    solved = solve_board(original)
    assert solved == original


def test_solve_board_with_walls_recovers_generated_solution():
    original = generate_full_board()
    walls = compute_walls(original)
    empty = [[0 for _ in range(9)] for _ in range(9)]

    solved = solve_board(empty, walls=walls)
    assert solved is not None
    assert solved.is_complete() is True
    assert solved.is_valid() is True
    assert solved.is_valid_with_walls(walls) is True
