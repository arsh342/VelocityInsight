from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..core.config import settings
from ..data.loader import load_race_telemetry_wide
import asyncio

router = APIRouter(tags=["ws"])


@router.websocket("/ws/live/{track}/{race}")
async def ws_live(websocket: WebSocket, track: str, race: str):
    """Stream live telemetry data for any track/race combination."""
    await websocket.accept()
    
    try:
        df = load_race_telemetry_wide(settings.dataset_root, track=track, race=race)
    except Exception as e:
        await websocket.send_json({"error": str(e)})
        await websocket.close()
        return
    
    # Convert timestamp columns to ISO format strings for JSON serialization
    if 'timestamp' in df.columns:
        df['timestamp'] = df['timestamp'].astype(str)
    
    # Simple simulated stream by timestamp order
    try:
        for _, row in df.iterrows():
            # Convert row to dict and ensure all values are JSON serializable
            data = {}
            for key, value in row.items():
                if isinstance(value, (int, float, str, bool)) or value is None:
                    data[key] = value
                else:
                    data[key] = str(value)
            await websocket.send_json(data)
            await asyncio.sleep(0.05)  # ~20 Hz
    except WebSocketDisconnect:
        return
