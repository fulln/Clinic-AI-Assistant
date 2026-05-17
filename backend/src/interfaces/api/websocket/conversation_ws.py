"""WebSocket handler for bidirectional conversation (human-in-the-loop tool approval)."""
import json
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
import os

from src.application.conversation_service import ConversationApplicationService


async def conversation_ws_endpoint(
    websocket: WebSocket,
    conversation_id: uuid.UUID,
    token: str,
    svc: ConversationApplicationService,
):
    # Authenticate via token query param (WebSocket can't set Authorization header)
    try:
        payload = jwt.decode(token, os.environ["JWT_SECRET_KEY"], algorithms=["HS256"])
        user_id = uuid.UUID(payload["sub"])
        user_role = payload.get("role", "staff")
    except (JWTError, KeyError, ValueError):
        await websocket.close(code=4001)
        return

    await websocket.accept()
    pending_tool_calls: dict[str, asyncio.Future] = {}

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "code": "invalid_json", "message": "Invalid JSON"}))
                continue

            msg_type = msg.get("type")

            if msg_type == "message":
                content = msg.get("content", "")
                agent_id_str = msg.get("agent_id")
                agent_id = uuid.UUID(agent_id_str) if agent_id_str else None

                message_id = str(uuid.uuid4())
                full_response = []

                try:
                    stream = await svc.stream_message(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        content=content,
                        agent_id=agent_id,
                        rag_enabled=None,
                        user_role=user_role,
                    )
                    # stream_message returns an SSE generator; adapt for WebSocket
                    async for sse_chunk in stream:
                        # Parse SSE and re-emit as WS JSON
                        if sse_chunk.startswith("event: token"):
                            data_line = [l for l in sse_chunk.split("\n") if l.startswith("data:")]
                            if data_line:
                                token_data = json.loads(data_line[0].replace("data: ", ""))
                                full_response.append(token_data.get("token", ""))
                                await websocket.send_text(json.dumps({"type": "token", "token": token_data.get("token", "")}))
                        elif sse_chunk.startswith("event: end"):
                            await websocket.send_text(json.dumps({"type": "end", "message_id": message_id}))
                        elif sse_chunk.startswith("event: error"):
                            data_line = [l for l in sse_chunk.split("\n") if l.startswith("data:")]
                            if data_line:
                                err_data = json.loads(data_line[0].replace("data: ", ""))
                                await websocket.send_text(json.dumps({"type": "error", **err_data}))
                except Exception as e:
                    await websocket.send_text(json.dumps({"type": "error", "code": "stream_error", "message": str(e)}))

            elif msg_type == "approve_tool":
                tool_call_id = msg.get("tool_call_id")
                if tool_call_id and tool_call_id in pending_tool_calls:
                    pending_tool_calls[tool_call_id].set_result(True)

            elif msg_type == "reject_tool":
                tool_call_id = msg.get("tool_call_id")
                if tool_call_id and tool_call_id in pending_tool_calls:
                    pending_tool_calls[tool_call_id].set_result(False)

    except WebSocketDisconnect:
        pass


import asyncio  # noqa: E402 — placed here to avoid circular import with jwt
