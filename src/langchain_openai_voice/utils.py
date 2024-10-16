import asyncio
import json
from typing import AsyncIterator, TypeVar, Any, Dict

T = TypeVar("T")


async def amerge(**streams: AsyncIterator[T]) -> AsyncIterator[tuple[str, T]]:
    """Merge multiple streams into one stream."""
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
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        print(f"Error decoding JSON: {data}")
        return {}


def serialize_result(result: Any) -> str:
    try:
        return json.dumps(result)
    except TypeError:
        return str(result)
