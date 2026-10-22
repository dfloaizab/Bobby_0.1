"""Controlador de partida: une observaciones (cámara/consola/UI), el estado y el agente.

Flujo físico: aprendiz mueve -> el "coach" inteligente responde -> se anuncia la jugada del coach (XR/pantalla/otra)
-> el aprendiz la ejecuta en el tablero real -> la cámara lo confirma -> turno del aprendiz.
"""
from __future__ import annotations
import threading
import chess
from .state import occupancy_from_board, infer_move


class GameController:
    def __init__(self, agent, emit, human_color: bool = chess.WHITE, max_mismatch: int = 0):
        self.agent, self.emit = agent, emit
        self.human_color, self.max_mismatch = human_color, max_mismatch
        self.board = chess.Board()
        self.pending: chess.Move | None = None   # jugada del agente a la espera de ser ejecutada físicamente
        self.last_eval: int | None = None        # centipeones, unidad de medida del motor UCE (Stockfish) para medir la jugada desde el punto de vista de las blancas
        self.last_move_uci: str | None = None
        self._lock = threading.RLock()

    # ---------- API pública ----------
    def snapshot(self) -> dict:
        return {
            "type": "state",
            "fen": self.board.fen(),
            "turn": "white" if self.board.turn else "black",
            "human_color": "white" if self.human_color else "black",
            "pending_agent_move": self.pending.uci() if self.pending else None,
            "last_move": self.last_move_uci,
            "eval_cp": self.last_eval,
            "game_over": self.board.is_game_over(),
        }

    def new_game(self):
        with self._lock:
            self.board.reset()
            self.pending, self.last_eval, self.last_move_uci = None, None, None
            self.emit({"type": "new_game"})
            if self.board.turn != self.human_color:
                self._agent_turn()
            self.emit(self.snapshot())

    def on_observation(self, observed: dict):
        """Punto de entrada desde visión: `observed` = ocupación de las 64 casillas."""
        with self._lock:
            if self.board.is_game_over():
                return
            if self.pending is not None:  # esperando que el aprendiz ejecute la jugada del agente
                after = self.board.copy(stack=False)
                after.push(self.pending)
                if observed == occupancy_from_board(after):
                    self._commit_agent_move()
                return
            if observed == occupancy_from_board(self.board):
                return  # sin cambios
            move = infer_move(self.board, observed, self.max_mismatch)
            if move is None:
                self.emit({"type": "unrecognized", "fen": self.board.fen()})
                return
            self._apply_human(move)

    # ---------- Atajos para consola / UI de depuración ----------
    def human_move_uci(self, uci: str):
        with self._lock:
            move = chess.Move.from_uci(uci)
            if move not in self.board.legal_moves:
                self.emit({"type": "illegal", "uci": uci})
                return
            tmp = self.board.copy(stack=False)
            tmp.push(move)
            self.on_observation(occupancy_from_board(tmp))

    def confirm_agent_move(self):
        with self._lock:
            if self.pending is None:
                return
            tmp = self.board.copy(stack=False)
            tmp.push(self.pending)
            self.on_observation(occupancy_from_board(tmp))

    # ---------- Internos ----------
    def _apply_human(self, move: chess.Move):
        san = self.board.san(move)
        self.board.push(move)
        self.last_move_uci = move.uci()
        self.emit({"type": "human_move", "uci": move.uci(), "san": san, "fen": self.board.fen()})
        if not self._check_game_over():
            self._agent_turn()
        self.emit(self.snapshot())

    def _agent_turn(self):
        move, ev = self.agent.play(self.board)
        self.pending, self.last_eval = move, ev
        self.emit({"type": "agent_move", "uci": move.uci(), "san": self.board.san(move), "eval_cp": ev})

    def _commit_agent_move(self):
        move, self.pending = self.pending, None
        self.board.push(move)
        self.last_move_uci = move.uci()
        self._check_game_over()
        self.emit(self.snapshot())

    def _check_game_over(self) -> bool:
        if self.board.is_game_over():
            outcome = self.board.outcome()
            self.emit({"type": "game_over", "result": self.board.result(),
                       "reason": outcome.termination.name if outcome else None})
            return True
        return False
