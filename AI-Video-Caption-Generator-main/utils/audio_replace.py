import os
import subprocess
import uuid

from config import FFMPEG_PATH


def replace_audio_in_video(video_path: str, new_audio_path: str) -> str:
    if not video_path or not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    if not new_audio_path or not os.path.exists(new_audio_path):
        raise FileNotFoundError(f"Audio file not found: {new_audio_path}")

    base_name = os.path.splitext(os.path.basename(video_path))[0]
    output_name = f"{base_name}_newaudio_{uuid.uuid4().hex[:6]}.mp4"
    output_dir = os.path.join("static", "videos")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_name)

    cmd = [
        FFMPEG_PATH,
        "-i",
        video_path,
        "-i",
        new_audio_path,
        "-c:v",
        "copy",
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-shortest",
        output_path,
        "-y",
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Failed to replace audio in video")

    return output_path
