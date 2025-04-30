import tkinter as tk
from tkinter import scrolledtext, messagebox, Button, Label, Canvas, Frame, N, S, E, W, DISABLED, NORMAL
from PIL import Image, ImageTk
import requests
import threading
import os
import time

# --- Configuration ---
FOOCUS_API_URL = "http://localhost:8888/v2/generation/text-to-image-with-ip"
# Directory to save the generated image
OUTPUT_DIR = "generated_images"
OUTPUT_FILENAME = os.path.join(OUTPUT_DIR, "generated_image.png")
# Display size for the image in the UI
MAX_DISPLAY_WIDTH = 512
# --- ------------- ---

class ImageGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Fooocus Image Generator")
        # self.root.geometry("600x750") # Optional: Set initial size

        self.photo_image = None # To hold the PhotoImage object reference

        # Ensure output directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        self.setup_ui()
        self.update_status("Ready. Enter a prompt and click Generate.")

    def setup_ui(self):
        # Main Frame
        main_frame = Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Prompt Input Section
        prompt_label = Label(main_frame, text="Enter Image Prompt:")
        prompt_label.pack(anchor=W, pady=(0, 5))

        self.prompt_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=6, width=60)
        self.prompt_text.pack(fill=tk.X, expand=False) # Fill horizontally, don't expand vertically much

        # Generate Button
        self.generate_button = Button(main_frame, text="Generate Image", command=self.start_image_generation)
        self.generate_button.pack(pady=10)

        # Image Display Section
        # Calculate initial canvas height based on a common aspect ratio (e.g., 896*1152 from your API)
        aspect_ratio = 1152 / 896
        canvas_height = int(MAX_DISPLAY_WIDTH * aspect_ratio)
        self.image_canvas = Canvas(main_frame, bg="lightgrey", width=MAX_DISPLAY_WIDTH, height=canvas_height, relief=tk.SUNKEN, bd=1)
        self.image_canvas.pack(fill=tk.BOTH, expand=True, pady=(5, 0)) # Fill available space
        self.image_canvas.create_text(MAX_DISPLAY_WIDTH // 2, 30, text="Image will appear here", fill="darkgrey")

        # Status Bar
        self.status_label = Label(self.root, text="Initializing...", bd=1, relief=tk.SUNKEN, anchor=W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def update_status(self, message):
        print(f"STATUS: {message}")
        self.status_label.config(text=message)
        self.root.update_idletasks()

    def start_image_generation(self):
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("Input Error", "Please enter a prompt.")
            return

        self.update_status("Requesting image generation from Fooocus...")
        self.generate_button.config(state=DISABLED)
        self.clear_image_display() # Clear old image

        # Run the API call in a thread to avoid freezing the UI
        thread = threading.Thread(target=self.generate_image_thread_target, args=(prompt,), daemon=True)
        thread.start()

    def generate_image_thread_target(self, prompt):
        """This function runs in a separate thread."""
        headers = {"accept": "image/png", "Content-Type": "application/json"}
        payload = {
            "prompt": prompt,
            "negative_prompt": "", # Keep simple
            "style_selections": ["Fooocus V2"], # Keep simple
            "performance_selection": "Speed", # Important for speed/VRAM
            "aspect_ratios_selection": "896*1152", # Match canvas aspect ratio if possible
            "image_number": 1,
            "image_seed": -1,
            "sharpness": 2,
            "guidance_scale": 4,
            "base_model_name": "juggernautXL_v8Rundiffusion.safetensors", # From your docs
            "refiner_model_name": "None",
            "refiner_switch": 0.5,
            "loras": [{"enabled": True, "model_name": "None", "weight": 1} for _ in range(5)], # Default empty LoRAs
            "advanced_params": {},
            "require_base64": False,
            "async_process": False,
        }

        success = False
        error_message = "An unknown error occurred."
        start_time = time.time()

        try:
            print("Sending request to Fooocus API...")
            response = requests.post(FOOCUS_API_URL, json=payload, headers=headers, timeout=300) # Add timeout (e.g., 5 minutes)
            end_time = time.time()
            print(f"Fooocus request finished in {end_time - start_time:.2f} seconds.")

            if response.status_code == 200:
                if 'image' in response.headers.get('Content-Type', '').lower():
                    try:
                        with open(OUTPUT_FILENAME, "wb") as f:
                            f.write(response.content)
                        print(f"Image saved successfully to '{OUTPUT_FILENAME}'")
                        success = True
                    except IOError as e:
                        error_message = f"Error saving image file: {e}"
                        print(error_message)
                else:
                    error_message = f"Fooocus returned OK but content type is not image: {response.headers.get('Content-Type')}. Response: {response.text[:200]}"
                    print(error_message)
            else:
                error_message = f"Fooocus API request failed with status code {response.status_code}. Response: {response.text[:500]}"
                print(error_message)

        except requests.exceptions.Timeout:
            error_message = "Error: Fooocus API request timed out."
            print(error_message)
        except requests.exceptions.RequestException as e:
            error_message = f"Error communicating with Fooocus API: {e}"
            print(error_message)
        except Exception as e:
             error_message = f"An unexpected error occurred: {e}"
             print(error_message)

        # Schedule UI update back on the main thread
        self.root.after(0, self.handle_generation_result, success, error_message)

    def handle_generation_result(self, success, message):
        """This function runs in the main thread to update UI."""
        if success:
            self.update_status("Image generated successfully!")
            self.display_image(OUTPUT_FILENAME)
        else:
            self.update_status(f"Image generation failed: {message}")
            messagebox.showerror("Generation Failed", message)
            self.clear_image_display() # Clear canvas on failure too

        self.generate_button.config(state=NORMAL) # Re-enable button

    def display_image(self, image_path):
        """Loads and displays the image on the canvas."""
        try:
            # Ensure canvas dimensions are up-to-date
            self.root.update_idletasks()
            canvas_width = self.image_canvas.winfo_width()
            canvas_height = self.image_canvas.winfo_height()

            if canvas_width <= 1 or canvas_height <= 1:
                 canvas_width = MAX_DISPLAY_WIDTH
                 canvas_height = int(MAX_DISPLAY_WIDTH * (1152/896)) # Fallback dimensions


            img = Image.open(image_path)
            img_width, img_height = img.size
            aspect_ratio = img_width / img_height

            # Calculate new size to fit canvas while preserving aspect ratio
            new_width = canvas_width
            new_height = int(new_width / aspect_ratio)

            if new_height > canvas_height:
                new_height = canvas_height
                new_width = int(new_height * aspect_ratio)

            # Resize using LANCZOS for better quality downscaling
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # IMPORTANT: Keep a reference!
            self.photo_image = ImageTk.PhotoImage(resized_img)

            # Clear previous image and display new one centered
            self.image_canvas.delete("all")
            self.image_canvas.create_image(canvas_width // 2, canvas_height // 2, anchor=tk.CENTER, image=self.photo_image)
            print(f"Displayed image: {image_path}")

        except FileNotFoundError:
            messagebox.showerror("Error", f"Image file not found: {image_path}")
            self.clear_image_display()
        except Exception as e:
            messagebox.showerror("Image Display Error", f"Could not display image: {e}")
            print(f"Error details: {e}")
            self.clear_image_display()

    def clear_image_display(self):
        """Clears the image canvas."""
        self.image_canvas.delete("all")
        # Get current canvas size or use fallback
        canvas_width = self.image_canvas.winfo_width() or MAX_DISPLAY_WIDTH
        self.image_canvas.create_text(canvas_width // 2, 30, text="Image will appear here", fill="darkgrey")
        self.photo_image = None # Clear reference


# --- Application Entry Point ---
if __name__ == "__main__":
    root = tk.Tk()
    app = ImageGeneratorApp(root)
    root.mainloop()