from model.board import Board
from solver.hint_engine import HintEngine


def test_naked_single_hint():
    board = Board([
        [5, 3, 4, 6, 7, 8, 9, 1, 2],
        [6, 7, 2, 1, 9, 5, 3, 4, 8],
        [1, 9, 8, 3, 4, 2, 5, 6, 7],
        [8, 5, 9, 7, 6, 1, 4, 2, 3],
        [4, 2, 6, 8, 5, 3, 7, 9, 1],
        [7, 1, 3, 9, 2, 4, 8, 5, 6],
        [9, 6, 1, 5, 3, 7, 2, 8, 4],
        [2, 8, 7, 4, 1, 9, 6, 0, 5],
        [3, 4, 5, 2, 8, 6, 1, 7, 9],
    ])
    hint = HintEngine(board).get_hint()
    assert hint is not None
    assert hint.technique == "Naked Single"
    assert hint.cells == [(7, 7)]
    assert hint.action["place"] == 3


def test_hidden_single_hint():
    board = Board([
        [5, 0, 0, 6, 7, 0, 0, 0, 0],
        [6, 7, 0, 0, 9, 5, 0, 0, 8],
        [0, 9, 8, 0, 0, 0, 5, 0, 7],
        [8, 0, 9, 0, 0, 0, 4, 0, 3],
        [4, 0, 6, 0, 0, 3, 7, 9, 1],
        [0, 1, 3, 0, 0, 4, 8, 0, 6],
        [9, 0, 1, 0, 3, 7, 0, 0, 0],
        [0, 8, 0, 0, 1, 0, 0, 0, 5],
        [0, 4, 5, 2, 0, 0, 1, 0, 9],
    ])
    hint = HintEngine(board).get_hint()
    assert hint is not None
    assert hint.technique == "Hidden Single"
    assert hint.cells == [(0, 5)]
    assert hint.action["place"] == 8


def test_naked_pair_hint():
    board = Board([
        [0, 0, 3, 4, 5, 6, 0, 8, 9],
        [2, 1, 4, 5, 6, 7, 8, 9, 3],
        [4, 5, 6, 7, 8, 9, 1, 2, 3],
        [3, 4, 5, 6, 7, 8, 9, 1, 2],
        [5, 6, 7, 8, 9, 1, 2, 3, 4],
        [6, 7, 8, 9, 1, 2, 3, 4, 5],
        [7, 8, 9, 1, 2, 3, 4, 5, 6],
        [8, 9, 1, 2, 3, 4, 5, 6, 7],
        [9, 2, 3, 4, 5, 6, 7, 1, 8],
    ])
    hint = HintEngine(board).get_hint()
    assert hint is not None
    assert hint.technique == "Naked Pair"
    assert set(hint.cells) == {(0, 0), (0, 1)}


def test_hidden_pair_hint():
    board = Board([
        [0, 0, 3, 4, 5, 6, 7, 8, 9],
        [2, 1, 4, 5, 6, 7, 8, 9, 3],
        [4, 5, 6, 7, 8, 9, 1, 2, 3],
        [3, 4, 5, 6, 7, 8, 9, 1, 2],
        [5, 6, 7, 8, 9, 1, 2, 3, 4],
        [6, 7, 8, 9, 1, 2, 3, 4, 5],
        [7, 8, 9, 1, 2, 3, 4, 5, 6],
        [8, 9, 1, 2, 3, 4, 5, 6, 7],
        [9, 2, 3, 4, 5, 6, 7, 1, 8],
    ])
    hint = HintEngine(board).get_hint()
    assert hint is not None
    assert hint.technique == "Hidden Pair"


def test_naked_triple_hint():
    board = Board([
        [0, 0, 0, 4, 5, 6, 7, 8, 9],
        [2, 1, 4, 5, 6, 7, 8, 9, 3],
        [4, 5, 6, 7, 8, 9, 1, 2, 3],
        [3, 4, 5, 6, 7, 8, 9, 1, 2],
        [5, 6, 7, 8, 9, 1, 2, 3, 4],
        [6, 7, 8, 9, 1, 2, 3, 4, 5],
        [7, 8, 9, 1, 2, 3, 4, 5, 6],
        [8, 9, 1, 2, 3, 4, 5, 6, 7],
        [9, 2, 3, 4, 5, 6, 7, 1, 8],
    ])
    hint = HintEngine(board).get_hint()
    assert hint is not None
    assert hint.technique == "Naked Triple"


def test_pointing_pairs_hint():
    board = Board([
        [0, 0, 0, 6, 7, 8, 9, 1, 2],
        [6, 7, 2, 1, 9, 5, 3, 4, 8],
        [1, 9, 8, 3, 4, 2, 5, 6, 7],
        [8, 5, 9, 7, 6, 1, 4, 2, 3],
        [4, 2, 6, 8, 5, 3, 7, 9, 1],
        [7, 1, 3, 9, 2, 4, 8, 5, 6],
        [9, 6, 1, 5, 3, 7, 2, 8, 4],
        [2, 8, 7, 4, 1, 9, 6, 3, 5],
        [3, 4, 5, 2, 8, 6, 1, 7, 9],
    ])
    hint = HintEngine(board).get_hint()
    assert hint is not None
    assert hint.technique == "Pointing Pairs"


def test_wall_forced_value_hint():
    board = Board([
        [5, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ])
    walls = {((0, 0), (0, 1)): True}
    hint = HintEngine(board, walls).get_hint()
    assert hint is not None
    assert hint.technique == "Wall Forced Value"


def test_no_wall_elimination_hint():
    board = Board([
        [5, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ])
    walls = {((0, 0), (0, 1)): False}
    hint = HintEngine(board, walls).get_hint()
    assert hint is not None
    assert hint.technique == "No-Wall Elimination"


def test_consecutive_pair_hint():
    board = Board([
        [5, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ])
    walls = {((0, 0), (0, 1)): True}
    hint = HintEngine(board, walls).get_hint()
    assert hint is not None
    assert hint.technique == "Consecutive Pair"


def test_consecutive_chain_hint():
    board = Board([
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ])
    walls = {
        ((0, 0), (0, 1)): True,
        ((0, 1), (0, 2)): True,
        ((0, 2), (0, 3)): True,
    }
    hint = HintEngine(board, walls).get_hint()
    assert hint is not None
    assert hint.technique == "Consecutive Chain"
