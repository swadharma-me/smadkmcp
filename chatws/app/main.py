from fastapi import FastAPI, HTTPException, Depends, Request, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware # Add this import
from fastapi.responses import PlainTextResponse
import httpx
import requests  # needed for ADK session calls
import json
from datetime import datetime, timezone
from pydantic import BaseModel
import uvicorn
from app.firebase import initialize_firebase, auth_with_firebase
import firebase_admin
from openai import OpenAI
import logging
import os
import asyncio
from typing import Optional
from app.config import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("dharma_chat")

GOOGLE_ADK_API_URL = config.GOOGLE_ADK_API_URL

SESSION_URL = f"{GOOGLE_ADK_API_URL}/apps/google_agent/users/"



app = FastAPI()

# Initialize Firebase on startup
logger.info("[DHARMA_CHAT] 🚀 STARTING DHARMA CHAT SERVER")
logger.info("[DHARMA_CHAT] Initializing Firebase...")
initialize_firebase()
logger.info("[DHARMA_CHAT] ✅ Firebase initialized successfully")
    
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


class User(BaseModel):
  apikey: str
  name: str
  userID: str 
  website: str
    
    
@app.websocket("/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    logger.info(f"[DHARMA_CHAT] ========== NEW WEBSOCKET CONNECTION ==========")
    logger.info(f"[DHARMA_CHAT] Session ID: {session_id}")
    
    origin = websocket.headers.get("origin")
    id_token = websocket.headers.get("Authorization", "")
    
    logger.info(f"[DHARMA_CHAT] Origin: {origin}")
    logger.info(f"[DHARMA_CHAT] Raw Authorization header: {id_token[:50]}..." if id_token else "[DHARMA_CHAT] No Authorization header found")
    
    if not id_token.startswith("Bearer "):
        logger.error(f"[DHARMA_CHAT] AUTHENTICATION FAILED - Missing or invalid Authorization header")
        await websocket.close(code=1008)
        return
    
    id_token = id_token.replace("Bearer ", "")
    logger.info(f"[DHARMA_CHAT] Extracted token: {id_token[:50]}...")
    
    try:
        firebase_user_id = await auth_with_firebase(id_token)
        logger.info(f"[DHARMA_CHAT] ✅ AUTHENTICATION SUCCESS - Firebase user: {firebase_user_id}")
    except Exception as e:
        logger.error(f"[DHARMA_CHAT] ❌ AUTHENTICATION FAILED - Firebase token invalid: {e}")
        await websocket.close(code=1008)
        return

    logger.info(f"[DHARMA_CHAT] 🎯 SCREEN LAUNCHED - Authenticated user: {firebase_user_id}, session_id={session_id}")
    await websocket.accept()
    logger.info(f"[DHARMA_CHAT] WebSocket connection accepted for user: {firebase_user_id}")

    try:
        logger.info(f"[DHARMA_CHAT] 👂 LISTENING FOR MESSAGES from user: {firebase_user_id}")
        while True:
            data = await websocket.receive_text()
            logger.info(f"[DHARMA_CHAT] 📝 MESSAGE TYPED by {firebase_user_id}: '{data}'")
            logger.info(f"[DHARMA_CHAT] Message length: {len(data)} characters")
            logger.info(f"[DHARMA_CHAT] Timestamp: {datetime.now(timezone.utc).isoformat()}")

            logger.info(f"[DHARMA_CHAT] 🔄 SENDING STATUS: working")
            await websocket.send_text(json.dumps({"type": "status", "status": "working"}))

            # Use Firebase user ID in session
            session_url = f"{GOOGLE_ADK_API_URL}/apps/google_agent/users/{firebase_user_id}/sessions/{session_id}"
            logger.info(f"[DHARMA_CHAT] 🔗 SESSION URL: {session_url}")
            
            session_resp = requests.get(session_url)
            logger.info(f"[DHARMA_CHAT] Session check response: {session_resp.status_code}")
            
            if session_resp.status_code != 200:
                logger.info(f"[DHARMA_CHAT] 🆕 CREATING NEW SESSION for {firebase_user_id}")
                create_resp = requests.post(session_url, headers={"Content-Type": "application/json"}, data='{}')
                logger.info(f"[DHARMA_CHAT] Session creation response: {create_resp.status_code}")
            else:
                logger.info(f"[DHARMA_CHAT] ✅ SESSION EXISTS for {firebase_user_id}")

            payload = {
                "appName": "google_agent",
                "userId": firebase_user_id,
                "sessionId": session_id,
                "newMessage": {
                    "role": "user",
                    "parts": [{"text": data}]
                }
            }
            
            logger.info(f"[DHARMA_CHAT] 📤 SENDING TO ADK:")
            logger.info(f"[DHARMA_CHAT] Payload: {json.dumps(payload, indent=2)}")
            logger.info(f"[DHARMA_CHAT] ADK URL: {GOOGLE_ADK_API_URL}/run")

            adk_start_time = datetime.now(timezone.utc)
            response = requests.post(
                f"{GOOGLE_ADK_API_URL}/run",
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload)
            )
            adk_end_time = datetime.now(timezone.utc)
            adk_duration = (adk_end_time - adk_start_time).total_seconds()

            logger.info(f"[DHARMA_CHAT] 📥 ADK RESPONSE:")
            logger.info(f"[DHARMA_CHAT] Status Code: {response.status_code}")
            logger.info(f"[DHARMA_CHAT] Response Time: {adk_duration:.2f} seconds")
            logger.info(f"[DHARMA_CHAT] Response Headers: {dict(response.headers)}")

            if response.status_code == 200:
                result = response.json()
                logger.info(f"[DHARMA_CHAT] Raw ADK Result (first 500 chars): {str(result)[:500]}...")
                
                reply = extract_best_reply(result)
                logger.info(f"[DHARMA_CHAT] 🎯 EXTRACTED REPLY:")
                logger.info(f"[DHARMA_CHAT] Reply length: {len(reply)} characters")
                logger.info(f"[DHARMA_CHAT] Reply content: {reply[:200]}..." if len(reply) > 200 else f"[DHARMA_CHAT] Reply content: {reply}")
                
                response_message = {"type": "message", "message": reply}
                logger.info(f"[DHARMA_CHAT] 📤 SENDING RESPONSE TO CLIENT: {json.dumps(response_message)[:200]}...")
                await websocket.send_text(json.dumps(response_message))
                logger.info(f"[DHARMA_CHAT] ✅ RESPONSE SENT successfully to {firebase_user_id}")
            else:
                logger.error(f"[DHARMA_CHAT] ❌ ADK ERROR:")
                logger.error(f"[DHARMA_CHAT] Status: {response.status_code}")
                logger.error(f"[DHARMA_CHAT] Error text: {response.text}")
                error_message = {"type": "error", "message": response.text}
                await websocket.send_text(json.dumps(error_message))
                logger.info(f"[DHARMA_CHAT] 📤 ERROR SENT to client")
    except WebSocketDisconnect:
        logger.info(f"[DHARMA_CHAT] 🔌 CLIENT DISCONNECTED - User: {firebase_user_id}")
    except Exception as e:
        logger.exception(f"[DHARMA_CHAT] ❌ EXCEPTION OCCURRED:")
        logger.exception(f"[DHARMA_CHAT] Exception details: {e}")
    finally:
        logger.info(f"[DHARMA_CHAT] ========== WEBSOCKET SESSION ENDED for {firebase_user_id} ==========")

