import os
import platform
import shutil
from pathlib import Path

def get_ffmpeg_path():
    """Get the FFmpeg path based on the operating system"""
    # In Docker, FFmpeg is installed in the standard location
    if os.path.isfile('/usr/bin/ffmpeg'):
        return '/usr/bin/ffmpeg'
        
    # Try to find ffmpeg in PATH
    ffmpeg_command = shutil.which('ffmpeg')
    if ffmpeg_command:
        return ffmpeg_command
        
    # Default paths for different operating systems
    system = platform.system().lower()
    if system == 'windows':
        possible_paths = [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            r"C:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe"
        ]
    elif system == 'linux':
        possible_paths = [
            "/usr/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
            str(Path.home() / "ffmpeg/ffmpeg")
        ]
    else:  # macOS and others
        possible_paths = [
            "/usr/local/bin/ffmpeg",
            "/opt/homebrew/bin/ffmpeg",
            str(Path.home() / "ffmpeg/ffmpeg")
        ]
    
    # Check each possible path
    for path in possible_paths:
        if os.path.isfile(path):
            return path
            
    raise FileNotFoundError(
        "FFmpeg not found. Please install FFmpeg and make sure it's in your PATH or "
        "in one of the default locations. Visit https://ffmpeg.org/download.html"
    )

# Configuration
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500MB
