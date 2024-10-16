# Define utility functions used throughout the project

import asyncio
import json
from typing import AsyncIterator, TypeVar, Any, Dict

T = TypeVar("T")


async def amerge(**streams: AsyncIterator[T]) -> AsyncIterator[tuple[str, T]]:
    """
    Merges multiple asynchronous streams into a single stream.

    Args:
        **streams: Keyword arguments where each value is an AsyncIterator.

    Yields:
        tuple[str, T]: A tuple containing the stream key and the yielded value.

    Raises:
        Exception: If an error occurs in any of the input streams.
    """
    nexts: dict[asyncio.Task, str] = {
        asyncio.create_task(anext(stream)): key for key, stream in streams.items()
    }
    while nexts:
        done, _ = await asyncio.wait(nexts, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            key = nexts.pop(task)
            stream = streams[key]
            try:
                yield key, task.result()
                nexts[asyncio.create_task(anext(stream))] = key
            except StopAsyncIteration:
                pass
            except Exception as e:
                for task in nexts:
                    task.cancel()
                raise e


def parse_json_safely(data: str) -> Dict[str, Any]:
    """
    Safely parses a JSON string into a dictionary.

    Args:
        data (str): The JSON string to parse.

    Returns:
        Dict[str, Any]: The parsed JSON as a dictionary. Returns an empty dictionary if parsing fails.
    """
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        print(f"Error decoding JSON: {data}")
        return {}


def serialize_result(result: Any) -> str:
    """
    Serializes a result to a JSON string.

    Args:
        result (Any): The result to serialize.

    Returns:
        str: The serialized result as a JSON string. If serialization fails, returns the string representation of the result.
    """
    try:
        return json.dumps(result)
    except TypeError:
        return str(result)
