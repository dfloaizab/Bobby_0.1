"""Configuración central del proyecto"""
from dataclasses import dataclass


@dataclass
class Config:
    # --- Cámara / calibración ---
    camera_index: int = 0
    frame_width: int = 1920
    frame_height: int = 1080
    aruco_dict: str = "DICT_4X4_50"
    # Marcadores ArUco ids 0..3 alrededor del tablero, vistos desde el lado de las blancas:
    #   0 = esquina superior izquierda (cerca de a8)   1 = superior derecha (h8)
    #   3 = inferior izquierda (a1)                    2 = inferior derecha (h1)
    board_mm: float = 400.0          # lado del área de juego (64 casillas), en mm
    marker_offset_mm: float = 25.0   # distancia del CENTRO de cada marcador a la esquina del área de juego,
                                     # medida hacia afuera en x e y (diagonal)
    warp_px: int = 800               # tamaño de la vista cenital rectificada (800 px -> 100 px por casilla)
    calibration_file: str = "calibration.npz"

    # --- Detección de jugada ---
    stable_frames: int = 8           # fotogramas consecutivos iguales para dar la jugada por válida
    # --- Motor ---
    stockfish_path: str = "stockfish"
    elo: int | None = None           # None = fuerza máxima; mínimo 1320 en Stockfish
    skill: int | None = None         # 0-20 alternativo a elo
    think_time: float = 0.5
    human_is_white: bool = True
    # --- Servidor ---
    ws_host: str = "0.0.0.0"
    ws_port: int = 8765
