# storyboard_app/main.py
import customtkinter as ctk
from PIL import Image
import os
import threading
import time # Needed for timestamping filenames
import db_manager # Needs DB_FILE constant accessible
import llm_interface # Assumes configured for your backend (e.g., LM Studio API)
import image_generator
import traceback # For debugging exceptions
import tkinter.messagebox # Use standard tkinter for simple popups
import gc # For garbage collection
import shutil # For export feature later
from tkinter import filedialog # For export feature later
import configparser # For settings
from tkinter import Menu # For File menu

# --- Import UI Components ---
try:
    from ui_components.scene_card import SceneCard
    from ui_components.settings_window import SettingsWindow
    from ui_components.tooltips import ToolTip
    import ui_components.main_window_ui as main_ui # Import the UI creation functions
except ImportError as e:
    print(f"ERROR: Failed to import UI component: {e}")
    print("Please ensure ui_components folder exists and contains required files.")
    exit()
# --- -------------------- ---

# --- App Configuration ---
APP_NAME = "Storyboard Studio Pro v1.6" # Version indicator
DEFAULT_APPEARANCE = "dark"
DEFAULT_COLOR_THEME = "blue"
MAX_IMAGE_DISPLAY_WIDTH = 600
ASSETS_DIR = "assets"
PROMPT_NOT_GENERATED_TEXT = "<Prompt not generated yet>"
CONFIG_FILE = "config.ini"
# --- ------------- ---

# --- Status Colors & Selected BG defined in scene_card.py now ---

