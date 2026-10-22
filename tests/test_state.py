import chess
from src.game.state import occupancy_from_board, infer_move


def observe_after(board, uci):
    b = board.copy()
    b.push_uci(uci)
    return occupancy_from_board(b)


def test_simple_move():
    b = chess.Board()
    assert infer_move(b, observe_after(b, "e2e4")).uci() == "e2e4"


def test_capture():
    b = chess.Board()
    for m in ["e2e4", "d7d5"]:
        b.push_uci(m)
    assert infer_move(b, observe_after(b, "e4d5")).uci() == "e4d5"


def test_castling():
    b = chess.Board("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
    assert infer_move(b, observe_after(b, "e1g1")).uci() == "e1g1"
    assert infer_move(b, observe_after(b, "e1c1")).uci() == "e1c1"


def test_en_passant():
    b = chess.Board("8/8/8/3pP3/8/8/8/4K2k w - d6 0 1")
    assert infer_move(b, observe_after(b, "e5d6")).uci() == "e5d6"


def test_promotion_defaults_to_queen():
    b = chess.Board("8/P7/8/8/8/8/8/k1K5 w - - 0 1")
    assert infer_move(b, observe_after(b, "a7a8q")).uci() == "a7a8q"


def test_no_match_returns_none():
    b = chess.Board()
    obs = observe_after(b, "e2e4")
    obs[chess.A1] = None  # ruido grave
    assert infer_move(b, obs) is None
    assert infer_move(b, obs, max_mismatch=1).uci() == "e2e4"
