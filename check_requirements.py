import sys
import time

RANGES = { 
    ("classic", "easy"): (40, 45), ("classic", "medium"): (30, 35), ("classic", "hard"): (24, 28),
    ("consecutive", "easy"): (20, 25), ("consecutive", "medium"): (8, 14), ("consecutive", "hard"): (0, 6),
}
DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]


def normalize_walls(walls):
    """{((r,c),(r2,c2)): bool} -> {(r,c,r2,c2): bool} в обидва боки."""
    out = {}
    for (a, b), w in (walls or {}).items():
        a, b = tuple(a), tuple(b)
        out[(a[0], a[1], b[0], b[1])] = bool(w)
        out[(b[0], b[1], a[0], a[1])] = bool(w)
    return out


def pair_walls(walls):
    """Формат вашого проєкту (як у web/app.py): {((r,c),(r2,c2)): bool} в обидва боки."""
    if walls is None:
        return None
    out = {}
    for (a, b), w in walls.items():
        out[(tuple(a), tuple(b))] = w
        out[(tuple(b), tuple(a))] = w
    return out


def valid_full(grid):
    full = set(range(1, 10))
    for i in range(9):
        if set(grid[i]) != full or {grid[r][i] for r in range(9)} != full:
            return False
    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            if {grid[r][c] for r in range(br, br + 3) for c in range(bc, bc + 3)} != full:
                return False
    return True


def walls_match_solution(solution, walls):
    """Перегородка є <=> різниця рівно 1, для кожної пари сусідів (п. 6.3)."""
    bad = 0
    for r in range(9):
        for c in range(9):
            for dr, dc in ((0, 1), (1, 0)):
                nr, nc = r + dr, c + dc
                if nr < 9 and nc < 9:
                    expected = abs(solution[r][c] - solution[nr][nc]) == 1
                    if walls.get((r, c, nr, nc)) is not expected:
                        bad += 1
    return bad


def candidates(grid, r, c, walls):
    cand = set(range(1, 10))
    for i in range(9):
        cand.discard(grid[r][i]); cand.discard(grid[i][c])
    br, bc = r - r % 3, c - c % 3
    for rr in range(br, br + 3):
        for cc in range(bc, bc + 3):
            cand.discard(grid[rr][cc])
    if walls is not None:
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 9 and 0 <= nc < 9 and grid[nr][nc]:
                n = grid[nr][nc]
                near = {n - 1, n + 1}
                cand = (cand & near) if walls[(r, c, nr, nc)] else (cand - near)
    return cand


def count_solutions(grid, walls, limit=2):
    """Незалежний backtracking + MRV; зупиняється на limit розв'язках."""
    g = [row[:] for row in grid]

    def rec():
        best, best_c = None, None
        for r in range(9):
            for c in range(9):
                if g[r][c] == 0:
                    cs = candidates(g, r, c, walls)
                    if not cs:
                        return 0
                    if best is None or len(cs) < len(best_c):
                        best, best_c = (r, c), cs
                        if len(cs) == 1:
                            break
            if best_c is not None and len(best_c) == 1:
                break
        if best is None:
            return 1
        total = 0
        for v in best_c:
            g[best[0]][best[1]] = v
            total += rec()
            g[best[0]][best[1]] = 0
            if total >= limit:
                break
        return total

    return rec()


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    from generator.board_generator import generate_full_board
    from generator.difficulty import generate_puzzle
    from generator.wall_generator import compute_walls
    from solver.solver import solve_board
    from solver.hint_engine import HintEngine

    fails = 0
    print(f"Перевірка: {n} полів на кожну з 6 комбінацій\n")
    for (mode, level), (lo, hi) in RANGES.items():
        problems, gens, hint_times, givens_list = [], [], [], []
        print(f"... {mode} {level}", flush=True)
        for _ in range(n):
            t = time.perf_counter()
            solution = generate_full_board()
            puzzle = generate_puzzle(mode, level, solution)
            gens.append(time.perf_counter() - t)

            sol = [row[:] for row in solution.grid]
            pz = [row[:] for row in puzzle.grid]
            walls_raw = compute_walls(solution) if mode == "consecutive" else None
            walls = normalize_walls(walls_raw) if walls_raw is not None else None  # для незалежних перевірок
            project_walls = pair_walls(walls_raw)                                   # для solve_board / HintEngine

            if not valid_full(sol):
                problems.append("повне поле некоректне")
            if walls is not None:
                bad = walls_match_solution(sol, walls)
                if bad:
                    problems.append(f"перегородки не відповідають значенням ({bad} пар)")
            if any(pz[r][c] not in (0, sol[r][c]) for r in range(9) for c in range(9)):
                problems.append("головоломка містить цифри, яких немає в розв'язку")

            givens = sum(1 for row in pz for v in row if v)
            givens_list.append(givens)
            if not lo <= givens <= hi:
                problems.append(f"відкритих клітинок {givens}, очікується {lo}-{hi}")

            solutions = count_solutions(pz, walls)
            if solutions != 1:
                problems.append(f"розв'язків: {'2+' if solutions >= 2 else solutions} (має бути 1)")

            try:
                solved = solve_board(pz, project_walls)
                if not solved or solved.grid != sol:
                    problems.append("solve_board не повернув очікуваний розв'язок")
            except Exception as e:
                problems.append(f"solve_board впав: {e}")

            try:
                t = time.perf_counter()
                hint = HintEngine(pz, project_walls).get_hint()
                hint_times.append(time.perf_counter() - t)
                if hint is None:
                    problems.append("HintEngine не знайшов жодної підказки на початковому полі")
                elif not (hint.technique and hint.explanation):
                    problems.append("підказка без техніки/пояснення")
            except Exception as e:
                problems.append(f"HintEngine впав: {e}")

        ok = not problems
        fails += 0 if ok else 1
        print(f"[{'OK ' if ok else 'ПОМИЛКА'}] {mode:12s} {level:6s} | відкритих: {min(givens_list)}-{max(givens_list)} "
              f"(треба {lo}-{hi}) | генерація макс {max(gens):.2f}с | підказка макс {max(hint_times or [0]):.3f}с")
        for p in sorted(set(problems)):
            print(f"        - {p}")

    print("\nNFR-1: генерація має вкладатися в кілька секунд; NFR-2: підказка < 1 с.")
    print("Підсумок:", "усе гаразд" if not fails else f"проблем у {fails} з 6 комбінацій")


if __name__ == "__main__":
    main()