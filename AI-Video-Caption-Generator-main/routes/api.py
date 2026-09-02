import os
import json
import time
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from utils.transcription import extract_audio, transcribe_audio, split_text_into_lines
from utils.subtitle import (
    generate_video_with_sentence_subtitles,
    generate_video_with_word_subtitles,
)
from utils.audio_replace import replace_audio_in_video
from utils.mcq_generation import generate_mcqs_with_flan
from config import FLAN_MODEL_PATH

api_bp = Blueprint("api", __name__)
UPLOAD_FOLDER = "static"

def get_transcript_path():
    return current_app.config.get("TRANSCRIPT_FILE", "transcript.json")

def load_transcript():
    path = get_transcript_path()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f).get("transcript", "")
    return ""

def save_transcript(text):
    path = get_transcript_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"transcript": text}, f)


@api_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file found'}), 400
    video = request.files['video']
    if video.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    upload_dir = os.path.join(current_app.root_path, 'static', 'videos')
    os.makedirs(upload_dir, exist_ok=True)

    filepath = os.path.join(upload_dir, video.filename)
    video.save(filepath)

    return jsonify({'filepath': filepath}), 200


@api_bp.route('/transcribe', methods=['POST'])
def transcribe():
    data = request.get_json()
    if not data:
        return jsonify(error="Invalid JSON format"), 400

    video_path = data.get('video_path')
    if not video_path:
        return jsonify(error="video_path required"), 400

    audio_path = video_path.replace(".mp4", ".wav")

    try:
        start_time = time.time()

        extract_audio(video_path, audio_path)
        wordlevel, transcript = transcribe_audio(audio_path)
        sentence_level = split_text_into_lines(wordlevel)

        elapsed_time = time.time() - start_time

        save_transcript(transcript)

        return jsonify({
            "transcript": transcript,
            "wordlevel": wordlevel,
            "sentences": sentence_level,
            "time_taken": round(elapsed_time, 2)
        }), 200

    except Exception as e:
        print("Transcription error:", str(e))
        return jsonify(error=str(e)), 500


@api_bp.route("/get_transcript", methods=["GET"])
def get_transcript():
    return jsonify(transcript=load_transcript())


@api_bp.route("/edit_transcript", methods=["POST"])
def edit_transcript():
    data = request.get_json()
    txt = data.get("transcript", "")
    save_transcript(txt)
    return jsonify(message="Transcript saved")


@api_bp.route("/generate_mcqs", methods=["POST"])
def generate_mcqs():
    data = request.get_json() or {}
    transcript = (data.get("transcript") or "").strip()
    num_questions = data.get("num_questions", 8)

    if not transcript:
        transcript = load_transcript().strip()

    if not transcript:
        return jsonify(error="Transcript is required"), 400

    try:
        num_questions = int(num_questions)
    except (TypeError, ValueError):
        return jsonify(error="num_questions must be an integer"), 400

    if num_questions < 1 or num_questions > 30:
        return jsonify(error="num_questions must be between 1 and 30"), 400

    try:
        mcqs = generate_mcqs_with_flan(
            transcript=transcript,
            num_questions=num_questions,
            model_path=FLAN_MODEL_PATH,
        )
        return jsonify(mcqs=mcqs, count=len(mcqs))
    except Exception as e:
        return jsonify(error=f"MCQ generation failed: {str(e)}"), 500


@api_bp.route("/generate_subtitles", methods=["POST"])
def generate_subtitles():
    data = request.get_json()
    video_path = data.get("video_path")
    transcript = data.get("transcript")
    words = data.get("wordlevel")
    mode = data.get("mode", "sentence")
    font_size = data.get("font_size")
    font_color = data.get("font_color", "white")
    font_family = data.get("font_family", "Arial-Bold")
    bg_color = data.get("bg_color", "black")

    if not video_path or transcript is None or words is None:
        return jsonify(error="video_path, transcript, and wordlevel are required"), 400

    edited = transcript.split()
    for i in range(min(len(edited), len(words))):
        words[i]["word"] = edited[i]

    subs = split_text_into_lines(words)

    if mode == "word":
        out_path = generate_video_with_word_subtitles(
            video_path,
            subs,
            font_size=font_size,
            font_color=font_color,
            font_family=font_family,
            bg_color=bg_color
        )
    else:
        out_path = generate_video_with_sentence_subtitles(
            video_path,
            subs,
            font_size=font_size,
            font_color=font_color,
            font_family=font_family,
            bg_color=bg_color
        )

    relative_path = os.path.relpath(out_path, "static").replace("\\", "/")
    video_url = f"/static/{relative_path}"

    return jsonify(output_video=video_url)


@api_bp.route("/download/<path:filename>", methods=["GET"])
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


@api_bp.route("/generate_audio", methods=["POST"])
def generate_audio():
    import os
    import pyttsx3
    import tempfile
    import shutil
    import wave
    import numpy as np
    from scipy.io.wavfile import write as write_wav
    from flask import request, jsonify

    data = request.get_json()
    transcript = data.get("transcript", "").strip()
    if not transcript:
        return jsonify({"error": "Transcript is required"}), 400

    try:
        print("📥 Transcript received:", transcript)

        # Output location
        output_dir = os.path.join("static", "audio")
        os.makedirs(output_dir, exist_ok=True)
        final_output_path = os.path.join(output_dir, "generated_tts.wav")

        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
            tmp_path = tmpfile.name

        # Generate audio using pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 150)
        engine.save_to_file(transcript, tmp_path)
        engine.runAndWait()

        # Convert to 16-bit PCM WAV using scipy
        with wave.open(tmp_path, "rb") as wav_file:
            framerate = wav_file.getframerate()
            audio_data = wav_file.readframes(wav_file.getnframes())

        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        write_wav(final_output_path, rate=framerate, data=audio_array)

        # Cleanup
        os.remove(tmp_path)

        print("✅ Audio generated:", final_output_path)
        return jsonify({"audio_path": final_output_path}), 200

    except Exception as e:
        print("❌ Audio generation error:", str(e))
        return jsonify({"error": str(e)}), 500



@api_bp.route("/replace_audio", methods=["POST"])
def replace_audio():
    try:
        data = request.get_json()

        # ✅ Safely decode paths
        video_path = data.get("video_path", "").encode("utf-8", "ignore").decode("utf-8")
        new_audio_path = data.get("new_audio_path", "").encode("utf-8", "ignore").decode("utf-8")

        if not video_path or not new_audio_path:
            return jsonify({"error": "Missing video_path or new_audio_path"}), 400

        # ✅ Replace audio
        replaced_video_path = replace_audio_in_video(video_path, new_audio_path)

        return jsonify({"output_video": replaced_video_path}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
