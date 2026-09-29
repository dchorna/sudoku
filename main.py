import argparse
import time

from generator.board_generator import generate_full_board
from generator.difficulty import generate_puzzle
from generator.wall_generator import compute_walls
from solver.solver import solve_board
from utils.renderer import render_board


def parse_args():
    parser = argparse.ArgumentParser(description="Sudoku generator and solver demo")
    parser.add_argument("--mode", choices=["classic", "consecutive"], default="consecutive")
    parser.add_argument("--level", choices=["easy", "medium", "hard"], default="medium")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    started = time.perf_counter()
    solution = generate_full_board()
    puzzle = generate_puzzle(args.mode, args.level, solution)
    elapsed = time.perf_counter() - started

    walls = compute_walls(solution) if args.mode == "consecutive" else None

    print(f"Mode: {args.mode} | Level: {args.level}")
    print(f"Generation time: {elapsed:.3f} seconds")
    print(f"Open cells: {sum(1 for row in puzzle.grid for value in row if value == 0)}")
    print("\nPuzzle:")
    print(render_board(puzzle, mode=args.mode, walls=walls))

    if args.mode == "consecutive":
        print("\nSolution (full board):")
        print(render_board(solution, mode=args.mode, walls=walls))
    else:
        print("\nSolution (full board):")
        print(render_board(solution, mode=args.mode))

    if args.mode == "consecutive":
        empty_board = [[0 for _ in range(9)] for _ in range(9)]
        solved = solve_board(empty_board, walls=walls)
        print("\nSolver check:")
        print("Recovered valid wall-consistent solution:", solved is not None and solved.is_valid_with_walls(walls))
