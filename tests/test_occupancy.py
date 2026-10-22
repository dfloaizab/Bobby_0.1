import chess
import cv2
import numpy as np
from src.game.state import occupancy_from_board
from src.vision.occupancy import OccupancyDetector, square_slice

SIZE = 800


def render(board: chess.Board) -> np.ndarray:
    img = np.zeros((SIZE, SIZE, 3), np.uint8)
    cell = SIZE // 8
    for sq in chess.SQUARES:
        col, row = chess.square_file(sq), 7 - chess.square_rank(sq)
        light = (col + row) % 2 == 0
        img[row*cell:(row+1)*cell, col*cell:(col+1)*cell] = (170, 200, 220) if light else (60, 100, 150)
        p = board.piece_at(sq)
        if p:
            c = (235, 235, 235) if p.color == chess.WHITE else (25, 25, 25)
            cv2.circle(img, (col*cell + cell//2, row*cell + cell//2), cell//3, c, -1)
    return img


def test_detects_start_position():
    det = OccupancyDetector(size=SIZE)
    det.set_reference(render(chess.Board(None)))
    start = render(chess.Board())
    det.calibrate_colors(start)
    assert det.detect(start) == occupancy_from_board(chess.Board())


def test_detects_after_move():
    det = OccupancyDetector(size=SIZE)
    det.set_reference(render(chess.Board(None)))
    det.calibrate_colors(render(chess.Board()))
    b = chess.Board()
    b.push_uci("g1f3")
    assert det.detect(render(b)) == occupancy_from_board(b)
