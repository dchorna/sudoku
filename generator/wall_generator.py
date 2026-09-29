from model.board import Board


def compute_walls(board: Board | list[list[int]]) -> dict[tuple[tuple[int, int], tuple[int, int]], bool]:
    if not isinstance(board, Board):
        board = Board(board)

    walls: dict[tuple[tuple[int, int], tuple[int, int]], bool] = {}

    for row in range(9):
        for col in range(9):
            # Горизонтальні перегородки
            if col + 1 < 9:
                a = (row, col)
                b = (row, col + 1)
                is_wall = abs(board.get_value(*a) - board.get_value(*b)) == 1
                walls[(a, b)] = is_wall
                walls[(b, a)] = is_wall  # Додано зворотний напрямок

            # Вертикальні перегородки
            if row + 1 < 9:
                a = (row, col)
                b = (row + 1, col)
                is_wall = abs(board.get_value(*a) - board.get_value(*b)) == 1
                walls[(a, b)] = is_wall
                walls[(b, a)] = is_wall  # Додано зворотний напрямок

    return walls