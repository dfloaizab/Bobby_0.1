"""Calibración geométrica: marcadores ArUco -> homografía -> vista cenital del tablero."""
from __future__ import annotations
import cv2
import numpy as np


def _detector(dict_name: str):
    dictionary = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, dict_name))
    return cv2.aruco.ArucoDetector(dictionary, cv2.aruco.DetectorParameters())


def find_homography(frame: np.ndarray, cfg) -> np.ndarray | None:
    """Calcula H (imagen -> vista cenital) con los 4 marcadores (ids 0..3). None si no se ven los cuatro."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = _detector(cfg.aruco_dict).detectMarkers(gray)
    if ids is None:
        return None
    centers = {int(i): c.reshape(4, 2).mean(axis=0) for i, c in zip(ids.flatten(), corners)}
    if not all(k in centers for k in range(4)):
        return None
    n = cfg.warp_px
    o = cfg.marker_offset_mm * n / cfg.board_mm
    dst = {0: (-o, -o), 1: (n + o, -o), 2: (n + o, n + o), 3: (-o, n + o)}
    src = np.float32([centers[i] for i in range(4)])
    dst_pts = np.float32([dst[i] for i in range(4)])
    H, _ = cv2.findHomography(src, dst_pts)
    return H


def warp_board(frame: np.ndarray, H: np.ndarray, size: int) -> np.ndarray:
    """Vista cenital del área de juego: a8 arriba-izquierda, h1 abajo-derecha (lado de las blancas)."""
    return cv2.warpPerspective(frame, H, (size, size))