def extract_best_reply(result):
    """Extract reply from ADK response event stream."""
    logger.info(f"[DHARMA_CHAT] 🔍 EXTRACTING REPLY from ADK result")
    logger.info(f"[DHARMA_CHAT] Result type: {type(result)}")
    
    if isinstance(result, list):
        logger.info(f"[DHARMA_CHAT] Processing {len(result)} events in result list")
        for i, event in enumerate(reversed(result)):
            logger.info(f"[DHARMA_CHAT] Processing event {i}: {str(event)[:100]}...")
            parts = event.get("content", {}).get("parts", [])
            logger.info(f"[DHARMA_CHAT] Event has {len(parts)} parts")
            
            for j, part in enumerate(parts):
                logger.info(f"[DHARMA_CHAT] Processing part {j}: {list(part.keys())}")
                if "text" in part:
                    reply_text = part["text"]
                    logger.info(f"[DHARMA_CHAT] ✅ FOUND TEXT REPLY: {reply_text[:100]}...")
                    return reply_text
                if "functionResponse" in part:
                    logger.info(f"[DHARMA_CHAT] Found function response, extracting...")
                    resp = part["functionResponse"].get("response", {}).get("result", {}).get("content", [])
                    for k, c in enumerate(resp):
                        logger.info(f"[DHARMA_CHAT] Function response content {k}: {c}")
                        if c.get("type") == "text":
                            reply_text = c["text"]
                            logger.info(f"[DHARMA_CHAT] ✅ FOUND FUNCTION TEXT REPLY: {reply_text[:100]}...")
                            return reply_text
    else:
        logger.info(f"[DHARMA_CHAT] Result is not a list: {str(result)[:200]}...")
    
    logger.warning(f"[DHARMA_CHAT] ⚠️ NO REPLY FOUND in ADK result")
    return "[No reply found]"

@app.get("/healthcheck")
async def healthcheck():
    """
    Health check endpoint to verify if the API is running.
    """
    current_time = datetime.now(timezone.utc)
    result = {
        "status": "ok",
        "timestamp": current_time.isoformat(),
        "message": "Dharma Chat API is running",
        "adk_url": GOOGLE_ADK_API_URL,
        "openai_model": OPENAI_WSCHAT_MODEL
    }
    logger.info(f"[DHARMA_CHAT] 🏥 HEALTH CHECK at {current_time.isoformat()}")
    logger.info(f"[DHARMA_CHAT] Health check result: {result}")
    return result

if __name__ == "__main__":
    logger.info("[DHARMA_CHAT] 🌟 STARTING UVICORN SERVER")
    logger.info(f"[DHARMA_CHAT] Host: 0.0.0.0, Port: 9000")
    logger.info(f"[DHARMA_CHAT] ADK URL: {GOOGLE_ADK_API_URL}")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)