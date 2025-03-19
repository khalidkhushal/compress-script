from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import os
import shutil
from werkzeug.utils import secure_filename
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from .video_processor import compress_video
import logging
from .config import get_ffmpeg_path, UPLOAD_FOLDER, OUTPUT_FOLDER, MAX_UPLOAD_SIZE
import zipfile
import io
from datetime import datetime
import asyncio
from typing import List

logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Configuration
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"

# Get FFmpeg path on startup
try:
    FFMPEG_PATH = get_ffmpeg_path()
    logger.info(f"Using FFmpeg at: {FFMPEG_PATH}")
except FileNotFoundError as e:
    logger.error(f"FFmpeg configuration error: {e}")
    raise

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Add max workers configuration
MAX_WORKERS = 3  # Adjust based on your CPU cores

async def process_video(video_file, filename):
    """Process a single video file"""
    file_path = None
    output_path = None
    try:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        output_path = os.path.join(OUTPUT_FOLDER, f"compressed_{filename}")
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(video_file.file, buffer)
        
        # Use ThreadPoolExecutor for CPU-intensive compression
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(compress_video, (file_path, output_path, FFMPEG_PATH))
            success, result = future.result()
            
        if not success:
            raise HTTPException(status_code=500, detail=result)
            
        return output_path
        
    except Exception as e:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        if output_path and os.path.exists(output_path):
            os.remove(output_path)
        raise e
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload/")
async def upload_video(video: UploadFile = File(...)):
    """Handle single file upload with improved threading"""
    try:
        if not video.filename:
            raise HTTPException(status_code=400, detail="No file uploaded")
        
        safe_filename = secure_filename(video.filename)
        output_path = await process_video(video, safe_filename)
        
        return FileResponse(
            output_path,
            media_type="video/mp4",
            filename=f"compressed_{safe_filename}"
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-multiple/")
async def upload_multiple_videos(files: List[UploadFile] = File(...)):
    """Handle multiple file uploads concurrently"""
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files uploaded")
        
        successful_files = []
        
        # Process videos with a fixed thread pool
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = []
            
            for video in files:
                if not video.filename:
                    continue
                    
                safe_filename = secure_filename(video.filename)
                file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
                output_path = os.path.join(OUTPUT_FOLDER, f"compressed_{safe_filename}")
                
                # Save uploaded file
                try:
                    contents = await video.read()
                    with open(file_path, "wb") as f:
                        f.write(contents)
                except Exception as e:
                    logger.error(f"Failed to save uploaded file {safe_filename}: {e}")
                    continue
                
                # Submit compression task
                future = pool.submit(compress_video, (file_path, output_path, FFMPEG_PATH))
                futures.append((future, safe_filename, file_path))
            
            # Wait for all compressions to complete
            for future, filename, input_path in futures:
                try:
                    success, result = future.result()
                    if success:
                        successful_files.append({
                            "original_name": filename,
                            "compressed_path": os.path.basename(result)  # Just return filename
                        })
                    else:
                        logger.error(f"Compression failed for {filename}: {result}")
                except Exception as e:
                    logger.error(f"Error processing {filename}: {e}")
                finally:
                    # Clean up input file
                    if os.path.exists(input_path):
                        os.remove(input_path)
        
        if not successful_files:
            raise HTTPException(status_code=500, detail="No files were successfully processed")
            
        return {"processed_files": successful_files}
            
    except Exception as e:
        logger.exception("Error during multiple file upload")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{filename}")
async def download_video(filename: str, background_tasks: BackgroundTasks):
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Function to cleanup file after download
        async def cleanup_after_download():
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Cleaned up compressed file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to clean up file {file_path}: {e}")

        # Add cleanup to background tasks
        background_tasks.add_task(cleanup_after_download)
        
        return FileResponse(
            file_path, 
            media_type="video/mp4",
            filename=filename
        )
        
    except Exception as e:
        logger.exception("Error during file download")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/clear-output")
async def clear_output():
    """Endpoint to manually clear all files in the output directory"""
    try:
        files = [f for f in os.listdir(OUTPUT_FOLDER) if os.path.isfile(os.path.join(OUTPUT_FOLDER, f))]
        for file in files:
            try:
                os.remove(os.path.join(OUTPUT_FOLDER, file))
                logger.debug(f"Cleared file: {file}")
            except Exception as e:
                logger.error(f"Failed to clear file {file}: {e}")
        return {"message": f"Cleared {len(files)} files from output directory"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cleanup/{filename}")
async def cleanup_file(filename: str):
    """Cleanup a specific file after it has been downloaded"""
    try:
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return {"message": f"Successfully cleaned up {filename}"}
        return {"message": "File already removed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
