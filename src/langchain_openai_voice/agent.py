# Core class implementing the OpenAI voice-based conversational agent

import asyncio
import json
from typing import AsyncIterator, Any, Callable, Coroutine, Dict, List

from langchain_core.tools import BaseTool
from langchain_core._api import beta
from langchain_core.utils import secret_from_env

from pydantic import BaseModel, Field, SecretStr

from .constants import DEFAULT_MODEL, DEFAULT_URL, EVENTS_TO_IGNORE
from .utils import amerge, parse_json_safely
from .tool_executor import VoiceToolExecutor
from .websocket import connect


@beta()
class OpenAIVoiceReactAgent(BaseModel):
    """
    A class representing an OpenAI voice-based conversational agent.

    This agent can connect to the OpenAI API, process voice input, execute tools,
    and generate voice responses.

    Attributes:
        model (str): The name of the OpenAI model to use.
        api_key (SecretStr): The API key for authenticating with OpenAI.
        instructions (str | None): Optional instructions for the agent.
        tools (List[BaseTool] | None): Optional list of tools the agent can use.
        url (str): The URL for the OpenAI API.
    """

    model: str = Field(default=DEFAULT_MODEL)
    api_key: SecretStr = Field(
        alias="openai_api_key",
        default_factory=secret_from_env("OPENAI_API_KEY", default=""),
    )
    instructions: str | None = None
    tools: List[BaseTool] | None = None
    url: str = Field(default=DEFAULT_URL)

    async def aconnect(
        self,
        input_stream: AsyncIterator[str],
        send_output_chunk: Callable[[str], Coroutine[Any, Any, None]],
    ) -> None:
        """
        Establishes a connection with the OpenAI API and processes the conversation.

        Args:
            input_stream (AsyncIterator[str]): An async iterator providing input data.
            send_output_chunk (Callable[[str], Coroutine[Any, Any, None]]): A coroutine
                function for sending output chunks.

        Returns:
            None
        """
        tools_by_name = {tool.name: tool for tool in self.tools or []}
        tool_executor = VoiceToolExecutor(tools_by_name=tools_by_name)

        async with connect(
            model=self.model, api_key=self.api_key.get_secret_value(), url=self.url
        ) as (model_send, model_receive_stream):
            tool_defs = [
                {
                    "type": "function",
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {"type": "object", "properties": tool.args},
                }
                for tool in tools_by_name.values()
            ]
            await model_send(
                {
                    "type": "session.update",
                    "session": {
                        "instructions": self.instructions,
                        "input_audio_transcription": {"model": "whisper-1"},
                        "tools": tool_defs,
                    },
                }
            )

            while True:
                async for stream_key, data_raw in amerge(
                    input_mic=input_stream,
                    output_speaker=model_receive_stream,
                    tool_outputs=tool_executor.output_iterator(),
                ):
                    data = (
                        parse_json_safely(data_raw)
                        if isinstance(data_raw, str)
                        else data_raw
                    )

                    if stream_key == "input_mic":
                        if data.get("type") == "start_listening":
                            await model_send({"type": "input_audio_buffer.start"})
                            print("Start listening for new input")
                        else:
                            await model_send(data)
                    elif stream_key == "tool_outputs":
                        print("Tool output:", data)
                        await model_send(data)
                        await model_send({"type": "response.create", "response": {}})
                    elif stream_key == "output_speaker":
                        await self._handle_output_speaker(
                            data, model_send, send_output_chunk, tool_executor
                        )

                    # 대화 종료 조건 확인 (필요한 경우)
                    if data.get("type") == "end_of_conversation":
                        return

    async def _handle_output_speaker(
        self,
        data: Dict[str, Any],
        model_send: Callable[[Dict[str, Any] | str], Coroutine[Any, Any, None]],
        send_output_chunk: Callable[[str], Coroutine[Any, Any, None]],
        tool_executor: VoiceToolExecutor,
    ) -> None:
        """
        Handles the output from the OpenAI model and processes various event types.

        Args:
            data (Dict[str, Any]): The data received from the model.
            model_send (Callable[[Dict[str, Any] | str], Coroutine[Any, Any, None]]):
                A coroutine function for sending data to the model.
            send_output_chunk (Callable[[str], Coroutine[Any, Any, None]]):
                A coroutine function for sending output chunks.
            tool_executor (VoiceToolExecutor): An instance of VoiceToolExecutor for
                executing tools.

        Returns:
            None
        """
        t = data["type"]
        if t == "response.audio.delta":
            await send_output_chunk(json.dumps(data))
        elif t == "response.audio_buffer.speech_started":
            print("Interrupt")
            await send_output_chunk(json.dumps(data))
        elif t == "error":
            print("Error:", data)
            await send_output_chunk(json.dumps({"type": "error", "message": str(data)}))
        elif t == "response.function_call_arguments.done":
            print("Tool call:", data)
            await tool_executor.add_tool_call(data)
        elif t == "response.audio_transcript.done":
            print("Model:", data["transcript"])
            await send_output_chunk(
                json.dumps(
                    {
                        "type": "transcript",
                        "transcript": data["transcript"],
                        "sender": "ai",
                    }
                )
            )
        elif t == "conversation.item.input_audio_transcription.completed":
            print("User:", data["transcript"])
            await send_output_chunk(
                json.dumps(
                    {
                        "type": "transcript",
                        "transcript": data["transcript"],
                        "sender": "user",
                    }
                )
            )
        elif t == "response.done":
            # AI의 응답이 끝났음을 알리는 메시지 추가
            await send_output_chunk(json.dumps({"type": "end_of_turn"}))
        elif t in [
            "input_audio_buffer.speech_started",
            "input_audio_buffer.speech_stopped",
            "input_audio_buffer.committed",
            "response.output_item.added",
        ]:
            # 이러한 이벤트들도 클라이언트에 전달
            await send_output_chunk(json.dumps({"type": t}))
        elif t not in EVENTS_TO_IGNORE:
            print("Unhandled event type:", t)
            # 처리되지 않은 이벤트 타입도 클라이언트에 전달
            await send_output_chunk(
                json.dumps({"type": "unhandled_event", "event_type": t})
            )
