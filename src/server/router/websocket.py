from langchain_openai_voice import OpenAIVoiceReactAgent
from langchain_openai_voice.tools import TOOLS
from server.backend.utils import websocket_stream
from starlette.websockets import WebSocket


async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        initial_data = await websocket.receive_json()

        instructions = initial_data.get("instructions")
        if not instructions:
            print("Using default instructions")
            from langchain_openai_voice.prompt import INSTRUCTIONS

            instructions = INSTRUCTIONS
        else:
            print(f"Using custom instructions: {instructions}")

        browser_receive_stream = websocket_stream(websocket)

        agent = OpenAIVoiceReactAgent(
            model="gpt-4o-realtime-preview",
            tools=TOOLS,
            instructions=instructions,
        )

        await agent.aconnect(browser_receive_stream, websocket.send_text)

    except Exception as e:
        print(f"Error in websocket_endpoint: {str(e)}")
    finally:
        await websocket.close(code=1000)
