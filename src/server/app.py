import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route, WebSocketRoute, Mount
from starlette.staticfiles import StaticFiles

from server.router.websocket import websocket_endpoint
from server.router.instructions import get_instructions, update_instructions
from server.router.home import homepage

routes = [
    Route("/", homepage),
    WebSocketRoute("/ws", websocket_endpoint),
    Route("/api/instructions", get_instructions, methods=["GET"]),
    Route("/api/instructions", update_instructions, methods=["POST"]),
    Mount("/static", StaticFiles(directory="src/server/static"), name="static"),
]

app = Starlette(debug=True, routes=routes)

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=3000)
