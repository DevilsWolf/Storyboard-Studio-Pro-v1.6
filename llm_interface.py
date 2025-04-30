# storyboard_app/llm_interface.py
import requests
import json
from prompts import SCENE_GENERATION_SYSTEM_PROMPT, IMAGE_PROMPT_GENERATION_SYSTEM_PROMPT
import traceback
import time
import configparser
import os

CONFIG_FILE = "config.ini" # Define config file path

def _load_llm_config():
    """Loads LLM related config just before use."""
    config = configparser.ConfigParser()
    # Provide safe defaults IN CASE reading fails badly
    config['API'] = {'lm_studio_base_url': 'http://localhost:1234/v1'}
    config['Models'] = {'lm_studio_model_identifier': 'loaded-model-placeholder'}
    try:
        if os.path.exists(CONFIG_FILE):
            config.read(CONFIG_FILE)
        else:
            print(f"Warning: {CONFIG_FILE} not found in llm_interface. Using defaults.")
    except Exception as e:
         print(f"Error reading {CONFIG_FILE} in llm_interface: {e}. Using defaults.")
    return config

# --- Generation Parameters (can also be moved to config) ---
TEMPERATURE = 0.7
MAX_TOKENS = 512
# --- ------------- ---

def call_lm_studio_api(system_prompt, user_prompt):
    """Sends request to LM Studio API using current config settings."""
    config = _load_llm_config() # Load config on each call
    api_base_url = config.get('API', 'lm_studio_base_url', fallback='http://localhost:1234/v1')
    chat_endpoint = f"{api_base_url}/chat/completions"
    model_identifier = config.get('Models', 'lm_studio_model_identifier', fallback='loaded-model-placeholder')

    headers = {"Content-Type": "application/json"}
    payload = {
        "model": model_identifier,
        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS, "stream": False
    }
    print("-" * 60); print(f"Sending request to LM Studio API (Endpoint: {chat_endpoint})"); print(f"Model Identifier: {model_identifier}")

    try:
        response = requests.post(chat_endpoint, headers=headers, json=payload, timeout=180)
        response.raise_for_status()
        response_data = response.json()
        # ... (Rest of response parsing and error handling remains the same as previous version) ...
        if response_data and isinstance(response_data.get("choices"), list) and len(response_data["choices"]) > 0:
             first_choice = response_data["choices"][0]
             if isinstance(first_choice.get("message"), dict):
                 message_content = first_choice["message"].get("content")
                 if isinstance(message_content, str): print("LM Studio API request successful."); return message_content.strip()
        print(f"Error: LM Studio response format unexpected."); print(f"Full Response: {response_data if 'response_data' in locals() else 'N/A'}"); return None
    except Exception as e: print(f"Error during LM Studio call: {e}"); print(traceback.format_exc()); return None # Catch-all


def generate_scenes(story_text):
    # ... (logic remains the same, uses call_lm_studio_api) ...
    print(">>> Request received: Generate Scenes (via LM Studio API)")
    if not story_text: return None
    response_text = call_lm_studio_api(SCENE_GENERATION_SYSTEM_PROMPT, story_text)
    if isinstance(response_text, str):
        # ... (scene parsing logic remains the same) ...
        scenes = []
        lines = response_text.strip().split('\n');
        for line in lines:
            line = line.strip()
            if '.' in line: parts = line.split('.', 1);
            else: parts = []
            if len(parts) == 2 and parts[0].strip().isdigit(): scene_desc = parts[1].strip();
            else: scene_desc = line
            if scene_desc: scenes.append(scene_desc)
        if not scenes: print(f"Warning: Scene parsing failed.\nRaw Response:\n{response_text}"); return None
        print(f"Generated and parsed {len(scenes)} scenes.")
        return scenes
    else: print(f"Error: No valid response text from LLM for scene gen."); return None

def generate_image_prompt(story_text, scene_description, key_elements_text,
                          prev_scene_num, prev_scene_desc, prev_scene_prompt, current_scene_num):
    # ... (logic remains the same, uses call_lm_studio_api) ...
    print(f">>> Request: Generate Prompt (w/ Prev Context) for Scene {current_scene_num}: '{scene_description[:50]}...'")
    if not story_text or not scene_description: print("Error: Story/scene missing."); return None, None
    key_elements_text = key_elements_text if key_elements_text else "None provided."
    prev_scene_num_str = str(prev_scene_num) if prev_scene_num is not None else "N/A"
    prev_scene_desc_str = prev_scene_desc if prev_scene_desc else "N/A (First scene)"
    prev_scene_prompt_str = (prev_scene_prompt[:250] + '...' if len(prev_scene_prompt or '') > 250 else prev_scene_prompt) if prev_scene_prompt else "N/A"
    try: formatted_system_prompt = IMAGE_PROMPT_GENERATION_SYSTEM_PROMPT.format(story=story_text, key_elements=key_elements_text, prev_scene_num=prev_scene_num_str, prev_scene_desc=prev_scene_desc_str, prev_scene_prompt=prev_scene_prompt_str, current_scene_num=current_scene_num, scene=scene_description)
    except KeyError as e: print(f"ERROR: Missing key '{e}' in prompts.py."); return None, None
    user_input = f"Generate the prompt block for Scene {current_scene_num} now."
    llm_response_block = call_lm_studio_api(formatted_system_prompt, user_input)
    if isinstance(llm_response_block, str):
        # ... (prompt parsing logic remains the same) ...
        main_prompt, negative_prompt = "", "ugly, deformed, blurry, low quality, worst quality"
        try:
            lines = llm_response_block.strip().split('\n'); neg_idx = -1
            for i, line in enumerate(lines):
                if line.strip().lower().startswith("negative prompt:"): neg_idx = i; break
            if neg_idx != -1: main_prompt = "\n".join(lines[:neg_idx]).strip(); negative_prompt = lines[neg_idx][len("Negative Prompt:"):].strip()
            else: print("Warning: Could not parse 'Negative Prompt:'."); main_prompt = llm_response_block.strip()
            main_prompt, negative_prompt = main_prompt.strip('"\' '), negative_prompt.strip('"\' ')
            if not main_prompt: print(f"Error: Main prompt parsing empty.\nRaw Block:\n{llm_response_block}"); return None, None
            print(f"  Parsed Main Prompt (snippet): {main_prompt[:100]}..."); print(f"  Parsed Negative Prompt: {negative_prompt}")
            return main_prompt, negative_prompt
        except Exception as e: print(f"Error parsing prompt block: {e}\nRaw Block:\n{llm_response_block}"); return None, None
    else: print(f"Error: No valid response text from LLM for prompt gen."); return None, None