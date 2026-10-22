"""Detección de ocupación y color por casilla sobre la vista cenital rectificada."""
""" (Del módulo de visión de la aplicación) """
from __future__ import annotations
import chess
import cv2
import numpy as np


def square_slice(sq: int, size: int, margin: float):
    cell = size // 8
    col, row = chess.square_file(sq), 7 - chess.square_rank(sq)
    m = int(cell * margin)
    return slice(row * cell + m, (row + 1) * cell - m), slice(col * cell + m, (col + 1) * cell - m)


class OccupancyDetector:
    def __init__(self, size: int = 800, diff_thresh: float = 18.0, margin: float = 0.25):
        self.size, self.diff_thresh, self.margin = size, diff_thresh, margin
        self.ref: np.ndarray | None = None      # tablero vacío (gris)
        self.color_thresh: float = 128.0        # brillo que separa blancas de negras

    @staticmethod
    def _gray(img: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)

    def set_reference(self, empty_warped: np.ndarray):
        self.ref = self._gray(empty_warped)

    def _stats(self, gray: np.ndarray, sq: int) -> tuple[float, float]:
        ys, xs = square_slice(sq, self.size, self.margin)
        diff = float(np.abs(gray[ys, xs] - self.ref[ys, xs]).mean())
        return diff, float(gray[ys, xs].mean())

    def calibrate_colors(self, start_warped: np.ndarray):
        """Con la posición inicial en el tablero: fija el umbral blanco/negro a partir de las 32 fichas."""
        gray = self._gray(start_warped)
        white = [self._stats(gray, sq)[1] for sq in chess.SQUARES if chess.square_rank(sq) <= 1]
        black = [self._stats(gray, sq)[1] for sq in chess.SQUARES if chess.square_rank(sq) >= 6]
        self.color_thresh = float((np.mean(white) + np.mean(black)) / 2)

    def detect(self, warped: np.ndarray) -> dict:
        assert self.ref is not None, "falta la referencia del tablero vacío"
        gray = self._gray(warped)
        out = {}
        for sq in chess.SQUARES:
            diff, mean = self._stats(gray, sq)
            out[sq] = None if diff < self.diff_thresh else (chess.WHITE if mean > self.color_thresh else chess.BLACK)
        return out
