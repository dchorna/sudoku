from generator.wall_generator import compute_walls
from model.board import Board


def test_compute_walls_for_adjacent_cells():
    grid = [
        [1, 2, 3, 4, 5, 6, 7, 8, 9],
        [2, 3, 4, 5, 6, 7, 8, 9, 1],
        [3, 4, 5, 6, 7, 8, 9, 1, 2],
        [4, 5, 6, 7, 8, 9, 1, 2, 3],
        [5, 6, 7, 8, 9, 1, 2, 3, 4],
        [6, 7, 8, 9, 1, 2, 3, 4, 5],
        [7, 8, 9, 1, 2, 3, 4, 5, 6],
        [8, 9, 1, 2, 3, 4, 5, 6, 7],
        [9, 1, 2, 3, 4, 5, 6, 7, 8],
    ]

    walls = compute_walls(Board(grid))

    assert walls[((0, 0), (0, 1))] is True
    assert walls[((0, 1), (0, 2))] is True
    assert walls[((0, 0), (1, 0))] is True
    assert walls[((1, 0), (2, 0))] is True

    grid[0][1] = 5
    walls = compute_walls(Board(grid))
    assert walls[((0, 0), (0, 1))] is False
