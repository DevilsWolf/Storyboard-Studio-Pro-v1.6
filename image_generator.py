# storyboard_app/image_generator.py
import requests
import os
import time
import configparser # Import configparser
import traceback

CONFIG_FILE = "config.ini" # Define config file path
ASSETS_DIR = "assets"

def _load_image_gen_config():
    """Loads image generator related config just before use."""
    config = configparser.ConfigParser()
    # Provide safe defaults
    config['API'] = {'fooocus_api_url': 'http://localhost:8888/v2/generation/text-to-image-with-ip'}
    config['Models'] = {'fooocus_base_model': 'juggernautXL_v8Rundiffusion.safetensors'}
    config['Defaults'] = {'aspect_ratio': '896*1152', 'performance': 'Speed'} # Example defaults
    try:
        if os.path.exists(CONFIG_FILE):
            config.read(CONFIG_FILE)
        else:
            print(f"Warning: {CONFIG_FILE} not found in image_generator. Using defaults.")
    except Exception as e:
        print(f"Error reading {CONFIG_FILE} in image_generator: {e}. Using defaults.")
    return config

def generate_image(prompt: str, negative_prompt: str, output_filename: str) -> bool:
    """Sends request to Fooocus API using current settings from config.ini."""
    config = _load_image_gen_config() # Load config on each call
    api_url = config.get('API', 'fooocus_api_url', fallback='http://localhost:8888/v2/generation/text-to-image-with-ip')
    base_model = config.get('Models', 'fooocus_base_model', fallback='juggernautXL_v8Rundiffusion.safetensors')
    aspect_ratio = config.get('Defaults', 'aspect_ratio', fallback='896*1152')
    performance = config.get('Defaults', 'performance', fallback='Speed')

    print("-" * 60)
    print(f"Requesting image from Fooocus:")
    print(f"   URL: {api_url}")
    print(f"   Base Model: {base_model}")
    print(f"   Aspect Ratio: {aspect_ratio}")
    print(f"   Performance: {performance}")
    print(f"   Prompt (snippet): '{prompt[:80]}...'")
    print(f"   Negative Prompt: '{negative_prompt}'")
    print(f"   Output File: '{output_filename}'")

    # Ensure assets directory exists
    os.makedirs(ASSETS_DIR, exist_ok=True)

    headers = {"accept": "image/png", "Content-Type": "application/json"}

    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "style_selections": ["Fooocus V2"],
        "performance_selection": performance, # Use value from config
        "aspect_ratios_selection": aspect_ratio, # Use value from config
        "image_number": 1,
        "image_seed": -1,
        "sharpness": 2,
        "guidance_scale": 4,
        "base_model_name": base_model, # Use value from config
        "refiner_model_name": "None",
        "refiner_switch": 0.5,
        # Assuming this list comprehension is correct for Fooocus API
        "loras": [{"enabled": True, "model_name": "None", "weight": 1} for _ in range(5)],
        "require_base64": False,
        "async_process": False,
    }

    start_time = time.time()
    try:
        print("Sending request to Fooocus API...")
        response = requests.post(api_url, json=payload, headers=headers, timeout=600) # Increased timeout
        end_time = time.time()
        print(f"Fooocus request finished in {end_time - start_time:.2f} seconds.")

        if response.status_code == 200:
            # Check if the response content type is an image
            if 'image' in response.headers.get('Content-Type', '').lower():
                print(f"Image received. Saving to '{output_filename}'...")
                try:
                    with open(output_filename, "wb") as f:
                        f.write(response.content) # Split statement onto new line
                    print("Image saved successfully.")
                    return True
                except IOError as e:
                    print(f"Error saving image file: {e}")
                    return False
            else:
                print(f"Error: Fooocus API returned OK status but unexpected Content-Type: {response.headers.get('Content-Type')}")
                try:
                    print(f"Response content start: {response.text[:500]}")
                except:
                    pass # Fail silently if response text is not accessible
                return False
        else:
            print(f"Error: Fooocus API failed. Status: {response.status_code}")
            try:
                print(f"Response content start: {response.text[:500]}")
            except:
                pass # Fail silently if response text is not accessible
            return False

    except requests.exceptions.Timeout:
        print("Error: Fooocus API request timed out.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Fooocus API: {e}")
        # You might want to print response text here if it's available
        # try: print(f"Response: {response.text[:500]}") except NameError: pass
        return False
    except Exception as e:
        print(f"Unexpected error during image generation: {e}")
        print(traceback.format_exc()) # Print full traceback for unexpected errors
        return False