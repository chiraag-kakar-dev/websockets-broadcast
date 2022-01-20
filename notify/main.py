from typing import List
from fastapi import FastAPI
from starlette.responses import HTMLResponse
from starlette.websockets import WebSocket, WebSocketDisconnect
app = FastAPI()
html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>Send Notification
    </h1>
        <span id="ws-id"></span>
        <ul id='messages'>
        </ul>
        <script>
        function connect(){
            user_id = Math.floor((Math.random() * 10) + 1);
            document.querySelector("#ws-id").textContent = user_id;
            var ws = new WebSocket("ws://localhost:8001/ws/" + user_id);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            ws.onclose = function(e) {
            console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
            setTimeout(function() {
            connect();
            }, 1000);
                };
                }
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
            connect()
        </script>
    </body>
</html>
"""
@app.get("/")
async def get():
    return HTMLResponse(html)
class Notifier:
    def __init__(self):
        self.connections: List[WebSocket] = []
        self.generator = self.get_notification_generator()
    async def get_notification_generator(self):
        while True:
            message = yield
            await self._notify(message)
    async def push(self, msg: str):
        await self.generator.asend(msg)
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)
    def remove(self, websocket: WebSocket):
        self.connections.remove(websocket)
    async def _notify(self, message: str):
        living_connections = []
        while len(self.connections) > 0:
            # Looping like this is necessary in case a disconnection is handled
            # during await websocket.send_text(message)
            if message:
                userid = message.split('_')[0]
            websocket = self.connections.pop()
            if websocket.path_params["user_id"] == userid:
                await websocket.send_text(message)
            living_connections.append(websocket)
        self.connections = living_connections
notifier = Notifier()
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id:str):
    await notifier.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data} for user id {user_id}" )
    except WebSocketDisconnect:
        notifier.remove(websocket)
@app.get("/push/{message}")
async def push_to_connected_websockets(message: str):
    await notifier.push(message)
@app.on_event("startup")
async def startup():
    # Prime the push notification generator
    await notifier.generator.asend(None)