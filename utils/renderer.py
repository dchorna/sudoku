from __future__ import annotations

from model.board import Board


def _cell_text(value: int) -> str:
    return "." if value == 0 else str(value)


def _wall_between(board: Board, row: int, col: int, right: bool = True, down: bool = False, walls: dict[tuple[tuple[int, int], tuple[int, int]], bool] | None = None) -> bool:
    if walls is None:
        return False
    a = (row, col)
    b = (row, col + 1) if right else (row + 1, col)
    if (a, b) in walls:
        return walls[(a, b)]
    if (b, a) in walls:
        return walls[(b, a)]
    return False


def render_board(board: Board, mode: str = "classic", walls: dict[tuple[tuple[int, int], tuple[int, int]], bool] | None = None) -> str:
    if mode == "classic":
        rows: list[str] = []
        for row in range(9):
            cells = []
            for col in range(9):
                cells.append(_cell_text(board.get_value(row, col)))
            rows.append(" | ".join(cells))
            if row in (2, 5):
                rows.append("-" * 31)
        return "\n".join(rows)

    row_lines: list[str] = []
    for row in range(9):
        line = ""
        for col in range(9):
            line += f" {_cell_text(board.get_value(row, col)):>1} "
            if col < 8:
                line += "║" if _wall_between(board, row, col, right=True, walls=walls) else "│"
        row_lines.append(line)
        if row in (2, 5):
            row_lines.append("─" * (len(row_lines[-1]) + 4))
    return "\n".join(row_lines)
