import os, subprocess, shlex, json, tempfile, uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Dict

app = FastAPI(title="Gemini CLI Backend (PoC)")

def stream_gemini_cli(prompt: str):
    # 非互動 + 不帶 --json；把 stderr 併到 stdout，錯誤也會串回客戶端
    proc = subprocess.Popen(
        ["gemini", "-p", prompt],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    try:
        for line in iter(proc.stdout.readline, ''):
            yield line
    finally:
        try:
            proc.stdout.close()
        except Exception:
            pass
        proc.wait()




@app.post("/chat/stream")
def chat_stream(body: Dict):
    prompt = (body or {}).get("prompt", "").strip()
    if not prompt:
        raise HTTPException(400, "prompt required")
    return StreamingResponse(stream_gemini_cli(prompt), media_type="text/plain")

def run_with_template(template_path: str, user_input: str):
    """
    簡單 BMAD：把模板 + 使用者輸入合併，丟給 /chat（非串流）
    """
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    merged = template.replace("{{input}}", user_input)

    # 非串流一次取回（用 --json 搭配 --no-color 避免控制碼）
    cmd = "gemini chat --json --no-color"
    proc = subprocess.Popen(
        shlex.split(cmd),
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True
    )
    out, err = proc.communicate(merged, timeout=120)
    if proc.returncode != 0:
        raise HTTPException(500, f"gemini error: {err}")
    # 嘗試 parse JSON；若失敗就當純文字
    try:
        return json.loads(out)
    except Exception:
        return {"text": out}

@app.post("/bmad/brief")
def bmad_brief(body: Dict):
    return JSONResponse(run_with_template("/app/bmad_prompts/brief.md", (body or {}).get("goal","")))

@app.post("/bmad/arch")
def bmad_arch(body: Dict):
    return JSONResponse(run_with_template("/app/bmad_prompts/arch.md", (body or {}).get("prd","")))

@app.post("/bmad/tasks")
def bmad_tasks(body: Dict):
    return JSONResponse(run_with_template("/app/bmad_prompts/tasks.md", (body or {}).get("arch","")))

@app.post("/bmad/deliver")
def bmad_deliver(body: Dict):
    return JSONResponse(run_with_template("/app/bmad_prompts/deliver.md", (body or {}).get("plan","")))
