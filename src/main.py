"""Punto de entrada.  Ejemplos:
    python -m src.main --mode console --random-agent       # sin cámara ni Stockfish
    python -m src.main --mode console --stockfish /usr/games/stockfish --elo 1500
    python -m src.main --mode camera  --stockfish /usr/games/stockfish
"""
from __future__ import annotations
import argparse
import asyncio
import threading
import chess
from .config import Config
from .engine.stockfish_agent import StockfishAgent, RandomAgent
from .game.controller import GameController
from .server.ws_server import Hub


def console_loop(controller: GameController):
    print("Escribe jugadas en UCI (e2e4), 'ok' para confirmar la jugada del agente, 'new' para reiniciar.")
    while True:
        try:
            line = input("> ").strip().lower()
        except EOFError:
            return
        if line == "ok":
            controller.confirm_agent_move()
        elif line == "new":
            controller.new_game()
        elif line:
            try:
                controller.human_move_uci(line)
            except ValueError:
                print("Formato inválido")


async def amain(args):
    cfg = Config(stockfish_path=args.stockfish, elo=args.elo, skill=args.skill,
                 camera_index=args.camera, human_is_white=not args.black)
    agent = RandomAgent() if args.random_agent else StockfishAgent(cfg.stockfish_path, cfg.elo, cfg.skill, cfg.think_time)
    hub = Hub()
    controller = GameController(agent, hub.emit, chess.WHITE if cfg.human_is_white else chess.BLACK)
    stop, force = threading.Event(), threading.Event()

    def on_message(msg: dict):
        cmd = msg.get("cmd")
        if cmd == "new_game":
            controller.new_game()
        elif cmd == "confirm":                 # botón "terminé mi jugada"
            force.set()
            controller.confirm_agent_move()
        elif cmd == "move" and "uci" in msg:   # para probar sin cámara desde la UI web
            controller.human_move_uci(msg["uci"])

    hub.on_message, hub.on_connect = on_message, controller.snapshot
    if args.mode == "camera":
        from .vision.capture import run_camera
        threading.Thread(target=run_camera, args=(controller, cfg, stop, force), daemon=True).start()
    else:
        threading.Thread(target=console_loop, args=(controller,), daemon=True).start()
    try:
        await hub.serve(cfg.ws_host, cfg.ws_port)
    finally:
        stop.set()
        agent.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["console", "camera"], default="console")
    p.add_argument("--stockfish", default="stockfish")
    p.add_argument("--elo", type=int, default=None)
    p.add_argument("--skill", type=int, default=None)
    p.add_argument("--camera", type=int, default=0)
    p.add_argument("--black", action="store_true", help="el humano juega con negras")
    p.add_argument("--random-agent", action="store_true")
    asyncio.run(amain(p.parse_args()))
