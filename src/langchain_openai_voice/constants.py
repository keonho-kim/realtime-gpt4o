DEFAULT_MODEL = "gpt-4o-realtime-preview-2024-10-01"
DEFAULT_URL = "wss://api.openai.com/v1/realtime"

EVENTS_TO_IGNORE = {
    "response.function_call_arguments.delta",
    "rate_limits.updated",
    "response.audio_transcript.delta",
    "response.created",
    "response.content_part.added",
    "response.content_part.done",
    "conversation.item.created",
    "response.audio.done",
    "session.created",
    "session.updated",
    "response.done",
    "response.output_item.done",
}