# --- Main Application Class ---
class StoryboardApp(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title(APP_NAME)
        self.geometry("1300x800")
        self.minsize(1000, 650)

        ctk.set_appearance_mode(DEFAULT_APPEARANCE)
        ctk.set_default_color_theme(DEFAULT_COLOR_THEME)

        self._config = self._load_config() # Load settings

        # --- State Variables ---
        self.current_story_id = None
        self.scenes_data = [] # Cache: List[{id, num, desc, prompt, neg_prompt, path}]
        self.selected_scene_id = None
        self.displayed_ctk_image = None
        self.scene_cards = {} # Map: scene_id -> SceneCard instance
        self.image_label = None
        self.prompt_generation_cache = {} # NEW: LLM Prompt Cache

        # --- Fonts ---
        self.title_font = ctk.CTkFont(size=16, weight="bold")
        self.label_font = ctk.CTkFont(size=13)
        self.small_font = ctk.CTkFont(size=11)
        self.placeholder_font = ctk.CTkFont(size=14, slant="italic")

        # --- Initialize DB ---
        if not self._initialize_database(): self.destroy(); return

        # --- Create UI ---
        self._create_menu()
        self._create_main_widgets()

        print(f"{APP_NAME} Initialized.")
        self.update_status("Ready. Settings loaded. Enter story & key elements, then Generate Scenes.")
        print("NOTE: Progress saved automatically to 'storyboard.db'.")
        if hasattr(self, 'export_button'): self.export_button.configure(state="disabled")


    def _load_config(self):
        """Loads settings from CONFIG_FILE, creates/updates with defaults if needed."""
        config = configparser.ConfigParser()
        defaults = { 'API': {'lm_studio_base_url': 'http://localhost:1234/v1', 'fooocus_api_url': 'http://localhost:8888/v2/generation/text-to-image-with-ip'},
                     'Models': {'lm_studio_model_identifier': 'loaded-model-placeholder', 'fooocus_base_model': 'juggernautXL_v8Rundiffusion.safetensors'},
                     'Defaults': {'aspect_ratio': '896*1152', 'performance': 'Speed'} }
        config.read_dict(defaults)
        needs_saving = False
        try:
            if os.path.exists(CONFIG_FILE):
                if config.read(CONFIG_FILE): print(f"Loaded settings from {CONFIG_FILE}")
                else: print(f"Warning: Could not read {CONFIG_FILE}."); needs_saving = True
            else: print(f"{CONFIG_FILE} not found. Creating..."); needs_saving = True
        except configparser.Error as e: print(f"Error parsing {CONFIG_FILE}: {e}."); needs_saving = True
        # Ensure structure and save if needed
        for section, options in defaults.items():
            if not config.has_section(section): config.add_section(section); needs_saving = True
            for option, value in options.items():
                if not config.has_option(section, option): config.set(section, option, value); needs_saving = True
        if needs_saving: self._save_config(config, initial_save=True)
        return config

    def _save_config(self, config_object=None, initial_save=False):
        """Saves the current config object to CONFIG_FILE."""
        config_to_save = config_object if config_object else self._config
        try:
            with open(CONFIG_FILE, 'w') as configfile: config_to_save.write(configfile)
            print(f"Settings saved to {CONFIG_FILE}")
            if not initial_save:
                print("NOTE: Backend modules will use new settings on next call.")
                self.update_status("Settings saved successfully.")
        except Exception as e: print(f"Error writing {CONFIG_FILE}: {e}"); tkinter.messagebox.showerror("Save Error", f"Could not write settings:\n{e}", parent=self)


    def _initialize_database(self):
        try: db_manager.init_db(); return True
        except Exception as e: tkinter.messagebox.showerror("Database Error", f"DB Init Failed: {e}"); return False

    def _create_menu(self):
        """Creates the main application menu."""
        self.menu_bar = Menu(self)
        self.configure(menu=self.menu_bar) # Use CTk configure method
        file_menu = Menu(self.menu_bar, tearoff=0); self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Settings...", command=self.open_settings_window)
        file_menu.add_separator(); file_menu.add_command(label="Export Storyboard...", command=self.handle_export)
        file_menu.add_separator(); file_menu.add_command(label="Exit", command=self.handle_exit)
        help_menu = Menu(self.menu_bar, tearoff=0); self.menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def open_settings_window(self):
        """Opens the settings dialog."""
        if hasattr(self, 'settings_win') and self.settings_win is not None and self.settings_win.winfo_exists(): self.settings_win.focus()
        else: self.settings_win = SettingsWindow(self, self._config, self._save_config) # Pass correct config and save callback

    def show_about(self):
        tkinter.messagebox.showinfo("About Storyboard Studio Pro", f"{APP_NAME}\n\nAI Storyboard Generator\n(c) 2024", parent=self)

    def _create_main_widgets(self):
        """Creates the main column widgets using functions from main_window_ui."""
        self.grid_columnconfigure(0, weight=1, minsize=320); self.grid_columnconfigure(1, weight=2, minsize=420); self.grid_columnconfigure(2, weight=3, minsize=520)
        self.grid_rowconfigure(0, weight=1); self.grid_rowconfigure(1, weight=0)
        # Create columns - functions attach necessary widgets to self
        main_ui.create_input_column(self, self)
        main_ui.create_scenes_column(self, self)
        main_ui.create_output_column(self, self)
        main_ui.create_status_bar(self, self)
        self._set_placeholder_image_text("Select a scene to generate an image") # Initial placeholder

    # --- UI Helper Methods ---
    def update_status(self, message):
        print(f"STATUS: {message}")
        if hasattr(self, 'status_label') and self.status_label: self.after(0, lambda: self.status_label.configure(text=message))

    def _set_placeholder_image_text(self, text):
        """Recreates the image label with placeholder text."""
        if not hasattr(self, 'image_container_frame') or not self.image_container_frame.winfo_exists(): return
        if hasattr(self, 'image_label') and self.image_label is not None and self.image_label.winfo_exists():
            self.image_label.destroy(); self.update_idletasks()
        self.displayed_ctk_image = None; gc.collect()
        placeholder_font = getattr(self, 'placeholder_font', ctk.CTkFont(size=14, slant="italic"))
        self.image_label = ctk.CTkLabel(self.image_container_frame, text=text, text_color="gray50", font=placeholder_font, corner_radius=3)
        self.image_label.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

    def _show_loading_indicator(self, container):
        if container == self.image_container_frame:
             if not hasattr(self, 'image_progress_bar'): return
             self._set_placeholder_image_text("")
             self.image_progress_bar.grid(row=0, column=0, padx=60, pady=120, sticky="ew")
             self.image_progress_bar.start()

    def _hide_loading_indicator(self):
        if hasattr(self, 'image_progress_bar') and self.image_progress_bar:
            self.image_progress_bar.stop(); self.image_progress_bar.grid_forget()

    def _clear_scene_list_ui(self):
        if hasattr(self, 'scene_scrollable_frame') and self.scene_scrollable_frame:
            for widget in self.scene_scrollable_frame.winfo_children(): widget.destroy()
        self.scene_cards.clear()

    def _reset_ui_for_new_story(self):
        """Resets UI state for new scene generation, clears prompt cache."""
        selected_card = self.scene_cards.get(self.selected_scene_id) if hasattr(self, 'selected_scene_id') and self.selected_scene_id else None
        if selected_card and selected_card.winfo_exists(): selected_card.set_selected(False)

        self._clear_scene_list_ui()
        self.scenes_data = []
        self.selected_scene_id = None
        self.prompt_generation_cache.clear() # NEW: Clear prompt cache
        print("Cleared prompt generation cache.")
        self._set_placeholder_image_text("Image will appear here")
        self._clear_prompt_textbox()
        if hasattr(self, 'scene_scrollable_frame'):
            self.no_scenes_label = ctk.CTkLabel(self.scene_scrollable_frame, text="Generating scenes...", font=self.placeholder_font, text_color="gray")
            self.no_scenes_label.pack(pady=30, padx=10)

    def _clear_prompt_textbox(self):
        if hasattr(self, 'prompt_textbox') and self.prompt_textbox:
            self.prompt_textbox.configure(state="normal"); self.prompt_textbox.delete("1.0", "end"); self.prompt_textbox.configure(state="disabled")

    def _update_prompt_display(self, prompt_text):
        """Safely updates the prompt textbox and makes it editable."""
        if hasattr(self, 'prompt_textbox') and self.prompt_textbox:
            self.prompt_textbox.configure(state="normal") # Make editable
            self.prompt_textbox.delete("1.0", "end")
            if not isinstance(prompt_text, str): prompt_text = str(prompt_text) if prompt_text is not None else ""
            self.prompt_textbox.insert("1.0", prompt_text)
            # Keep editable

    def _update_button_states(self):
        """Updates enabled/disabled state of action buttons."""
        gen_prompt_enabled, regen_prompt_enabled, gen_image_enabled, regen_image_enabled = False, False, False, False
        if self.selected_scene_id:
            current_prompt = self.prompt_textbox.get("1.0", "end-1c").strip() if hasattr(self, 'prompt_textbox') else ""
            prompt_exists_and_valid = bool(current_prompt) and current_prompt != PROMPT_NOT_GENERATED_TEXT
            if not prompt_exists_and_valid: gen_prompt_enabled = True
            if self.selected_scene_id: regen_prompt_enabled = True
            if prompt_exists_and_valid: gen_image_enabled = True; regen_image_enabled = True

        # Schedule UI updates safely
        if hasattr(self, 'generate_prompt_button'): self.after(0, lambda: self.generate_prompt_button.configure(state="normal" if gen_prompt_enabled else "disabled"))
        if hasattr(self, 'regenerate_prompt_button'): self.after(0, lambda: self.regenerate_prompt_button.configure(state="normal" if regen_prompt_enabled else "disabled"))
        if hasattr(self, 'generate_image_button'): self.after(0, lambda: self.generate_image_button.configure(state="normal" if gen_image_enabled else "disabled"))
        if hasattr(self, 'regenerate_image_button'): self.after(0, lambda: self.regenerate_image_button.configure(state="normal" if regen_image_enabled else "disabled"))

    def _handle_error(self, title, message, is_fatal=False):
        """Centralized error handling."""
        full_message = f"{title}: {message}"; print(f"ERROR: {full_message}")
        self.after(0, lambda t=title, m=message: tkinter.messagebox.showerror(t, m, parent=self))
        self.update_status(f"Error: {message[:100]}")
        self._hide_loading_indicator()
        # Re-enable base buttons safely
        if hasattr(self, 'generate_scenes_button'): self.after(0, lambda: self.generate_scenes_button.configure(state="normal"))
        if hasattr(self, 'export_button'): self.after(0, lambda: self.export_button.configure(state="normal" if self.scenes_data else "disabled"))
        if hasattr(self, 'prompt_textbox'): self.after(0, lambda: self.prompt_textbox.configure(state="normal"))
        self._update_button_states()


    # --- Backend Interaction & Threading ---
    def run_in_thread(self, target_func, *args):
        """Starts a function in a thread with error handling."""
        def thread_wrapper(*a, **kw):
            thread_name = threading.current_thread().name
            try: print(f"--- Thread {thread_name} started ---"); target_func(*a, **kw)
            except Exception as e: print(f"--- Uncaught Exception in Thread {thread_name} ---"); print(traceback.format_exc()); self.after(0, self._handle_error, "Thread Error", f"Unexpected error: {e}")
            finally:
                 # Safely reset buttons
                 if hasattr(self, 'generate_scenes_button'): self.after(0, lambda: self.generate_scenes_button.configure(state="normal"))
                 if hasattr(self, 'export_button'): self.after(0, lambda: self.export_button.configure(state="normal" if self.scenes_data else "disabled"))
                 if hasattr(self, 'prompt_textbox'): self.after(0, lambda: self.prompt_textbox.configure(state="normal"))
                 self.after(0, self._update_button_states)
                 print(f"--- Thread {thread_name} finished ---")
        thread = threading.Thread(target=thread_wrapper, args=args, daemon=True, name=f"{target_func.__name__}_Thread")
        thread.start()

    # --- Event Handlers ---
    def handle_generate_scenes(self):
        story_text = self.story_textbox.get("1.0", "end-1c").strip()
        if not story_text: tkinter.messagebox.showwarning("Input Error", "Please enter a story.", parent=self); return
        self.update_status("Requesting scene generation...")
        # Disable buttons safely
        for btn_name in ['generate_scenes_button', 'export_button', 'generate_prompt_button', 'regenerate_prompt_button', 'generate_image_button', 'regenerate_image_button']:
             if hasattr(self, btn_name): getattr(self, btn_name).configure(state="disabled")
        self._reset_ui_for_new_story() # Clears UI and resets state including prompt cache
        self.run_in_thread(self._generate_scenes_task, story_text)

    def _generate_scenes_task(self, story_text):
        story_id = db_manager.add_story(story_text)
        if story_id is None: self.after(0, self._handle_error, "DB Error", "Failed to save story.", True); return
        self.current_story_id = story_id
        self.after(0, lambda: self.update_status("Loading LLM & generating scenes..."))
        scene_descriptions = llm_interface.generate_scenes(story_text)
        self.after(0, self._process_scene_generation_results, scene_descriptions)

    def _process_scene_generation_results(self, scene_descriptions):
        self._clear_scene_list_ui()
        success_count = 0
        if scene_descriptions is None:
            self._handle_error("LLM Error", "Failed to generate scenes.")
            self.no_scenes_label = ctk.CTkLabel(self.scene_scrollable_frame, text="Scene generation failed.", font=self.placeholder_font, text_color="orange"); self.no_scenes_label.pack(pady=30, padx=10)
        elif not scene_descriptions:
            self.update_status("LLM ran but no scenes parsed/returned.")
            self.no_scenes_label = ctk.CTkLabel(self.scene_scrollable_frame, text="No scenes returned/parsed.", font=self.placeholder_font, text_color="orange"); self.no_scenes_label.pack(pady=30, padx=10)
        else:
            temp_scenes_data = []
            for i, desc in enumerate(scene_descriptions):
                scene_num = i + 1
                try:
                    scene_id = db_manager.add_scene(self.current_story_id, scene_num, desc)
                    if scene_id:
                        success_count += 1
                        card = SceneCard(master=self.scene_scrollable_frame, scene_id=scene_id, scene_num=scene_num, scene_desc=desc, select_command=self.handle_scene_selection, delete_command=self.handle_delete_scene)
                        card.pack(fill="x", padx=5, pady=(0, 7))
                        self.scene_cards[scene_id] = card
                        temp_scenes_data.append({'id': scene_id, 'number': scene_num, 'description': desc, 'image_prompt': None, 'negative_prompt': None, 'image_path': None})
                    else: print(f"Warning: add_scene returned None for Scene {scene_num}.")
                except Exception as e: print(f"Error saving Scene {scene_num}: {e}"); traceback.print_exc(); tkinter.messagebox.showwarning("DB Warning", f"Failed to save Scene {scene_num}.", parent=self)
            self.scenes_data = temp_scenes_data
            if success_count == 0 and len(scene_descriptions) > 0:
                 self.update_status("Generated scenes, but failed to save any to DB.")
                 self.no_scenes_label = ctk.CTkLabel(self.scene_scrollable_frame, text="Failed to save scenes.", font=self.placeholder_font, text_color="orange"); self.no_scenes_label.pack(pady=30, padx=10)
            elif success_count > 0:
                 self.update_status(f"Generated {success_count} scenes. Loading thumbnails...")
                 self.after(100, self._load_initial_thumbnails)
        # Re-enable base buttons
        if hasattr(self, 'generate_scenes_button'): self.generate_scenes_button.configure(state="normal")
        if hasattr(self, 'export_button'): self.export_button.configure(state="normal" if self.scenes_data else "disabled")
        self._update_button_states()

    def _load_initial_thumbnails(self):
        """Iterates through scene data, updates thumbnails and status on cards."""
        print("Loading initial thumbnails and statuses...")
        loaded_count = 0
        if not self.scenes_data: return
        for scene_data in self.scenes_data:
            scene_id = scene_data.get('id')
            if not scene_id or scene_id not in self.scene_cards: continue
            card = self.scene_cards[scene_id]
            image_path, prompt_text = scene_data.get('image_path'), scene_data.get('image_prompt')
            db_needs_check = (image_path is None or prompt_text is None)
            db_scene = None
            if db_needs_check:
                db_scene = db_manager.get_scene_by_id(scene_id)
                if db_scene:
                    if image_path is None: image_path = db_scene.get('image_path');
                    if image_path: scene_data['image_path'] = image_path
                    if prompt_text is None: prompt_text = db_scene.get('image_prompt');
                    if prompt_text is not None: scene_data['image_prompt'] = prompt_text
            status = "default"; prompt_valid = prompt_text is not None and prompt_text != PROMPT_NOT_GENERATED_TEXT; image_valid = image_path and isinstance(image_path, str) and os.path.exists(image_path)
            if image_valid: status = "image_done"
            elif prompt_valid: status = "prompt_done"
            self.after(0, lambda c=card, p=image_path if image_valid else None, s=status: self._update_card_ui_safe(c, p, s)) # Schedule UI update
            if image_valid: loaded_count += 1
        print(f"Finished loading {loaded_count} initial thumbnails.")
        status_msg = f"Loaded {len(self.scenes_data)} scenes." + (f" Found {loaded_count} thumbnails." if loaded_count else "") + " Select a scene."
        self.after(100, lambda msg=status_msg: self.update_status(msg))

    def _update_card_ui_safe(self, card_widget, image_path, status):
         """Safely updates card UI elements if the widget still exists."""
         if card_widget and card_widget.winfo_exists():
             card_widget.update_thumbnail(image_path)
             card_widget.update_status_indicator(status)

    def handle_scene_selection(self, scene_id):
        """Handles clicking on a scene card to select it."""
        if scene_id == self.selected_scene_id: return
        print(f"Scene card selected, ID: {scene_id}")
        # Update Visual Selection
        if self.selected_scene_id and self.selected_scene_id in self.scene_cards:
            if self.scene_cards[self.selected_scene_id].winfo_exists(): self.scene_cards[self.selected_scene_id].set_selected(False)
        new_card = self.scene_cards.get(scene_id)
        if new_card and new_card.winfo_exists(): new_card.set_selected(True)
        self.selected_scene_id = scene_id
        # Load Data (Cache > DB)
        prompt_text, image_path, scene_num = PROMPT_NOT_GENERATED_TEXT, None, "?"
        db_scene = None; scene_data = next((s for s in self.scenes_data if s['id'] == scene_id), None)
        if scene_data:
            scene_num = scene_data.get('number', '?'); prompt_text, image_path = scene_data.get('image_prompt'), scene_data.get('image_path')
            db_needs_check = (prompt_text is None or image_path is None)
            if db_needs_check:
                db_scene = db_manager.get_scene_by_id(scene_id)
                if db_scene:
                    if prompt_text is None: prompt_text = db_scene.get('image_prompt');
                    if prompt_text is not None: scene_data['image_prompt'] = prompt_text
                    if image_path is None: image_path = db_scene.get('image_path');
                    if image_path: scene_data['image_path'] = image_path
            prompt_text = prompt_text if prompt_text is not None else PROMPT_NOT_GENERATED_TEXT
        else: # DB Fallback
             db_scene = db_manager.get_scene_by_id(scene_id)
             if db_scene: prompt_text, image_path, scene_num = db_scene.get('image_prompt', PROMPT_NOT_GENERATED_TEXT), db_scene.get('image_path'), db_scene.get('number', '?')
             else: prompt_text = "Error loading details."
        # Update UI
        self._update_prompt_display(prompt_text) # Makes editable
        valid_image_path = image_path if image_path and isinstance(image_path, str) and os.path.exists(image_path) else None
        status = "default"; prompt_valid = bool(prompt_text) and prompt_text != PROMPT_NOT_GENERATED_TEXT and "Error" not in prompt_text; image_valid = valid_image_path is not None
        if image_valid: status = "image_done"
        elif prompt_valid: status = "prompt_done"
        if new_card and new_card.winfo_exists(): self._update_card_ui_safe(new_card, valid_image_path, status) # Update selected card UI
        if valid_image_path: self.display_image(valid_image_path); self.update_status(f"Scene {scene_num} selected. Image loaded.")
        else:
            if image_path and not valid_image_path: print(f"Path invalid/missing: {image_path}")
            placeholder = "Generate image" if prompt_valid else "Generate prompt -> Generate image"
            self._set_placeholder_image_text(placeholder); self.update_status(f"Scene {scene_num} selected. Ready.")
        self._update_button_states()


    # --- Generate/Regenerate Prompt Handlers ---
    def handle_generate_prompt(self): self._initiate_prompt_generation("Generating prompt...")
    def handle_regenerate_prompt(self): self._initiate_prompt_generation("Regenerating prompt...")

    def _initiate_prompt_generation(self, status_message):
        if not self.selected_scene_id: tkinter.messagebox.showwarning("Select Error", "Select scene.", parent=self); return
        if not self.current_story_id: tkinter.messagebox.showerror("Internal Error", "No story context.", parent=self); return
        self.update_status(status_message)
        self.generate_prompt_button.configure(state="disabled"); self.regenerate_prompt_button.configure(state="disabled")
        self.generate_image_button.configure(state="disabled"); self.regenerate_image_button.configure(state="disabled")
        self.generate_scenes_button.configure(state="disabled"); self.export_button.configure(state="disabled")
        self.prompt_textbox.configure(state="disabled")
        card = self.scene_cards.get(self.selected_scene_id)
        if card and card.winfo_exists(): card.show_generating_indicator(True)
        current_scene_data = next((s for s in self.scenes_data if s['id'] == self.selected_scene_id), None)
        if not current_scene_data: self._handle_error("Internal Error", "Selected scene data missing."); return
        current_scene_num = current_scene_data.get('number', '?'); current_scene_desc = current_scene_data.get('description', '')
        prev_scene_num, prev_scene_desc, prev_scene_prompt = None, None, None
        if current_scene_num != '?' and current_scene_num > 1:
            target_prev_num = current_scene_num - 1
            prev_scene_data = next((s for s in self.scenes_data if s.get('number') == target_prev_num), None)
            if prev_scene_data:
                prev_scene_num, prev_scene_desc = prev_scene_data.get('number'), prev_scene_data.get('description')
                prev_scene_prompt = prev_scene_data.get('image_prompt')
                if prev_scene_prompt is None: prev_db_scene = db_manager.get_scene_by_id(prev_scene_data['id']); prev_scene_prompt = prev_db_scene.get('image_prompt') if prev_db_scene else None
                print(f"  Context: Prev Scene {prev_scene_num}. Prompt available: {prev_scene_prompt is not None}")
            else: print(f"  Context: Prev scene {target_prev_num} not found.")
        else: print("  Context: First scene.")
        key_elements_text = self.key_elements_textbox.get("1.0", "end-1c").strip()
        if key_elements_text.startswith("e.g.:\nProtagonist:"): key_elements_text = ""
        self.run_in_thread(self._generate_prompt_task, self.current_story_id, self.selected_scene_id, current_scene_desc, current_scene_num, key_elements_text, prev_scene_num, prev_scene_desc, prev_scene_prompt)

    # --- CORRECTED _generate_prompt_task ---
    def _generate_prompt_task(self, story_id, scene_id, scene_description, scene_number,
                              key_elements_text, prev_scene_num, prev_scene_desc, prev_scene_prompt):
        """Background task: Generates image prompt + negative using LLM with context, checks cache first."""
        # --- Check Cache ---
        cache_key = (scene_id, scene_description, key_elements_text, prev_scene_num, prev_scene_desc, prev_scene_prompt)
        if cache_key in self.prompt_generation_cache:
            print(f"Cache HIT for scene {scene_id} prompt generation.")
            main_prompt, negative_prompt = self.prompt_generation_cache[cache_key]
            self.after(0, self._process_prompt_generation_result, scene_id, main_prompt, negative_prompt, scene_number)
            return # Stop execution, use cached data
        else:
            print(f"Cache MISS for scene {scene_id} prompt generation. Calling LLM.")

        # --- Proceed with LLM call if not cached ---
        story_data = db_manager.get_story_by_id(story_id)
        if not story_data: self.after(0, self._handle_error, "DB Error", "Could not get story."); return
        story_text = story_data['story_text']
        self.after(0, lambda: self.update_status(f"Loading LLM for Scene {scene_number} prompt..."))
        # Pass ALL arguments to the llm_interface function
        main_prompt, negative_prompt = llm_interface.generate_image_prompt(
            story_text, scene_description, key_elements_text,
            prev_scene_num, prev_scene_desc, prev_scene_prompt, scene_number
        )
        # --- Store in Cache on Success ---
        if main_prompt is not None:
             self.prompt_generation_cache[cache_key] = (main_prompt, negative_prompt)
             print(f"Stored result in cache for scene {scene_id}.")
        # --- ------------------------- ---
        self.after(0, self._process_prompt_generation_result, scene_id, main_prompt, negative_prompt, scene_number)
    # --- END CORRECTION ---

    def _process_prompt_generation_result(self, scene_id, main_prompt, negative_prompt, scene_number):
        """Handles LLM prompt result in main UI thread."""
        card_to_update = self.scene_cards.get(scene_id)
        if card_to_update and card_to_update.winfo_exists(): card_to_update.show_generating_indicator(False)

        prompt_status = "default"
        if main_prompt is None:
            self._handle_error("LLM Error", f"Failed to generate prompt for Scene {scene_number}.")
            if self.selected_scene_id == scene_id: self.after(0, lambda: self.prompt_textbox.configure(state="normal"))
        else:
            self.update_status(f"Prompt generated/regenerated for Scene {scene_number}.")
            self._update_prompt_display(main_prompt) # Makes editable
            success = db_manager.update_scene_prompt(scene_id, main_prompt)
            if success:
                scene_data = next((s for s in self.scenes_data if s['id'] == scene_id), None)
                if scene_data: scene_data['image_prompt'], scene_data['negative_prompt'] = main_prompt, negative_prompt; print(f"Scene {scene_number} prompts saved.")
                prompt_status = "prompt_done"
            else: print(f"Warning: Failed to save prompt for Scene {scene_number} to DB."); tkinter.messagebox.showwarning("DB Warning", "Generated prompt, but failed to save it.", parent=self); prompt_status = "default"

        if card_to_update and card_to_update.winfo_exists(): self._update_card_ui_safe(card_to_update, None, prompt_status) # Update card status only
        if hasattr(self, 'generate_scenes_button'): self.generate_scenes_button.configure(state="normal")
        if hasattr(self, 'export_button'): self.export_button.configure(state="normal" if self.scenes_data else "disabled")
        if hasattr(self, 'prompt_textbox'): self.prompt_textbox.configure(state="normal") # Ensure editable
        self._update_button_states()


    # --- Image Generation Handlers ---
    def handle_generate_image(self): self._initiate_image_generation("Starting image generation...")
    def handle_regenerate_image(self): self._initiate_image_generation("Starting image regeneration...")

    def _initiate_image_generation(self, status_message):
        if not self.selected_scene_id: tkinter.messagebox.showwarning("Select Error", "Select scene.", parent=self); return
        prompt_text = self.prompt_textbox.get("1.0", "end-1c").strip()
        if not prompt_text or prompt_text == PROMPT_NOT_GENERATED_TEXT: tkinter.messagebox.showerror("Input Error", "Generate/enter prompt first.", parent=self); return
        self.update_status(status_message)
        self.generate_image_button.configure(state="disabled"); self.regenerate_image_button.configure(state="disabled")
        self.generate_prompt_button.configure(state="disabled"); self.regenerate_prompt_button.configure(state="disabled")
        self.generate_scenes_button.configure(state="disabled"); self.export_button.configure(state="disabled")
        self.prompt_textbox.configure(state="disabled")
        card = self.scene_cards.get(self.selected_scene_id)
        if card and card.winfo_exists(): card.show_generating_indicator(True)
        self._show_loading_indicator(self.image_container_frame)
        self.run_in_thread(self._generate_image_task, self.selected_scene_id, prompt_text)

    def _generate_image_task(self, scene_id, image_prompt): # image_prompt is main prompt
        scene_data = next((s for s in self.scenes_data if s['id'] == scene_id), None)
        scene_number = scene_data.get('number', '?') if scene_data else '?'
        negative_prompt = scene_data.get('negative_prompt', '') if scene_data else ''
        if not negative_prompt: print("Warning: Negative prompt cache miss. Using default empty.")
        story_id = self.current_story_id
        if not story_id: raise ValueError("No current_story_id for image generation.")
        self.after(0, lambda: self.update_status(f"Calling Fooocus for Scene {scene_number}... (Uses VRAM!)"))
        timestamp = int(time.time())
        output_filename = os.path.join(ASSETS_DIR, f"story_{story_id}_scene_{scene_id}_ts_{timestamp}.png")
        success = image_generator.generate_image(image_prompt, negative_prompt, output_filename) # Pass both prompts
        self.after(0, self._handle_image_generation_result, success, output_filename, scene_id, scene_number)

    def _handle_image_generation_result(self, success, image_path, scene_id, scene_number):
        card_to_update = self.scene_cards.get(scene_id)
        if card_to_update and card_to_update.winfo_exists(): card_to_update.show_generating_indicator(False) # Hide card indicator
        self._hide_loading_indicator() # Hide main indicator
        if hasattr(self, 'prompt_textbox'): self.prompt_textbox.configure(state="normal") # Re-enable prompt editing

        final_status = "default"
        valid_image_path = image_path if success and image_path and os.path.exists(image_path) else None

        if valid_image_path:
            print(f"Image successful, saving path: {image_path}")
            db_success = db_manager.update_scene_image_path(scene_id, image_path)
            if db_success:
                scene_data = next((s for s in self.scenes_data if s['id'] == scene_id), None)
                if scene_data: scene_data['image_path'] = image_path; print(f"Scene {scene_number} image path saved.")
                final_status = "image_done"
            else: print(f"Warning: Failed to save image path for Scene {scene_number} to DB."); tkinter.messagebox.showwarning("DB Warning", "Generated image, but failed to save path.", parent=self); final_status = "prompt_done"
            self.display_image(valid_image_path); self.update_status(f"Image for Scene {scene_number} generated successfully!")
            if card_to_update and card_to_update.winfo_exists(): self.after(50, lambda c=card_to_update, p=valid_image_path, s=final_status: self._update_card_ui_safe(c, p, s))
        else:
            reason = "Check Fooocus logs." if not success else "File not found after generation."
            self._handle_error("Image Generation Error", f"Failed for Scene {scene_number}. {reason}")
            self._set_placeholder_image_text("Image generation failed")
            scene_data = next((s for s in self.scenes_data if s.get('id') == scene_id), None)
            prompt_was_valid = scene_data and scene_data.get('image_prompt') and scene_data.get('image_prompt') != PROMPT_NOT_GENERATED_TEXT
            final_status = "prompt_done" if prompt_was_valid else "default"
            if card_to_update and card_to_update.winfo_exists(): self.after(50, lambda c=card_to_update, s=final_status: self._update_card_ui_safe(c, None, s)) # Clear thumb, set status

        # Update status indicator again directly if card still exists (handled by _update_card_ui_safe now)
        if hasattr(self, 'generate_scenes_button'): self.generate_scenes_button.configure(state="normal")
        if hasattr(self, 'export_button'): self.export_button.configure(state="normal" if self.scenes_data else "disabled")
        self._update_button_states()


    def display_image(self, image_path):
        """Recreates label, loads, resizes, displays image."""
        try:
            if not os.path.exists(image_path): raise FileNotFoundError(f"Not found: {image_path}")
            print(f"Displaying image: {image_path}")
            self.image_container_frame.update_idletasks()
            c_width, c_height = self.image_container_frame.winfo_width(), self.image_container_frame.winfo_height()
            if c_width <= 1: c_width = MAX_IMAGE_DISPLAY_WIDTH
            if c_height <= 1: c_height = int(c_width * 1.3)

            pil_image = Image.open(image_path)
            w, h = pil_image.size;
            if w <= 0 or h <= 0: raise ValueError("Invalid image dimensions")
            aspect = w / h; target_w, target_h = max(1, c_width - 10), max(1, c_height - 10); cont_aspect = target_w / (target_h or 1)
            if aspect > cont_aspect: new_w, new_h = target_w, int(target_w / aspect)
            else: new_h, new_w = target_h, int(target_h * aspect)
            new_w, new_h = max(1, int(new_w)), max(1, int(new_h))
            print(f"Resizing image to: {new_w}x{new_h}")

            resized = pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
            new_img = ctk.CTkImage(light_image=resized, dark_image=resized, size=(new_w, new_h))

            # Recreate label
            if hasattr(self, 'image_label') and self.image_label is not None and self.image_label.winfo_exists():
                self.image_label.destroy(); self.update_idletasks()
            self.image_label = ctk.CTkLabel(self.image_container_frame, text="", corner_radius=3, image=new_img)
            self.image_label.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
            self.displayed_ctk_image = new_img # Update reference

            print(f"Displayed: {os.path.basename(image_path)}")
        except Exception as e:
            print(f"ERROR during display_image: {e}"); print(traceback.format_exc())
            self._set_placeholder_image_text(f"Error displaying image:\n{type(e).__name__}")
            self.update_status(f"Error displaying image.")

    # --- Scene Deletion Handler ---
    def handle_delete_scene(self, scene_id_to_delete, scene_num_to_delete):
        """Handles the delete button click on a scene card."""
        print(f"Delete requested for Scene {scene_num_to_delete} (ID: {scene_id_to_delete})")
        confirm = tkinter.messagebox.askyesno("Confirm Delete", f"Delete Scene {scene_num_to_delete} permanently?", parent=self)
        if not confirm: print("Delete cancelled."); return

        self.update_status(f"Deleting Scene {scene_num_to_delete}...")
        deleted_from_db = db_manager.delete_scene(scene_id_to_delete) # Assumes function exists

        if not deleted_from_db: self._handle_error("Database Error", f"Failed to delete Scene {scene_num_to_delete} from DB."); return
        print(f"Scene {scene_id_to_delete} deleted from database.")

        card_to_remove = self.scene_cards.pop(scene_id_to_delete, None)
        if card_to_remove and card_to_remove.winfo_exists(): card_to_remove.destroy()
        else: print(f"Warning: Could not find UI card for deleted scene {scene_id_to_delete}.")

        self.scenes_data = [s for s in self.scenes_data if s.get('id') != scene_id_to_delete] # Remove from cache

        if self.selected_scene_id == scene_id_to_delete: # Reset selection if needed
            self.selected_scene_id = None;
            self._clear_prompt_textbox(); self._set_placeholder_image_text("Select a scene")

        self.update_status(f"Scene {scene_num_to_delete} deleted.")
        self.export_button.configure(state="normal" if self.scenes_data else "disabled") # Update export button state
        self._update_button_states() # Update buttons

    # --- Export Handler ---
    def handle_export(self):
        """Handles the 'Export Storyboard' button click."""
        if not self.scenes_data: tkinter.messagebox.showwarning("Export Error", "No scenes to export.", parent=self); return
        if not self.current_story_id: tkinter.messagebox.showerror("Export Error", "No story context.", parent=self); return

        export_dir = filedialog.askdirectory(title="Select Export Directory", parent=self)
        if not export_dir: self.update_status("Export cancelled."); return

        story_export_folder = os.path.join(export_dir, f"storyboard_{self.current_story_id}")
        try: os.makedirs(story_export_folder, exist_ok=True)
        except OSError as e: tkinter.messagebox.showerror("Export Error", f"Cannot create dir:\n{story_export_folder}\n{e}", parent=self); return

        self.update_status(f"Exporting storyboard to {story_export_folder}...")
        # Disable buttons during export
        if hasattr(self,'generate_scenes_button'): self.generate_scenes_button.configure(state="disabled")
        if hasattr(self,'export_button'): self.export_button.configure(state="disabled")
        if hasattr(self,'generate_prompt_button'): self.generate_prompt_button.configure(state="disabled")
        if hasattr(self,'regenerate_prompt_button'): self.regenerate_prompt_button.configure(state="disabled")
        if hasattr(self,'generate_image_button'): self.generate_image_button.configure(state="disabled")
        if hasattr(self,'regenerate_image_button'): self.regenerate_image_button.configure(state="disabled")

        self.run_in_thread(self._export_task, list(self.scenes_data), story_export_folder) # Pass copy

    def _export_task(self, scenes_to_export, export_folder):
        """Background task to export scenes."""
        exported_files, skipped_images, errors = 0, 0, 0
        try:
            scenes_from_db = db_manager.get_scenes_for_story(self.current_story_id) # Get fresh data
            if not scenes_from_db:
                raise Exception("No scenes found in database for current story.")

            for db_scene_data in scenes_from_db:
                scene_num = db_scene_data.get('number', 0)
                scene_id = db_scene_data.get('id')
                if not scene_id:
                    continue

                base_filename = f"{scene_num:03d}_scene_{scene_id}"
                txt_filename = os.path.join(export_folder, f"{base_filename}.txt")
                img_filename_out = os.path.join(export_folder, f"{base_filename}.png")

                try:  # Write Text File
                    desc = db_scene_data.get('description', 'N/A')
                    prompt = db_scene_data.get('image_prompt', 'N/A')
                    img_path_db = db_scene_data.get('image_path')
                    neg_prompt_cache = next((s.get('negative_prompt', 'N/A') for s in scenes_to_export if s.get('id') == scene_id), 'N/A')

                    with open(txt_filename, 'w', encoding='utf-8') as f:
                        f.write(f"Scene: {scene_num}\n\nDescription:\n{desc}\n\n")
                        f.write(f"Image Prompt:\n{prompt}\n\n")
                        f.write(f"Negative Prompt:\n{neg_prompt_cache}\n\n")
                        f.write(f"Original Path: {img_path_db or 'N/A'}\n")
                    exported_files += 1
                except Exception as e:
                    print(f"Error writing text for Scene {scene_num}: {e}")
                    errors += 1
                    try:
                        with open(txt_filename, 'w') as f:
                            f.write(f"Error exporting Text: {e}")
                    except Exception:
                        pass
                    continue

                # Copy Image File
                if img_path_db and os.path.exists(img_path_db):
                    try:
                        shutil.copy2(img_path_db, img_filename_out)
                        exported_files += 1
                    except Exception as e:
                        print(f"Error copying image for Scene {scene_num}: {e}")
                        errors += 1
                        try:
                            with open(txt_filename, 'a', encoding='utf-8') as f:
                                f.write(f"\nError copying image: {e}")
                        except Exception:
                            pass
                else:
                    print(f"Skipping image export for Scene {scene_num}: Path '{img_path_db}' missing/invalid.")
                    skipped_images += 1
                    try:
                        with open(txt_filename, 'a', encoding='utf-8') as f:
                            f.write(f"\nImage not found/generated.")
                    except Exception:
                        pass
# Note: The remaining part of the original function (status updates, button re-enabling,
# and the outer except/finally blocks) was not included in the provided snippet.
# If you provide the full function, I can ensure the indentation is correct for the entire block.


            # Final Status
            status = f"Export complete: {exported_files} files written"
            if skipped_images > 0: status += f", {skipped_images} images skipped"
            if errors > 0: status += f", {errors} errors."
            self.after(0, lambda msg=status: self.update_status(msg))
            if errors == 0: self.after(0, lambda fold=export_folder: tkinter.messagebox.showinfo("Export Complete", f"Exported to:\n{fold}", parent=self))
            elif errors > 0: self.after(0, lambda fold=export_folder: tkinter.messagebox.showwarning("Export Complete (with errors)", f"Export finished with errors.\nCheck console logs.\nFiles saved to:\n{fold}", parent=self))

        except Exception as e: self.after(0, self._handle_error, "Export Error", f"Unexpected error: {e}")
        finally: # Re-enable buttons
            if hasattr(self, 'export_button'): self.after(0, lambda: self.export_button.configure(state="normal" if self.scenes_data else "disabled"))
            if hasattr(self, 'generate_scenes_button'): self.after(0, lambda: self.generate_scenes_button.configure(state="normal"))
            self.after(0, self._update_button_states)

    # --- Clear DB and Exit Handlers ---
    def handle_clear_database(self):
        """Asks for confirmation and clears the database and UI."""
        confirm = tkinter.messagebox.askyesno("Confirm Clear Data", "WARNING!\n\nDelete all stories and scenes from 'storyboard.db'?\n\nThis cannot be undone.", icon='warning', parent=self)
        if not confirm: self.update_status("Clear data cancelled."); return

        print("User confirmed database clear.")
        self.update_status("Clearing database and resetting application...")
        # Disable buttons immediately
        for btn_name in ['generate_scenes_button', 'export_button', 'generate_prompt_button', 'regenerate_prompt_button', 'generate_image_button', 'regenerate_image_button']:
             if hasattr(self, btn_name): getattr(self, btn_name).configure(state="disabled")

        # Reset Internal State
        self.current_story_id = None; self.scenes_data = []; self.selected_scene_id = None; self.scene_cards.clear(); self.prompt_generation_cache.clear()

        # Clear UI Elements
        if hasattr(self, 'story_textbox'): self.story_textbox.delete("1.0", "end")
        if hasattr(self, 'key_elements_textbox'): self.key_elements_textbox.delete("1.0", "end"); self.key_elements_textbox.insert("1.0", "e.g.:\nProtagonist: ...")
        self._reset_ui_for_new_story() # Call reset which handles most UI clearing now
        self._clear_prompt_textbox(); self._set_placeholder_image_text("Enter a story and generate scenes")
        if hasattr(self, 'no_scenes_label') and self.no_scenes_label.winfo_exists(): self.no_scenes_label.configure(text="Enter a new story to begin.") # Update placeholder

        # Delete and Reinitialize Database File
        db_file = db_manager.DB_FILE
        db_cleared = False
        try:
            if os.path.exists(db_file): os.remove(db_file); print("Database file deleted.")
            else: print("Database file not found, skipping deletion.")
            print("Re-initializing database..."); db_manager.init_db(); db_cleared = True; print("Database re-initialized.")
        except OSError as e: print(f"Error deleting database file: {e}"); self._handle_error("File Error", f"Could not delete database file:\n{db_file}\n{e}")
        except Exception as e: print(f"Error re-initializing database: {e}"); self._handle_error("Database Error", f"Could not re-initialize database:\n{e}")

        if db_cleared: self.update_status("Database cleared. Ready for a new story.")
        else: self.update_status("Database clear failed. Check logs.")

        # Reset buttons to initial state
        if hasattr(self,'generate_scenes_button'): self.generate_scenes_button.configure(state="normal")
        if hasattr(self,'export_button'): self.export_button.configure(state="disabled")
        self._update_button_states()

    def handle_exit(self):
        """Closes the application window."""
        print("Exit requested by user.")
        self.update_status("Exiting...")
        self.destroy()


# --- Application Entry Point ---
if __name__ == "__main__":
    # Ensure assets directory exists
    if not os.path.exists(ASSETS_DIR):
        try: os.makedirs(ASSETS_DIR); print(f"Created '{ASSETS_DIR}' directory.")
        except OSError as e: print(f"Warning: Could not create '{ASSETS_DIR}': {e}")

    print(f"Starting {APP_NAME}...")
    app = StoryboardApp()
    app.mainloop() # Start the UI event loop