# services/ai_agent.py

import litellm
import re
import json
from flask import current_app

# --- 1. KEEP YOUR DB AND SECURITY IMPORTS ---
from models import db, AIModelConfig
from services.security import decrypt_key

# --- 2. KEEP YOUR TOKEN ESTIMATOR ---
def estimate_tokens(text: str) -> int:
    """
    Rough token estimator.
    1 token ≈ 4 characters (for English text).
    """
    if not text:
        return 0
    return max(1, len(text) // 4)

# --- 3. KEEP YOUR DB HELPER ---
def get_active_model_config() -> AIModelConfig:
    """
    Fetches the active AI model configuration from the database.
    """
    config = AIModelConfig.query.filter_by(is_active=True).first()
    if not config:
        # Fallback or error
        raise Exception("No active AI model is configured in the admin settings.")
    return config

# --- 4. (REMOVED) All phi.agent imports, get_model_instance, get_simple_agent, get_streaming_agent
# ---    (REMOVED) The old extract_usage function

# --- 5. NEW: run_agent (replaces old run_agent) ---
def run_agent(prompt: str) -> dict:
    """
    Runs a NON-STREAMING completion with litellm using the active model.
    Returns the same contract as the old run_agent:
    {"content": "...", "usage": {"input_tokens": ..., "output_tokens": ...}}
    """
    try:
        config = get_active_model_config()
        api_key = decrypt_key(config.encrypted_api_key)
        
        model_name = config.model_name
        
        # --- Handle provider-specific model name adjustments if needed ---
        if config.provider.lower() == "google":
             # litellm expects "gemini/model-name"
             if not model_name.startswith("gemini/"):
                 model_name = f"gemini/{model_name}"
        
        if config.provider.lower() == "groq":
             # litellm expects "groq/model-name"
             if not model_name.startswith("groq/"):
                 model_name = f"groq/{model_name}"
        
        if config.provider.lower() == "azure":
             # litellm expects "azure/deployment-name"
             if not model_name.startswith("azure/"):
                 model_name = f"azure/{model_name}"

        # (OpenAI models, e.g., "gpt-4o", usually just work as-is)

        messages = [{"role": "user", "content": prompt}]
        
        # --- Build litellm call with Azure endpoint if provided ---
        call_params = {
            "model": model_name,
            "messages": messages,
            "api_key": api_key,
        }
        
        # Add api_base for Azure or custom endpoints
        if config.api_base:
            call_params["api_base"] = config.api_base
        
        # --- Make the litellm call ---
        response = litellm.completion(**call_params)
        
        content = response.choices[0].message.content or ""
        
        # Extract exact usage
        usage = {
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
        }
        
        return {"content": content.strip(), "usage": usage}
        
    except Exception as e:
        print(f"❌ litellm non-streaming error: {e}")
        # Re-raise the exception so the route can handle it
        raise e

# --- 6. NEW: run_agent_and_get_content (replaces old version) ---
def run_agent_and_get_content(prompt: str) -> dict:
    """
    This function was previously for streaming, but now we can just
    use the non-streaming `run_agent` since it's cleaner and
    the refine_document route expects a single response.
    """
    # This directly calls our new `run_agent` function
    return run_agent(prompt)

# --- 7. NEW: run_streaming_agent (replaces old version) ---
def run_streaming_agent(prompt: str):
    """
    Runs a STREAMING completion with litellm.
    This fulfills the contract for the old streaming function,
    including estimating tokens at the end.
    """
    full_buffer = ""
    try:
        config = get_active_model_config()
        api_key = decrypt_key(config.encrypted_api_key)
        
        model_name = config.model_name
        if config.provider.lower() == "google":
             if not model_name.startswith("gemini/"):
                 model_name = f"gemini/{model_name}"
        if config.provider.lower() == "groq":
             if not model_name.startswith("groq/"):
                 model_name = f"groq/{model_name}"
        if config.provider.lower() == "azure":
             if not model_name.startswith("azure/"):
                 model_name = f"azure/{model_name}"

        messages = [{"role": "user", "content": prompt}]
        
        # --- Build streaming call with Azure endpoint if provided ---
        stream_params = {
            "model": model_name,
            "messages": messages,
            "api_key": api_key,
            "stream": True
        }
        
        if config.api_base:
            stream_params["api_base"] = config.api_base
        
        response_stream = litellm.completion(**stream_params)
        
        for chunk in response_stream:
            content_delta = chunk.choices[0].delta.content
            if content_delta:
                full_buffer += content_delta
                yield content_delta
                
    except Exception as e:
        print(f"❌ litellm streaming error: {e}")
        yield f"[ERROR]{str(e)}"
    finally:
        # --- ESTIMATE USAGE ---
        # Streaming does not return usage, so we MUST estimate it
        # to keep the TokenUsageLog compatible.
        try:
            usage_data = {
                "input_tokens": estimate_tokens(prompt),
                "output_tokens": estimate_tokens(full_buffer)
            }
            yield f"[USAGE_DATA]{json.dumps(usage_data)}"
        except Exception as e:
            print(f"⚠️ Could not estimate usage from litellm stream: {e}")
            yield f"[USAGE_DATA]{json.dumps({'input_tokens': 0, 'output_tokens': 0})}"


# --- 8. KEEP: Your clean_markdown_output helper ---
def clean_markdown_output(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"```(?:markdown|md)?\s*([\sS]*?)\s*```", r"\1", text, flags=re.DOTALL)
    text = text.replace("```", "")
    text = re.sub(r"^\s*---\s*$", "", text.strip(), flags=re.MULTILINE)
    text = re.sub(r"^\s*(>>>|\*\*) .*", "", text, flags=re.MULTILINE)
    return text.strip()