from generator.board_generator import generate_full_board
from generator.difficulty import LEVEL_RANGES, generate_puzzle
from generator.wall_generator import compute_walls
from solver.uniqueness_check import count_solutions


def test_generate_puzzle_for_all_levels_and_modes():
    for mode in ["classic", "consecutive"]:
        for level in ["easy", "medium", "hard"]:
            solution = generate_full_board()
            puzzle = generate_puzzle(mode, level, solution)
            open_cells = sum(1 for row in puzzle.grid for value in row if value == 0)
            min_open, max_open = LEVEL_RANGES[mode][level]
            assert min_open <= open_cells <= max_open, (mode, level, open_cells)

            walls = compute_walls(solution) if mode == "consecutive" else None
            assert count_solutions(puzzle, walls, limit=2) == 1, (mode, level)
