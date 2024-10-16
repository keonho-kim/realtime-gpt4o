import asyncio
import json
from typing import AsyncIterator

from langchain_core.tools import BaseTool
from pydantic import BaseModel, PrivateAttr


class VoiceToolExecutor(BaseModel):
    """
    Can accept function calls and emits function call outputs to a stream.
    """

    tools_by_name: dict[str, BaseTool]
    _trigger_future: asyncio.Future = PrivateAttr(default_factory=asyncio.Future)
    _lock: asyncio.Lock = PrivateAttr(default_factory=asyncio.Lock)

    async def _trigger_func(self) -> dict:  # returns a tool call
        return await self._trigger_future

    async def add_tool_call(self, tool_call: dict) -> None:
        # lock to avoid simultaneous tool calls racing and missing
        # _trigger_future being
        async with self._lock:
            if self._trigger_future.done():
                # TODO: handle simultaneous tool calls better
                raise ValueError("Tool call adding already in progress")

            self._trigger_future.set_result(tool_call)

    async def _create_tool_call_task(self, tool_call: dict) -> asyncio.Task[dict]:
        tool = self.tools_by_name.get(tool_call["name"])
        if tool is None:
            # immediately yield error, do not add task
            raise ValueError(
                f"tool {tool_call['name']} not found. "
                f"Must be one of {list(self.tools_by_name.keys())}"
            )

        # try to parse args
        try:
            args = json.loads(tool_call["arguments"])
        except json.JSONDecodeError:
            raise ValueError(
                f"failed to parse arguments `{tool_call['arguments']}`. Must be valid JSON."
            )

        async def run_tool() -> dict:
            result = await tool.ainvoke(args)
            try:
                result_str = json.dumps(result)
            except TypeError:
                # not json serializable, use str
                result_str = str(result)
            return {
                "type": "conversation.item.create",
                "item": {
                    "id": tool_call["call_id"],
                    "call_id": tool_call["call_id"],
                    "type": "function_call_output",
                    "output": result_str,
                },
            }

        task = asyncio.create_task(run_tool())
        return task

    async def output_iterator(self) -> AsyncIterator[dict]:  # yield events
        trigger_task = asyncio.create_task(self._trigger_func())
        tasks = set([trigger_task])
        while True:
            done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                tasks.remove(task)
                if task == trigger_task:
                    async with self._lock:
                        self._trigger_future = asyncio.Future()
                    trigger_task = asyncio.create_task(self._trigger_func())
                    tasks.add(trigger_task)
                    tool_call = task.result()
                    try:
                        new_task = await self._create_tool_call_task(tool_call)
                        tasks.add(new_task)
                    except ValueError as e:
                        yield {
                            "type": "conversation.item.create",
                            "item": {
                                "id": tool_call["call_id"],
                                "call_id": tool_call["call_id"],
                                "type": "function_call_output",
                                "output": (f"Error: {str(e)}"),
                            },
                        }
                else:
                    yield task.result()
