# Function for managing WebSocket connection with the OpenAI real-time API

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
    """
    Establishes a WebSocket connection to the OpenAI real-time API.

    This async context manager creates a connection to the OpenAI API and yields
    functions for sending events and receiving a stream of events.

    Args:
        api_key (str): The API key for authenticating with OpenAI.
        model (str): The name of the OpenAI model to use.
        url (str): The URL for the OpenAI API.

    Yields:
        tuple[Callable[[Dict[str, Any] | str], Coroutine[Any, Any, None]], AsyncIterator[Dict[str, Any]]]:
            A tuple containing:
            - A function for sending events to the API.
            - An async iterator for receiving events from the API.

    Raises:
        websockets.exceptions.WebSocketException: If there's an error in establishing or maintaining the WebSocket connection.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "OpenAI-Beta": "realtime=v1",
    }

    url = f"{url or DEFAULT_URL}?model={model}"

    async with websockets.connect(url, extra_headers=headers) as websocket:

        async def send_event(event: Dict[str, Any] | str) -> None:
            """
            Sends an event to the OpenAI API.

            Args:
                event (Dict[str, Any] | str): The event to send, either as a dictionary or a JSON string.
            """
            formatted_event = json.dumps(event) if isinstance(event, dict) else event
            await websocket.send(formatted_event)

        async def event_stream() -> AsyncIterator[Dict[str, Any]]:
            """
            Creates an async iterator for receiving events from the OpenAI API.

            Yields:
                Dict[str, Any]: Parsed JSON events received from the API.
            """
            async for raw_event in websocket:
                yield parse_json_safely(raw_event)

        yield send_event, event_stream()
