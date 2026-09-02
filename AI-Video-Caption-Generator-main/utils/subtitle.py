import os
import uuid
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.config import change_settings
from config import IMAGEMAGICK_PATH

os.makedirs("static/videos", exist_ok=True)
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})


def create_caption(textJSON, frame_size, font_size=None, font_color="white", font_family="Arial-Bold", bg_color="black"):
    sent, s, e = textJSON["word"], textJSON["start"], textJSON["end"]

    font_size = int(font_size) if font_size else int(frame_size[1] * 0.05)
    padding = 20

    print(f"[Subtitle] Font: {font_family}, Size: {font_size}, Color: {font_color}, BG: {bg_color}")

    txt = TextClip(
        sent,
        fontsize=font_size,
        font=font_family,
        color=font_color,
        method="caption",
        size=(int(frame_size[0] * 0.8), None),
        align="center"
    ).set_start(s).set_duration(e - s).set_position(("center", frame_size[1] * 0.85))

    bg = TextClip(
        " " * len(sent),
        fontsize=font_size,
        font=font_family,
        size=(int(frame_size[0] * 0.8) + padding, txt.size[1] + padding),
        color=bg_color,
        bg_color=bg_color
    ).set_opacity(0.6).set_start(s).set_duration(e - s).set_position(("center", frame_size[1] * 0.85))

    return [bg, txt]


def generate_output_path(original_path, suffix):
    base_name = os.path.basename(original_path).replace(".mp4", "")
    unique_id = uuid.uuid4().hex[:6]
    new_name = f"{base_name}_{suffix}_{unique_id}.mp4"
    return os.path.join("static", "videos", new_name)


def generate_video_with_sentence_subtitles(video_path, subs, font_size=None, font_color="white", font_family="Arial-Bold", bg_color="black"):
    video = VideoFileClip(video_path)
    frame_size = video.size
    clips = [video]
    for s in subs:
        clips += create_caption(s, frame_size, font_size=font_size, font_color=font_color, font_family=font_family, bg_color=bg_color)
    out = generate_output_path(video_path, "sentencecaptioned")
    CompositeVideoClip(clips).write_videofile(out, codec="libx264", audio_codec="aac", threads=4, preset="ultrafast")
    return out


def generate_video_with_word_subtitles(video_path, subs, font_size=None, font_color="white", font_family="Arial-Bold", bg_color="black"):
    video = VideoFileClip(video_path)
    frame_size = video.size
    clips = [video]
    for s in subs:
        clips += create_caption(s, frame_size, font_size=font_size, font_color=font_color, font_family=font_family, bg_color=bg_color)
    out = generate_output_path(video_path, "wordcaptioned")
    CompositeVideoClip(clips).write_videofile(out, codec="libx264", audio_codec="aac", threads=4, preset="ultrafast")
    return out
