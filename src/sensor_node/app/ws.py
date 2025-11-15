# src/sensor_node/app/ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio, contextlib, logging
router = APIRouter()

logger = logging.getLogger(__name__)

async def _relay(bus, topic: str, websocket: WebSocket):
    q = bus.subscribe(topic)
    #while True:
    #    await websocket.send_json({"topic": topic, "payload": await q.get()})
    try:
        while True:
            payload = await q.get()
            await websocket.send_json({"topic": topic, "payload": payload})
    except WebSocketDisconnect as e:
        # client closed the connection; this is normal
        logger.info(
            "WebSocket client disconnected from topic=%s (code=%s)",
            topic,
            getattr(e, "code", None),
        )
    except asyncio.CancelledError:
        # app shutdown / task cancelled – let shutdown proceed cleanly
        logger.debug("Relay for topic=%s cancelled", topic)
        raise
    finally:
        # if your Bus has an unsubscribe method, use it to avoid leaks
        with contextlib.suppress(Exception):
            if hasattr(bus, "unsubscribe"):
                bus.unsubscribe(topic, q)
                

@router.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    bus = websocket.app.state.bus
    # Speed-only MVP: one relay
    await _relay(bus, "speed", websocket)
