import os

import hmac
import hashlib
import uvicorn

import config

from fastapi import FastAPI, HTTPException, Request
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
if not WEBHOOK_SECRET:
    raise ValueError("WEBHOOK_SECRET not found in .env")

WEBHOOK_SECRET = WEBHOOK_SECRET.encode("utf-8")

router = FastAPI()

@router.post("/github")
async def github_webhook(request: Request) -> dict[str, str]:
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")
    
    mac = hmac.new(WEBHOOK_SECRET, body, hashlib.sha256)
    expected_signature = "sha256=" + mac.hexdigest()
    
    if not hmac.compare_digest(expected_signature, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    return {"status": "ok"}

def main() -> None:
    uvicorn.run("api:router", host="0.0.0.0", port=config.get("port"))