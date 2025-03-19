import os
import subprocess
from multiprocessing import Pool
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

def compress_video(args):
    """
    Compresses a video to Facebook-like specifications using FFmpeg.
    
    :param args: Tuple containing (input_path, output_path, ffmpeg_path, max_threads)
    """
    input_path, output_path, ffmpeg_path = args
    
    # Check if input file exists
    if not os.path.isfile(input_path):
        print(f"The input file {input_path} does not exist!")
        return
        
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # FFmpeg command
    ffmpeg_command = [
        ffmpeg_path,
        "-y",
        "-i", input_path,
        "-vf", "scale=1280:720",
        "-b:v", "1167824",
        "-b:a", "48023",
        "-r", "25",
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "aac",
        "-q:a", "2",
        output_path
    ]

    try:
        subprocess.run(ffmpeg_command, check=True)
        print(f"Compression successful! Compressed video saved at {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error during compression of {input_path}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred with {input_path}: {e}")

def process_videos(input_folder, output_folder, ffmpeg_path, max_threads = 10):
    # Create list of video files to process
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.wmv')
    input_files = [f for f in Path(input_folder).glob('*') if f.suffix.lower() in video_extensions]
    
    # Prepare arguments for each video
    args_list = []
    for input_file in input_files:
        output_file = Path(output_folder) / f"compressed_{input_file.name}"
        args_list.append((str(input_file), str(output_file), ffmpeg_path))
    
    # Process videos in parallel using all available CPU cores
    # with Pool() as pool:
    #     pool.map(compress_video, args_list)

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        # Submit all tasks and get futures
        futures = [executor.submit(compress_video, args) for args in args_list]
        
        # Print total number of videos to process
        total_videos = len(futures)
        print(f"Processing {total_videos} videos...")
        
        # Wait for all tasks to complete
        completed = 0
        for future in futures:
            future.result()  # Wait for task to complete
            completed += 1
            print(f"Progress: {completed}/{total_videos} videos processed")

if __name__ == "__main__":
    # Specify paths
    input_folder = "input"  # Replace with your input folder path
    output_folder = "output"  # Replace with your output folder path
    ffmpeg_path = r"C:\ffmpeg-7.0.2-essentials_build\bin\ffmpeg.exe"
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Process all videos in the input folder
    process_videos(input_folder, output_folder, ffmpeg_path, max_threads = 10)  