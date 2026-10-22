"""Bucle de captura: cámara -> vista cenital -> ocupación -> controlador (con detección de 'tablero quieto')."""
from __future__ import annotations
import time
from collections import deque
import cv2
import numpy as np
from .calibration import warp_board
from .occupancy import OccupancyDetector


def open_camera(cfg) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(cfg.camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.frame_height)
    return cap


def load_calibration(cfg) -> tuple[np.ndarray, OccupancyDetector]:
    data = np.load(cfg.calibration_file)
    det = OccupancyDetector(size=cfg.warp_px)
    det.ref = data["ref"]
    det.color_thresh = float(data["color_thresh"])
    return data["H"], det


def run_camera(controller, cfg, stop_event, force_event=None):
    """Evalúa el tablero solo cuando está estable (sin manos) o cuando llega la señal 'confirmar'."""
    H, det = load_calibration(cfg)
    cap = open_camera(cfg)
    history: deque = deque(maxlen=cfg.stable_frames)
    last_sent = None
    while not stop_event.is_set():
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.05)
            continue
        occ = tuple(sorted(det.detect(warp_board(frame, H, cfg.warp_px)).items()))
        history.append(occ)
        forced = bool(force_event and force_event.is_set())
        stable = len(history) == history.maxlen and all(h == history[0] for h in history)
        if (stable or forced) and occ != last_sent:
            controller.on_observation(dict(occ))
            last_sent = occ
        if forced:
            force_event.clear()
    cap.release()
