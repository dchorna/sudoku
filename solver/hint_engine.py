from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from model.board import Board
from solver.solver import adjacent_wall_relation, candidate_values


@dataclass(frozen=True)
class Hint:
    technique: str
    cells: list[tuple[int, int]]
    action: dict
    explanation: str


class HintEngine:
    """Find the next logical Sudoku hint, from simplest to hardest."""

    _TECHNIQUE_ORDER = [
        "Naked Single",
        "Hidden Single",
        "Naked Pair",
        "Hidden Pair",
        "Naked Triple",
        "Pointing Pairs",
        "Wall Forced Value",
        "No-Wall Elimination",
        "Consecutive Pair",
        "Consecutive Chain",
    ]

    def __init__(
        self,
        board: Board | list[list[int]],
        walls: dict[tuple[tuple[int, int], tuple[int, int]], bool] | None = None,
    ):
        self.board = board.copy() if isinstance(board, Board) else Board(board)
        self.walls = dict(walls) if walls else None

    def get_hint(self) -> Hint | None:
        for technique_name in self._TECHNIQUE_ORDER:
            if technique_name in {"Wall Forced Value", "No-Wall Elimination", "Consecutive Pair", "Consecutive Chain"}:
                if self.walls is None:
                    continue
            hint = self._find_hint_by_name(technique_name)
            if hint is not None:
                return hint
        return None

    def solve_with_logic_only(self) -> set[str]:
        applied: set[str] = set()
        while True:
            changed = False
            for technique_name in self._TECHNIQUE_ORDER:
                if technique_name in applied:
                    continue
                if self.walls is None and technique_name in {"Wall Forced Value", "No-Wall Elimination", "Consecutive Pair", "Consecutive Chain"}:
                    continue
                hint = self._find_hint_by_name(technique_name)
                if hint is None:
                    continue
                applied.add(technique_name)
                changed = True
                if "place" in hint.action and len(hint.cells) == 1:
                    row, col = hint.cells[0]
                    self.board.set_value(row, col, hint.action["place"])
                break
            if not changed:
                break
        return applied

    def _find_hint_by_name(self, technique_name: str) -> Hint | None:
        if technique_name == "Naked Single":
            return self._naked_single()
        if technique_name == "Hidden Single":
            return self._hidden_single()
        if technique_name == "Naked Pair":
            return self._naked_pair()
        if technique_name == "Hidden Pair":
            return self._hidden_pair()
        if technique_name == "Naked Triple":
            return self._naked_triple()
        if technique_name == "Pointing Pairs":
            return self._pointing_pairs()
        if technique_name == "Wall Forced Value":
            return self._wall_forced_value()
        if technique_name == "No-Wall Elimination":
            return self._no_wall_elimination()
        if technique_name == "Consecutive Pair":
            return self._consecutive_pair()
        if technique_name == "Consecutive Chain":
            return self._consecutive_chain()
        return None

    def _cell_candidates(self, row: int, col: int) -> list[int]:
        candidates = candidate_values(self.board, row, col, self.walls)
        if candidates:
            return candidates
        return self._fallback_candidates(row, col)

    def _fallback_candidates(self, row: int, col: int) -> list[int]:
        row_missing = {value for value in range(1, 10) if all(self.board.get_value(row, c) != value for c in range(9))}
        col_missing = {value for value in range(1, 10) if all(self.board.get_value(r, col) != value for r in range(9))}
        box_row_start = (row // 3) * 3
        box_col_start = (col // 3) * 3
        box_missing = {
            value
            for value in range(1, 10)
            if all(self.board.get_value(r, c) != value for r in range(box_row_start, box_row_start + 3) for c in range(box_col_start, box_col_start + 3))
        }
        allowed = (row_missing | col_missing) - box_missing
        if not allowed:
            allowed = row_missing | col_missing
        return sorted(allowed)

    def _naked_single(self) -> Hint | None:
        for row in range(9):
            for col in range(9):
                if self.board.get_value(row, col) != 0:
                    continue
                candidates = self._cell_candidates(row, col)
                if len(candidates) == 1:
                    return Hint(
                        technique="Naked Single",
                        cells=[(row, col)],
                        action={"place": candidates[0]},
                        explanation=f"Cell ({row}, {col}) has only one candidate left: {candidates[0]}.",
                    )
        return None

    def _hidden_single(self) -> Hint | None:
        for unit_type in ("row", "col", "box"):
            for index in range(9):
                unit = self._unit_cells(unit_type, index)
                for value in range(1, 10):
                    if any(self.board.get_value(r, c) == value for r, c in unit):
                        continue
                    positions = [
                        cell
                        for cell in unit
                        if self.board.get_value(*cell) == 0 and value in self._cell_candidates(*cell)
                    ]
                    if len(positions) == 1:
                        cell = positions[0]
                        return Hint(
                            technique="Hidden Single",
                            cells=[cell],
                            action={"place": value},
                            explanation=(
                                f"Value {value} can only go in cell ({cell[0]}, {cell[1]}) of this {unit_type}."
                            ),
                        )
        return None

    def _naked_pair(self) -> Hint | None:
        for unit in self._all_units():
            empty_cells = [cell for cell in unit if self.board.get_value(*cell) == 0]
            for left, right in combinations(empty_cells, 2):
                left_candidates = self._cell_candidates(*left)
                right_candidates = self._cell_candidates(*right)
                if len(left_candidates) != 2 or left_candidates != right_candidates:
                    continue
                elimination: dict[tuple[int, int], list[int]] = {}
                for cell in empty_cells:
                    if cell in (left, right):
                        continue
                    candidates = self._cell_candidates(*cell)
                    common = sorted(set(candidates) & set(left_candidates))
                    if common:
                        elimination[cell] = common
                if elimination:
                    return Hint(
                        technique="Naked Pair",
                        cells=[left, right],
                        action={"eliminate": elimination},
                        explanation=(
                            f"Cells {left} and {right} are a naked pair with candidates {left_candidates}; "
                            "those values can be removed from other cells in the unit."
                        ),
                    )
        return None

    def _hidden_pair(self) -> Hint | None:
        for unit in self._all_units():
            empty = [cell for cell in unit if self.board.get_value(*cell) == 0]
            if len(empty) < 2:
                continue
            values = [v for v in range(1, 10) if any(v in candidate_values(self.board, *cell, self.walls) for cell in empty)]
            for combo in combinations(values, 2):
                positions = [cell for cell in empty if set(combo).issubset(set(self._cell_candidates(*cell)))]
                if len(positions) != 2:
                    continue
                elimination: dict[tuple[int, int], list[int]] = {}
                for cell in positions:
                    candidates = self._cell_candidates(*cell)
                    rest = sorted(set(candidates) - set(combo))
                    if rest:
                        elimination[cell] = rest
                if elimination:
                    return Hint(
                        technique="Hidden Pair",
                        cells=positions,
                        action={"eliminate": elimination},
                        explanation=(
                            f"Values {combo} are confined to cells {positions}; the other candidates in those cells are impossible."
                        ),
                    )
        return None

    def _naked_triple(self) -> Hint | None:
        for unit in self._all_units():
            empty = [cell for cell in unit if self.board.get_value(*cell) == 0]
            for triple in combinations(empty, 3):
                candidate_sets = [set(self._cell_candidates(*cell)) for cell in triple]
                union = sorted(set().union(*candidate_sets))
                if len(union) != 3:
                    continue
                elimination: dict[tuple[int, int], list[int]] = {}
                for cell in empty:
                    if cell in triple:
                        continue
                    candidates = set(self._cell_candidates(*cell))
                    to_remove = sorted(candidates & set(union))
                    if to_remove:
                        elimination[cell] = to_remove
                if elimination:
                    return Hint(
                        technique="Naked Triple",
                        cells=list(triple),
                        action={"eliminate": elimination},
                        explanation=(
                            f"These three cells {triple} have a naked triple across values {union}; those values can be removed from the rest of the unit."
                        ),
                    )
        return None

    def _pointing_pairs(self) -> Hint | None:
        for box_index in range(9):
            box = self._unit_cells("box", box_index)
            for value in range(1, 10):
                positions = [
                    cell for cell in box if self.board.get_value(*cell) == 0 and value in self._cell_candidates(*cell)
                ]
                if not positions:
                    continue
                row_positions = {row for row, _ in positions}
                if len(row_positions) == 1:
                    row = next(iter(row_positions))
                    eliminate = [
                        (row, col)
                        for col in range(9)
                        if self.board.get_value(row, col) == 0 and (row, col) not in box and value in self._cell_candidates(row, col)
                    ]
                    if eliminate:
                        return Hint(
                            technique="Pointing Pairs",
                            cells=sorted(positions),
                            action={"eliminate": {cell: [value] for cell in eliminate}},
                            explanation=(
                                f"Value {value} appears only in row {row} of this box, so it can be removed from the rest of that row."
                            ),
                        )
                col_positions = {col for _, col in positions}
                if len(col_positions) == 1:
                    col = next(iter(col_positions))
                    eliminate = [
                        (row, col)
                        for row in range(9)
                        if self.board.get_value(row, col) == 0 and (row, col) not in box and value in self._cell_candidates(row, col)
                    ]
                    if eliminate:
                        return Hint(
                            technique="Pointing Pairs",
                            cells=sorted(positions),
                            action={"eliminate": {cell: [value] for cell in eliminate}},
                            explanation=(
                                f"Value {value} appears only in column {col} of this box, so it can be removed from the rest of that column."
                            ),
                        )
        return None

    def _wall_forced_value(self) -> Hint | None:
        if self.walls is None:
            return None
        for row in range(9):
            for col in range(9):
                if self.board.get_value(row, col) != 0:
                    continue
                candidates = candidate_values(self.board, row, col, self.walls)
                for neighbor in Board.neighbors(row, col):
                    neighbor_value = self.board.get_value(*neighbor)
                    if neighbor_value == 0:
                        continue
                    if adjacent_wall_relation(self.walls, (row, col), neighbor) is not True:
                        continue
                    valid = {neighbor_value - 1, neighbor_value + 1}
                    valid = {v for v in valid if 1 <= v <= 9}
                    restricted = sorted(set(candidates) & valid)
                    if not restricted:
                        continue
                    if len(restricted) == 1 and restricted[0] in candidates:
                        return Hint(
                            technique="Wall Forced Value",
                            cells=[(row, col)],
                            action={"place": restricted[0]},
                            explanation=(
                                f"A wall connects ({row}, {col}) to a filled neighbor {neighbor_value}, leaving only {restricted[0]} as valid."
                            ),
                        )
                    if len(candidates) > len(restricted):
                        return Hint(
                            technique="Wall Forced Value",
                            cells=[(row, col)],
                            action={"eliminate": {(row, col): sorted(set(candidates) - set(restricted))}},
                            explanation=(
                                f"The wall to {neighbor_value} limits ({row}, {col}) to {restricted}; other candidates are impossible."
                            ),
                        )
        return None

    def _no_wall_elimination(self) -> Hint | None:
        if self.walls is None:
            return None
        for row in range(9):
            for col in range(9):
                if self.board.get_value(row, col) != 0:
                    continue
                candidates = candidate_values(self.board, row, col, self.walls)
                for neighbor in Board.neighbors(row, col):
                    neighbor_value = self.board.get_value(*neighbor)
                    if neighbor_value == 0:
                        continue
                    if adjacent_wall_relation(self.walls, (row, col), neighbor) is not False:
                        continue
                    forbidden = {neighbor_value - 1, neighbor_value + 1}
                    forbidden = {v for v in forbidden if 1 <= v <= 9}
                    to_remove = sorted(set(candidates) & forbidden)
                    if to_remove:
                        return Hint(
                            technique="No-Wall Elimination",
                            cells=[(row, col)],
                            action={"eliminate": {(row, col): to_remove}},
                            explanation=(
                                f"There is no wall between ({row}, {col}) and the filled neighbor {neighbor_value}, so values {to_remove} are impossible here."
                            ),
                        )
        return None

    def _consecutive_pair(self) -> Hint | None:
        if self.walls is None:
            return None
        for (a, b), relation in self.walls.items():
            if relation is not True:
                continue
            ar, ac = a
            br, bc = b
            if self.board.get_value(ar, ac) != 0 or self.board.get_value(br, bc) != 0:
                continue
            left_candidates = candidate_values(self.board, ar, ac, self.walls)
            right_candidates = candidate_values(self.board, br, bc, self.walls)
            valid_pairs = [
                (lv, rv)
                for lv in left_candidates
                for rv in right_candidates
                if abs(lv - rv) == 1
            ]
            if not valid_pairs:
                continue
            allowed_left = {lv for lv, _ in valid_pairs}
            allowed_right = {rv for _, rv in valid_pairs}
            elimination: dict[tuple[int, int], list[int]] = {}
            left_bad = sorted(set(left_candidates) - allowed_left)
            if left_bad:
                elimination[(ar, ac)] = left_bad
            right_bad = sorted(set(right_candidates) - allowed_right)
            if right_bad:
                elimination[(br, bc)] = right_bad
            if elimination:
                return Hint(
                    technique="Consecutive Pair",
                    cells=[a, b],
                    action={"eliminate": elimination},
                    explanation=(
                        f"Because the wall between {a} and {b} requires consecutive values, these candidates are impossible for the pair."
                    ),
                )
        return None

    def _consecutive_chain(self) -> Hint | None:
        if self.walls is None:
            return None
        for row in range(9):
            for start in range(0, 7):
                chain = [(row, c) for c in range(start, start + 3)]
                if not all(self.board.get_value(*cell) == 0 for cell in chain):
                    continue
                if not all(adjacent_wall_relation(self.walls, chain[i], chain[i + 1]) is True for i in range(2)):
                    continue
                candidates_by_cell = [candidate_values(self.board, *cell, self.walls) for cell in chain]
                valid_values = []
                for values0 in candidates_by_cell[0]:
                    for values1 in candidates_by_cell[1]:
                        if abs(values0 - values1) != 1:
                            continue
                        for values2 in candidates_by_cell[2]:
                            if abs(values1 - values2) == 1:
                                valid_values.append((values0, values1, values2))
                if not valid_values:
                    continue
                elimination: dict[tuple[int, int], list[int]] = {}
                for index, cell in enumerate(chain):
                    allowed = {seq[index] for seq in valid_values}
                    bad = sorted(set(candidate_values(self.board, *cell, self.walls)) - allowed)
                    if bad:
                        elimination[cell] = bad
                if elimination:
                    return Hint(
                        technique="Consecutive Chain",
                        cells=chain,
                        action={"eliminate": elimination},
                        explanation=(
                            f"The consecutive chain {chain} forces values that differ by 1; the rest are impossible in the chain."
                        ),
                    )
        for col in range(9):
            for start in range(0, 7):
                chain = [(r, col) for r in range(start, start + 3)]
                if not all(self.board.get_value(*cell) == 0 for cell in chain):
                    continue
                if not all(adjacent_wall_relation(self.walls, chain[i], chain[i + 1]) is True for i in range(2)):
                    continue
                candidates_by_cell = [candidate_values(self.board, *cell, self.walls) for cell in chain]
                valid_values = []
                for values0 in candidates_by_cell[0]:
                    for values1 in candidates_by_cell[1]:
                        if abs(values0 - values1) != 1:
                            continue
                        for values2 in candidates_by_cell[2]:
                            if abs(values1 - values2) == 1:
                                valid_values.append((values0, values1, values2))
                if not valid_values:
                    continue
                elimination: dict[tuple[int, int], list[int]] = {}
                for index, cell in enumerate(chain):
                    allowed = {seq[index] for seq in valid_values}
                    bad = sorted(set(candidate_values(self.board, *cell, self.walls)) - allowed)
                    if bad:
                        elimination[cell] = bad
                if elimination:
                    return Hint(
                        technique="Consecutive Chain",
                        cells=chain,
                        action={"eliminate": elimination},
                        explanation=(
                            f"The consecutive chain {chain} forces values that differ by 1; the rest are impossible in the chain."
                        ),
                    )
        return None

    def _all_units(self):
        units: list[list[tuple[int, int]]] = []
        for index in range(9):
            units.append(self._unit_cells("row", index))
            units.append(self._unit_cells("col", index))
            units.append(self._unit_cells("box", index))
        return units

    def _unit_cells(self, unit_type: str, index: int) -> list[tuple[int, int]]:
        if unit_type == "row":
            return [(index, col) for col in range(9)]
        if unit_type == "col":
            return [(row, index) for row in range(9)]
        if unit_type == "box":
            box_row = (index // 3) * 3
            box_col = (index % 3) * 3
            return [(r, c) for r in range(box_row, box_row + 3) for c in range(box_col, box_col + 3)]
        raise ValueError(f"Unsupported unit type: {unit_type}")
