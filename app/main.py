import os
import uuid
import threading
import time
import re
from pathlib import Path
from typing import List, Dict
from fastapi import FastAPI, Request, UploadFile, Form, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# 引入核心逻辑
from .core import create_video_from_images

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Pic-to-Vid")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# 任务状态存储
TASKS: Dict[str, dict] = {}

def cleanup_task(task_id: str, file_path: str = None):
    """延迟清理任务"""
    time.sleep(600) 
    if task_id in TASKS:
        del TASKS[task_id]
    if file_path and os.path.exists(file_path):
        os.remove(file_path)

def sanitize_filename(name: str) -> str:
    """清理文件名中的非法字符"""
    return re.sub(r'[\\/*?:"<>|]', "", name) or "video"

def background_video_generation(task_id, files_content, duration, resolution):
    try:
        def update_progress(percent=None, message=None, stage=None):
            if percent is not None:
                TASKS[task_id]["percent"] = percent
            if message:
                TASKS[task_id]["msg"] = message

        video_path = create_video_from_images(
            files_content, 
            duration_per_image=duration,
            resolution_type=resolution,
            progress_callback=update_progress
        )
        
        TASKS[task_id]["status"] = "completed"
        TASKS[task_id]["percent"] = 100
        TASKS[task_id]["result"] = video_path
        
        threading.Thread(target=cleanup_task, args=(task_id, video_path)).start()

    except Exception as e:
        TASKS[task_id]["status"] = "failed"
        TASKS[task_id]["msg"] = str(e)
        print(f"Task {task_id} Failed: {e}")

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_and_start(
    files: List[UploadFile],
    title: str = Form(...),      # 新增：接收标题
    duration: float = Form(2.0),
    resolution: str = Form("portrait")
):
    task_id = str(uuid.uuid4())
    
    files_content = []
    for file in files:
        content = await file.read()
        if len(content) > 0:
            files_content.append(content)
    
    if not files_content:
        return JSONResponse(status_code=400, content={"error": "没有有效图片"})

    TASKS[task_id] = {
        "status": "processing",
        "percent": 0,
        "msg": "准备中...",
        "result": None,
        "filename": f"{sanitize_filename(title)}.mp4" # 存储文件名
    }

    thread = threading.Thread(
        target=background_video_generation,
        args=(task_id, files_content, duration, resolution)
    )
    thread.start()

    return {"task_id": task_id}

@app.get("/status/{task_id}")
async def check_status(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        return JSONResponse(status_code=404, content={"error": "任务不存在"})
    return task

@app.get("/download/{task_id}")
async def download_video(task_id: str):
    task = TASKS.get(task_id)
    if not task or task["status"] != "completed":
        return JSONResponse(status_code=400, content={"error": "文件未就绪"})
    
    # 使用用户定义的标题下载
    return FileResponse(
        task["result"],
        media_type="video/mp4",
        filename=task.get("filename", "video.mp4")
    )