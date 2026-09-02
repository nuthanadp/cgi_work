import os
import subprocess
from faster_whisper import WhisperModel
from moviepy.config import get_setting
from config import FFMPEG_PATH, LOCAL_MODEL_PATH

get_setting("IMAGEMAGICK_BINARY")  # Ensure ImageMagick is configured

def extract_audio(video_path, audio_path):
    cmd = [FFMPEG_PATH, "-i", video_path, "-q:a", "0", "-ac", "1", "-ar", "16000", "-map", "a", audio_path, "-y"]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def transcribe_audio(audio_path):
    model = WhisperModel(LOCAL_MODEL_PATH, compute_type="int8", local_files_only=True)
    segments, _ = model.transcribe(audio_path, word_timestamps=True)

    words, full_text = [], ""
    for seg in segments:
        full_text += seg.text.strip() + " "
        for w in getattr(seg, "words", []):
            words.append({
                "word": w.word,
                "start": w.start,
                "end": w.end
            })
    
    os.remove(audio_path)
    return words, full_text.strip()

def split_text_into_lines(data):
    subtitles, line, dur = [], [], 0
    max_chars, max_dur, max_gap = 30, 2.5, 1.5

    for i, w in enumerate(data):
        line.append(w)
        dur += w['end'] - w['start']
        txt = " ".join(x['word'] for x in line)
        if dur > max_dur or len(txt) > max_chars or (i > 0 and w['start'] - data[i - 1]['end'] > max_gap):
            subtitles.append({
                "word": txt,
                "start": line[0]['start'],
                "end": line[-1]['end']
            })
            line, dur = [], 0

    if line:
        subtitles.append({
            "word": " ".join(x['word'] for x in line),
            "start": line[0]['start'],
            "end": line[-1]['end']
        })

    return subtitles
