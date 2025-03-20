import os
import subprocess
from pathlib import Path
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def check_gpu_support():
    """Check if NVIDIA GPU encoding is available"""
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            probe = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True)
            return 'h264_nvenc' in probe.stdout
        return False
    except FileNotFoundError:
        return False

def get_encoding_settings():
    """Get encoding settings based on available hardware"""
    has_gpu = check_gpu_support()
    logger.info(f"GPU encoding available: {has_gpu}")
    
    # Base quality settings
    crf = "28"  # Higher CRF = more compression (range 18-28 is good, 23 is default)
    
    if has_gpu:
        return {
            'codec': 'h264_nvenc',
            'preset': 'p7',  # More compression-focused preset
            'extra_params': [
                '-rc', 'vbr',  # Variable bitrate mode
                '-cq', '27',   # Quality-based VBR (higher = more compression)
                '-b:v', '800k',  # Target bitrate
                '-maxrate', '1200k',  # Maximum bitrate
                '-bufsize', '2400k'   # VBV buffer size
            ]
        }
    else:
        return {
            'codec': 'libx264',
            'preset': 'slower',  # Better compression than 'veryfast'
            'extra_params': [
                '-crf', crf,
                '-maxrate', '1000k',
                '-bufsize', '2000k',
                '-movflags', '+faststart'
            ]
        }

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

    encode_settings = get_encoding_settings()
    ffmpeg_command = [
        ffmpeg_path,
        "-y",
        "-i", input_path,
        "-vf", "scale='min(1280,iw)':'-2'",  # Maintain aspect ratio
        "-c:v", encode_settings['codec'],
        "-preset", encode_settings['preset'],
        *encode_settings['extra_params'],  # Unpack extra encoding parameters
        "-c:a", "aac",
        "-b:a", "96k",        # Reduced audio bitrate
        "-ac", "2",           # Convert to stereo
        "-ar", "44100",       # Standard audio sample rate
        "-map", "0:v:0",      # Take first video stream
        "-map", "0:a:0?",     # Take first audio stream if it exists
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
