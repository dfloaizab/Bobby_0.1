"""Agentes de juego: Stockfish por UCI y un agente aleatorio para desarrollar sin el binario."""
""" (Debe instalarse o actualizarse el  módulo chess previamente: pip install chess """
from __future__ import annotations
import random
import chess
import chess.engine


class StockfishAgent:
    def __init__(self, path: str = "stockfish", elo: int | None = None,
                 skill: int | None = None, think_time: float = 0.5):
        self.engine = chess.engine.SimpleEngine.popen_uci(path)
        self.think_time = think_time
        opts = {}
        if elo is not None:
            opts.update({"UCI_LimitStrength": True, "UCI_Elo": elo})
        if skill is not None:
            opts["Skill Level"] = skill
        self.engine.configure({k: v for k, v in opts.items() if k in self.engine.options})

    def play(self, board: chess.Board) -> tuple[chess.Move, int | None]:
        res = self.engine.play(board, chess.engine.Limit(time=self.think_time), info=chess.engine.INFO_SCORE)
        score = res.info.get("score")
        cp = score.white().score(mate_score=10000) if score else None
        return res.move, cp

    def close(self):
        self.engine.quit()


class RandomAgent:
    """Para probar el flujo completo sin instalar Stockfish."""
    def play(self, board: chess.Board) -> tuple[chess.Move, int | None]:
        return random.choice(list(board.legal_moves)), None

    def close(self):
        pass
