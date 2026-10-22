"""Hub WebSocket: difunde eventos del juego a los clientes (XR, UI 2D, registro) y recibe comandos."""
from __future__ import annotations
import asyncio
import json
import websockets


class Hub:
    def __init__(self):
        self.clients: set = set()
        self.loop: asyncio.AbstractEventLoop | None = None
        self.on_message = None   # callable(dict)  -> se ejecuta en un hilo
        self.on_connect = None   # callable() -> dict con el estado inicial

    async def _handler(self, ws):
        self.clients.add(ws)
        try:
            if self.on_connect:
                await ws.send(json.dumps(self.on_connect()))
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if self.on_message:
                    await asyncio.to_thread(self.on_message, msg)
        finally:
            self.clients.discard(ws)

    def emit(self, msg: dict):
        """Seguro para llamar desde cualquier hilo."""
        print("[evento]", msg)
        if self.loop is not None:
            asyncio.run_coroutine_threadsafe(self._broadcast(msg), self.loop)

    async def _broadcast(self, msg: dict):
        websockets.broadcast(self.clients, json.dumps(msg))

    async def serve(self, host: str, port: int):
        self.loop = asyncio.get_running_loop()
        async with websockets.serve(self._handler, host, port):
            print(f"[ws] escuchando en ws://{host}:{port}")
            await asyncio.Future()
