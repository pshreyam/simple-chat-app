from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

app = FastAPI()

# Connected WebSocket clients
connected_users = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws/{user_id}")
async def chat(user_id: str, websocket: WebSocket):
    """Endpoint for streaming chat data."""
    await websocket.accept()

    connected_users[user_id] = websocket

    logger.info(f"{user_id} connected. Active users: {len(connected_users)}")

    for user, user_ws in connected_users.items():
        if user != user_id:
            await user_ws.send_json(
                {
                    "data": f"{user_id} has joined the chat and can now see new messages in the chatroom.",
                    "message_type": "system_broadcast",
                }
            )

    try:
        while True:
            json_data = await websocket.receive_json()
            data = json_data["data"]
            logger.info(f"Received message from {user_id}: {data}")

            for user, user_ws in connected_users.items():
                await user_ws.send_json(
                    {
                        "data": data,
                        "user_id": user_id,
                        "current_user": user == user_id,
                        "message_type": "group_message",
                    }
                )
    except WebSocketDisconnect:
        logger.info(f"{user_id} disconnected.")

        del connected_users[user_id]

        for user, user_ws in connected_users.items():
            await user_ws.send_json(
                {
                    "data": f"{user_id} has left the chat and will no longer be able to see new messages in the chatroom.",
                    "message_type": "system_broadcast",
                }
            )
