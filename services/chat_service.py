from __future__ import annotations
from typing import Dict, Set
from fastapi import WebSocket


class ChatConnectionManager:
    """In-memory WebSocket connection manager.

    For production, swap to Redis pub/sub or a message broker.
    """

    def __init__(self) -> None:
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, thread_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.setdefault(thread_id, set()).add(websocket)

    def disconnect(self, thread_id: int, websocket: WebSocket) -> None:
        if thread_id in self.active_connections:
            self.active_connections[thread_id].discard(websocket)
            if not self.active_connections[thread_id]:
                self.active_connections.pop(thread_id, None)

    async def broadcast(self, thread_id: int, message: dict) -> None:
        for connection in self.active_connections.get(thread_id, set()):
            await connection.send_json(message)


manager = ChatConnectionManager()
