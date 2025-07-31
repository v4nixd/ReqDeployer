import os
import requests
import ipaddress

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

GITHUB_HOOKS_IPS = requests.get("https://api.github.com/meta").json()["hooks"]
GITHUB_HOOKS_NETS = [ipaddress.ip_network(ip) for ip in GITHUB_HOOKS_IPS]

def is_github_ip(ip: str) -> bool:
    client_ip = ipaddress.ip_address(ip)
    return any(client_ip in net for net in GITHUB_HOOKS_NETS)

@router.post("/github")
async def github_webhook(request: Request) -> dict[str, str]:
    client_host = request.client.host
    if not is_github_ip(client_host):
        raise HTTPException(status_code=403, detail="Forbidden: not GitHub")
    
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