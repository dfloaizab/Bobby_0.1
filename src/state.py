"""Lógica de tablero: ocupación esperada e inferencia de la jugada a partir de lo observado.

Idea clave: no hace falta reconocer cada pieza. Se compara la ocupación (vacía / blanca / negra)
de las 64 casillas con la que produciría cada jugada legal; casi siempre solo una coincide.
"""
from __future__ import annotations
import chess

Occupancy = dict  # square (0..63) -> None | chess.WHITE | chess.BLACK


def occupancy_from_board(board: chess.Board) -> Occupancy:
    out = {}
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        out[sq] = piece.color if piece else None
    return out


def mismatches(a: Occupancy, b: Occupancy) -> int:
    return sum(1 for sq in chess.SQUARES if a.get(sq) != b.get(sq))


def infer_move(board: chess.Board, observed: Occupancy, max_mismatch: int = 0) -> chess.Move | None:
    """Devuelve la jugada legal cuyo resultado coincide con `observed`, o None si no hay una única candidata.

    max_mismatch > 0 tolera casillas mal detectadas (ruido de visión). Las promociones se resuelven a dama.
    """
    scored: list[tuple[int, chess.Move]] = []
    for move in board.legal_moves:
        if move.promotion and move.promotion != chess.QUEEN:
            continue  # los cuatro tipos de promoción producen la misma ocupación
        board.push(move)
        score = mismatches(occupancy_from_board(board), observed)
        board.pop()
        scored.append((score, move))
    if not scored:
        return None
    scored.sort(key=lambda t: t[0])
    best = scored[0][0]
    if best > max_mismatch:
        return None
    winners = [m for s, m in scored if s == best]
    return winners[0] if len(winners) == 1 else None
