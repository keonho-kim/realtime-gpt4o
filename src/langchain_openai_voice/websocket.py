import json
import websockets
from contextlib import asynccontextmanager
from typing import AsyncGenerator, AsyncIterator, Any, Callable, Coroutine, Dict
from .utils import parse_json_safely
from .constants import DEFAULT_URL


@asynccontextmanager
async def connect(
    *, api_key: str, model: str, url: str
) -> AsyncGenerator[
    tuple[
        Callable[[Dict[str, Any] | str], Coroutine[Any, Any, None]],
        AsyncIterator[Dict[str, Any]],
    ],
    None,
]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "OpenAI-Beta": "realtime=v1",
    }

    url = f"{url or DEFAULT_URL}?model={model}"

    async with websockets.connect(url, extra_headers=headers) as websocket:

        async def send_event(event: Dict[str, Any] | str) -> None:
            formatted_event = json.dumps(event) if isinstance(event, dict) else event
            await websocket.send(formatted_event)

        async def event_stream() -> AsyncIterator[Dict[str, Any]]:
            async for raw_event in websocket:
                yield parse_json_safely(raw_event)

        yield send_event, event_stream()
