import random
from typing import Literal

from generator.board_generator import generate_full_board
from generator.wall_generator import compute_walls
from model.board import Board
from solver.uniqueness_check import has_unique_solution

# Розраховано на те, що ти імпортуєш HintEngine з відповідного модуля
# from solver.hint_engine import HintEngine

Mode = Literal["classic", "consecutive"]
Level = Literal["easy", "medium", "hard"]

# Залишаємо твої ліміти клітинок
LEVEL_RANGES: dict[Mode, dict[Level, tuple[int, int]]] = {
    "classic": {
        "easy": (40, 45),
        "medium": (30, 35),
        "hard": (24, 28),
    },
    "consecutive": {
        "easy": (20, 25),
        "medium": (8, 14),
        "hard": (0, 6),
    },
}

# Додаємо заборонені техніки для кожного рівня згідно з ТЗ
FORBIDDEN_TECHNIQUES: dict[Mode, dict[Level, set[str]]] = {
    "classic": {
        "easy": {"Naked Pair", "Hidden Pair", "Naked Triple", "Hidden Triple", "Pointing Pairs"},
        "medium": {"Naked Triple", "Hidden Triple"},
        "hard": set(), # На складному дозволено всі класичні логічні техніки
    },
    "consecutive": {
        "easy": {"Consecutive Pair", "Consecutive Chain"},
        "medium": {"Consecutive Chain"},
        "hard": set(), # Дозволено всі логічні техніки
    }
}


def _count_open_cells(board: Board) -> int:
    return sum(1 for row in board.grid for value in row if value != 0)

def _check_techniques_allowed(mode: Mode, level: Level, used_techniques: set[str]) -> bool:
    """Перевіряє, чи не використовувались заборонені для цього рівня техніки."""
    forbidden = FORBIDDEN_TECHNIQUES[mode][level]
    # Якщо є перетин використаних технік із забороненими — повертаємо False
    if used_techniques.intersection(forbidden):
        return False
    return True


def generate_puzzle(mode: Mode, level: Level, full_board: Board | None = None) -> Board:
    if mode not in LEVEL_RANGES or level not in LEVEL_RANGES[mode]:
        raise ValueError(f"Unsupported mode/level combination: {mode}/{level}")

    solution = full_board.copy() if full_board is not None else generate_full_board()
    puzzle = solution.copy()
    target_min, target_max = LEVEL_RANGES[mode][level]

    cells = [(row, col) for row in range(9) for col in range(9)]
    random.shuffle(cells)

    for row, col in cells:
        previous = puzzle.get_value(row, col)
        if previous == 0:
            continue

        # 1. Видаляємо клітинку
        puzzle.set_value(row, col, 0)
        walls = compute_walls(solution) if mode == "consecutive" else None
        
        # 2. Перевіряємо унікальність розв'язку
        if not has_unique_solution(puzzle, walls):
            puzzle.set_value(row, col, previous)
            continue
            
        # 3. Перевіряємо складність технік через HintEngine (Згідно з ТЗ)
        # TODO: Розкоментуй цей блок, коли HintEngine буде готовий
        # hint_engine = HintEngine(puzzle, walls)
        # is_solvable_logically, used_techniques = hint_engine.solve_logical()
        
        # Тимчасова заглушка для тестування (поки HintEngine не підключений):
        is_solvable_logically = True 
        used_techniques = set() 

        # Якщо головоломку не можна розв'язати логічно без вгадування,
        # або довелось застосувати надто складну техніку — відкочуємо видалення
        if not is_solvable_logically or not _check_techniques_allowed(mode, level, used_techniques):
            puzzle.set_value(row, col, previous)
            continue

        # 4. Перевіряємо, чи входимо ми в потрібний діапазон кількості порожніх клітинок
        open_cells = _count_open_cells(puzzle)
        if target_min <= open_cells <= target_max:
            return puzzle

    # Якщо не вийшло досягти діапазону (алгоритм обійшов усі клітинки),
    # повертаємо найкращий валідний варіант
    return puzzle