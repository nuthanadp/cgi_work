import json
import re
from threading import Lock
from typing import Any, Dict, List


_MODEL = None
_TOKENIZER = None
_MODEL_LOCK = Lock()


def _load_model(model_path: str):
    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    except Exception as exc:
        raise RuntimeError(
            "Transformers is not installed in the active environment. Install with: pip install transformers torch sentencepiece"
        ) from exc

    global _MODEL, _TOKENIZER
    if _MODEL is None or _TOKENIZER is None:
        with _MODEL_LOCK:
            if _MODEL is None or _TOKENIZER is None:
                _TOKENIZER = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
                _MODEL = AutoModelForSeq2SeqLM.from_pretrained(model_path, local_files_only=True)
    return _TOKENIZER, _MODEL


def _split_context(transcript: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", transcript.strip())
    contexts = [p.strip() for p in parts if len(p.strip().split()) >= 8]
    if contexts:
        return contexts
    return [transcript.strip()] if transcript.strip() else []


def _extract_json(text: str) -> Dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}

    raw = text[start : end + 1]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _fallback_mcq(context: str, idx: int) -> Dict[str, Any]:
    words = re.findall(r"[A-Za-z][A-Za-z\-']{3,}", context)
    answer = words[0] if words else "context"
    question = context.replace(answer, "_____", 1) if answer in context else f"What best fits this context: {context}"
    options = [answer, "Option A", "Option B", "Option C"]
    return {
        "question_no": idx,
        "question": f"Fill in the blank: {question}",
        "options": options,
        "answer": answer,
    }


def _normalize_mcq(item: Dict[str, Any], idx: int, fallback_context: str) -> Dict[str, Any]:
    question = str(item.get("question", "")).strip()
    answer = str(item.get("answer", "")).strip()
    options = item.get("options", [])

    if not question or not answer or not isinstance(options, list):
        return _fallback_mcq(fallback_context, idx)

    clean_options = [str(opt).strip() for opt in options if str(opt).strip()]
    if answer not in clean_options:
        clean_options.append(answer)

    unique_options = []
    seen = set()
    for opt in clean_options:
        key = opt.lower()
        if key not in seen:
            seen.add(key)
            unique_options.append(opt)

    while len(unique_options) < 4:
        unique_options.append(f"Option {len(unique_options) + 1}")

    return {
        "question_no": idx,
        "question": question,
        "options": unique_options[:4],
        "answer": answer,
    }


def _build_prompt(context: str) -> str:
    return (
        "You are an expert teacher. Create exactly one multiple-choice question from the context. "
        "Return only JSON with keys: question, options, answer. "
        "Rules: options must be an array of exactly 4 short choices, answer must match one option exactly, "
        "question should test understanding of the context.\n\n"
        f"Context: {context}"
    )


def generate_mcqs_with_flan(transcript: str, num_questions: int, model_path: str) -> List[Dict[str, Any]]:
    transcript = (transcript or "").strip()
    if not transcript:
        return []

    tokenizer, model = _load_model(model_path)
    contexts = _split_context(transcript)
    if not contexts:
        return []

    desired = max(1, int(num_questions))
    mcqs: List[Dict[str, Any]] = []

    for i in range(desired):
        context = contexts[i % len(contexts)]
        prompt = _build_prompt(context)
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)

        outputs = model.generate(
            **inputs,
            max_new_tokens=220,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            num_return_sequences=1,
        )

        text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        raw_item = _extract_json(text)
        mcqs.append(_normalize_mcq(raw_item, i + 1, context))

    return mcqs
