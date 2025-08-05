import os
import time
import asyncio
import requests
import ipaddress
import subprocess

import yaml
import hmac
import hashlib
import uvicorn

import config

from fastapi import FastAPI, HTTPException, Request
from dotenv import load_dotenv

from main import DEBUG
from console import console

load_dotenv()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
if not WEBHOOK_SECRET:
    raise ValueError("WEBHOOK_SECRET not found in .env")

WEBHOOK_SECRET = WEBHOOK_SECRET.encode("utf-8")

router = FastAPI()

GITHUB_HOOKS_IPS = requests.get("https://api.github.com/meta").json()["hooks"]
GITHUB_HOOKS_NETS = [ipaddress.ip_network(ip) for ip in GITHUB_HOOKS_IPS]

BASE_GITHUB_URL = "https://github.com"

async def run_cmd(cmd, cwd=None):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\nstdout: {stdout.decode()}\nstderr: {stderr.decode()}")
    return stdout.decode()

async def is_github_ip(ip: str) -> bool:
    client_ip = ipaddress.ip_address(ip)
    return any(client_ip in net for net in GITHUB_HOOKS_NETS)

@router.post("/github")
async def github_webhook(request: Request) -> dict[str, str]:
    webhook_start = time.time()
    client_host = request.client.host
    if not await is_github_ip(client_host):
        raise HTTPException(status_code=403, detail="Forbidden: not GitHub")
    
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")
    
    mac = hmac.new(WEBHOOK_SECRET, body, hashlib.sha256).hexdigest()
    if signature != f"sha256={mac}":
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    payload = await request.json()
    ref = payload.get("ref", "")
    repo_json = payload.get("repository", "")
    branch = ref.split("/")[-1]
    BRANCH = config.get("branch")
    if branch != config.get("branch"):
        return {"status": "ignored", "branch": branch}
    if repo_json is str:
        return {"status": "ignored", "message": "repository not found in payload"}
    repo_name = repo_json["name"]
    repo_link = f"{BASE_GITHUB_URL}/{repo_json["full_name"]}"
    
    DEPLOY_DIR = config.get("deploydir").format(APP=repo_name)
    
    if not os.path.isdir(DEPLOY_DIR):
        await run_cmd(f"git clone --depth=1 --branch {BRANCH} {repo_link} {DEPLOY_DIR}")
    else:
        await run_cmd(f"git fetch origin {BRANCH}", cwd=DEPLOY_DIR)
        await run_cmd(f"git reset --hard origin/{BRANCH}", cwd=DEPLOY_DIR)
        
    venv_path = os.path.join(DEPLOY_DIR, ".venv")
    if os.name == "nt":
        venv_bin = os.path.join(venv_path, "Scripts")
        python_bin = os.path.abspath(os.path.join(venv_bin, "python.exe"))
    else:
        venv_bin = os.path.join(venv_path, "bin")
        python_bin = os.path.abspath(os.path.join(venv_bin, "python"))
        
    if not os.path.isdir(venv_path):
        await run_cmd(f"python3 -m venv .venv", cwd=DEPLOY_DIR)
        
    if DEBUG:
        console.print("🗃️ App Tree - [bright_black]ls -lR")
        console.print(f"[yellow]\n{await run_cmd("ls -lR", cwd=DEPLOY_DIR)}")
    await run_cmd(f"{python_bin} -m pip install --upgrade pip", cwd=DEPLOY_DIR)
    
    if not os.path.isfile(os.path.join(DEPLOY_DIR, "requirements.txt")):
        raise FileNotFoundError(f"requirements.txt not found in {DEPLOY_DIR}")
    await run_cmd(f"{python_bin} -m pip install -r requirements.txt", cwd=DEPLOY_DIR)
    
    if not os.path.isfile(os.path.join(DEPLOY_DIR, "reqdep.yaml")):
        raise FileNotFoundError(f"reqdep.yaml not found in {DEPLOY_DIR}, get it from https://github.com/v4nixd/ReqDeployer")
    with open(f"{DEPLOY_DIR}/reqdep.yaml") as file:
        repo_cfg = yaml.safe_load(file)
        repo_cfg_run = repo_cfg["run"]
        repo_cfg_run_file = repo_cfg_run["file"]
    
    for cmd in repo_cfg_run["command"]:
        await run_cmd(cmd.format(VENV_BIN=venv_bin, APP_DIR=DEPLOY_DIR, FILE=repo_cfg_run_file))
    
    webhook_end = time.time()
    webhook_total = webhook_end - webhook_start
    console.print(f"✅ [green]Successfully deployed[/green] [b magenta]{repo_name}[/b magenta] in [bright_black]{webhook_total:.2f}s[/bright_black] - [b red]{payload["before"][:7]}[/b red] -> [b green]{payload["after"][:7]}[/b green]")
    return {"status": "deployed", "branch": branch}

def main() -> None:
    console.print("⚙️ [b green]STARTING[/b green] API")
    uvicorn.run("api:router", host="0.0.0.0", port=config.get("port"))