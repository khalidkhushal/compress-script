import os
import subprocess
from pathlib import Path
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def compress_video(args):
    """
    Compresses a video using FFmpeg with optimized settings for better compression.
    """
    input_path, output_path, ffmpeg_path = args
    
    logger.debug(f"Starting compression with input: {input_path}")
    
    # Verify FFmpeg exists
    if not os.path.isfile(ffmpeg_path):
        error_msg = f"FFmpeg not found at path: {ffmpeg_path}"
        logger.error(error_msg)
        return False, error_msg

    # Check if input file exists
    if not os.path.isfile(input_path):
        error_msg = f"The input file {input_path} does not exist!"
        logger.error(error_msg)
        return False, error_msg
        
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Updated FFmpeg command with better compression settings
    ffmpeg_command = [
        ffmpeg_path,
        "-y",  # Overwrite output file if it exists
        "-i", input_path,
        "-vf", "scale='min(1280,iw)':'-2'",  # Scale width to 1280 or less, maintain aspect ratio
        "-c:v", "libx264",
        "-crf", "28",  # Constant Rate Factor (18-28 is good, higher = more compression)
        "-preset", "medium",  # Slower preset = better compression
        "-tune", "film",  # Optimize for typical video content
        "-b:v", "800k",  # Target video bitrate
        "-maxrate", "1000k",  # Maximum bitrate
        "-bufsize", "1600k",  # Buffer size (2x maxrate)
        "-movflags", "+faststart",  # Enable fast start for web playback
        "-c:a", "aac",
        "-b:a", "128k",  # Reduced audio bitrate
        "-ar", "44100",  # Audio sample rate
        output_path
    ]

    try:
        logger.debug(f"Running FFmpeg command: {' '.join(ffmpeg_command)}")
        
        # Run FFmpeg with both stdout and stderr captured
        process = subprocess.run(
            ffmpeg_command,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Check if output file was created and has size > 0
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info(f"Successfully compressed video to: {output_path}")
            return True, output_path
        else:
            error_msg = "Output file was not created or is empty"
            logger.error(error_msg)
            return False, error_msg

    except subprocess.CalledProcessError as e:
        error_msg = f"FFmpeg error: {e.stderr}"
        logger.error(error_msg)
        return False, error_msg
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
