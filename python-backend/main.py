# -----------------------------
# backend/main.py (FastAPI server)
# -----------------------------

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./chat.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    sender_id = Column(String)
    receiver_id = Column(String)
    message = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections
active_connections: Dict[str, WebSocket] = {}

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    active_connections[user_id] = websocket
    print(f"User connected: {user_id}")

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Save to DB
            db = SessionLocal()
            msg = Message(
                id=str(datetime.utcnow().timestamp()) + user_id,
                sender_id=message_data["sender_id"],
                receiver_id=message_data["receiver_id"],
                message=message_data["message"]
            )
            db.add(msg)
            db.commit()

            # Send to receiver if connected
            receiver_ws = active_connections.get(message_data["receiver_id"])
            if receiver_ws:
                await receiver_ws.send_text(json.dumps({
                    "sender_id": msg.sender_id,
                    "receiver_id": msg.receiver_id,
                    "message": msg.message,
                    "timestamp": msg.timestamp.isoformat()
                }))
    except WebSocketDisconnect:
        print(f"User disconnected: {user_id}")
        if user_id in active_connections:
            del active_connections[user_id]

@app.get("/messages/{sender_id}/{receiver_id}", response_model=List[dict])
def get_messages(sender_id: str, receiver_id: str):
    db = SessionLocal()
    messages = db.query(Message).filter(
        ((Message.sender_id == sender_id) & (Message.receiver_id == receiver_id)) |
        ((Message.sender_id == receiver_id) & (Message.receiver_id == sender_id))
    ).order_by(Message.timestamp).all()

    return [
        {
            "sender_id": m.sender_id,
            "receiver_id": m.receiver_id,
            "message": m.message,
            "timestamp": m.timestamp.isoformat()
        } for m in messages
    ]