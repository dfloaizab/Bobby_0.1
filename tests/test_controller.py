import chess
from src.engine.stockfish_agent import RandomAgent
from src.game.controller import GameController
from src.game.state import occupancy_from_board


def test_full_cycle_with_physical_confirmation():
    events = []
    c = GameController(RandomAgent(), events.append)
    c.human_move_uci("e2e4")
    assert c.pending is not None                       # el agente respondió, falta ejecutarla
    types = [e["type"] for e in events]
    assert "human_move" in types and "agent_move" in types
    before = c.board.fen()
    c.on_observation(occupancy_from_board(c.board))    # tablero sin cambios -> sigue pendiente
    assert c.pending is not None and c.board.fen() == before
    c.confirm_agent_move()
    assert c.pending is None and c.board.turn == chess.WHITE
