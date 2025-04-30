# storyboard_app/ui_components/settings_window.py
import customtkinter as ctk
import tkinter.messagebox
import traceback # Import traceback
from .tooltips import ToolTip # Import from sibling file

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, master, config, save_callback, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.config_ref = config # Reference to the actual config object
        self.save_callback = save_callback

        self.title("Settings")
        self.geometry("550x420")
        self.transient(master) # Keep window on top of parent
        self.grab_set() # Grab focus until window is closed

        # Get fonts from master or use defaults
        # Use self.master instead of just master if accessing attributes set on the app instance
        self.title_font = getattr(self.master, 'title_font', ctk.CTkFont(size=16, weight="bold"))
        self.label_font = getattr(self.master, 'label_font', ctk.CTkFont(size=13))

        self.grid_columnconfigure(1, weight=1)
        self._create_widgets()
        self._load_values()
        self.protocol("WM_DELETE_WINDOW", self.destroy) # Handle window close button

    def _create_widgets(self):
        """Creates widgets for the settings window."""
        row_index = 0

        # API Section
        api_label = ctk.CTkLabel(self, text="API Configuration", font=self.title_font)
        api_label.grid(row=row_index, column=0, columnspan=2, padx=20, pady=(10, 5), sticky="w")
        row_index += 1

        lm_url_label = ctk.CTkLabel(self, text="LM Studio URL:", anchor="w")
        lm_url_label.grid(row=row_index, column=0, padx=(20, 5), pady=5, sticky="w")
        self.lm_url_entry = ctk.CTkEntry(self, width=300)
        self.lm_url_entry.grid(row=row_index, column=1, padx=(0, 20), pady=5, sticky="ew")
        row_index += 1
        ToolTip(self.lm_url_entry, "Base URL for LM Studio's API (e.g., http://localhost:1234/v1)")

        fooocus_url_label = ctk.CTkLabel(self, text="Fooocus API URL:", anchor="w")
        fooocus_url_label.grid(row=row_index, column=0, padx=(20, 5), pady=5, sticky="w")
        self.fooocus_url_entry = ctk.CTkEntry(self, width=300)
        self.fooocus_url_entry.grid(row=row_index, column=1, padx=(0, 20), pady=5, sticky="ew")
        row_index += 1
        ToolTip(self.fooocus_url_entry, "URL for Fooocus API generation endpoint (e.g., http://localhost:8888/v2/generation/text-to-image-with-ip)")


        # Model Section
        model_label = ctk.CTkLabel(self, text="Model Configuration", font=self.title_font)
        model_label.grid(row=row_index, column=0, columnspan=2, padx=20, pady=(15, 5), sticky="w")
        row_index += 1

        lm_model_label = ctk.CTkLabel(self, text="LM Studio Model ID:", anchor="w")
        lm_model_label.grid(row=row_index, column=0, padx=(20, 5), pady=5, sticky="w")
        self.lm_model_entry = ctk.CTkEntry(self, width=300)
        self.lm_model_entry.grid(row=row_index, column=1, padx=(0, 20), pady=5, sticky="ew")
        row_index += 1
        ToolTip(self.lm_model_entry, "Identifier string for the model loaded in LM Studio (e.g., 'TheBloke/Llama-2-7B-Chat-GGUF')")

        fooocus_model_label = ctk.CTkLabel(self, text="Fooocus Base Model:", anchor="w")
        fooocus_model_label.grid(row=row_index, column=0, padx=(20, 5), pady=5, sticky="w")
        self.fooocus_model_entry = ctk.CTkEntry(self, width=300)
        self.fooocus_model_entry.grid(row=row_index, column=1, padx=(0, 20), pady=5, sticky="ew")
        row_index += 1
        ToolTip(self.fooocus_model_entry, "Filename of the base model used by Fooocus (e.g., 'juggernautXL_v8Rundiffusion.safetensors')")


        # Defaults Section
        defaults_label = ctk.CTkLabel(self, text="Generation Defaults", font=self.title_font)
        defaults_label.grid(row=row_index, column=0, columnspan=2, padx=20, pady=(15, 5), sticky="w")
        row_index += 1

        aspect_ratio_label = ctk.CTkLabel(self, text="Aspect Ratio:", anchor="w")
        aspect_ratio_label.grid(row=row_index, column=0, padx=(20, 5), pady=5, sticky="w")
        self.aspect_ratio_var = ctk.StringVar()
        aspect_ratios = ["896*1152", "1024*1024", "1152*896", "1344*768", "768*1344", "1536*640", "640*1536"] # Add more as needed
        self.aspect_ratio_menu = ctk.CTkOptionMenu(self, variable=self.aspect_ratio_var, values=aspect_ratios)
        self.aspect_ratio_menu.grid(row=row_index, column=1, padx=(0, 20), pady=5, sticky="ew")
        row_index += 1
        ToolTip(self.aspect_ratio_menu, "Default aspect ratio for generated images.")

        performance_label = ctk.CTkLabel(self, text="Performance:", anchor="w")
        performance_label.grid(row=row_index, column=0, padx=(20, 5), pady=5, sticky="w")
        self.performance_var = ctk.StringVar()
        perf_options = ["Speed", "Quality", "Extreme Speed"] # Match Fooocus options
        self.performance_menu = ctk.CTkOptionMenu(self, variable=self.performance_var, values=perf_options)
        self.performance_menu.grid(row=row_index, column=1, padx=(0, 20), pady=5, sticky="ew")
        row_index += 1
        ToolTip(self.performance_menu, "Default performance preset for image generation.")

        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=row_index, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="ew")
        button_frame.grid_columnconfigure((0, 1), weight=1) # Make buttons expand

        save_button = ctk.CTkButton(button_frame, text="Save & Close", command=self._save_and_close)
        save_button.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        cancel_button = ctk.CTkButton(button_frame, text="Cancel", command=self.destroy, fg_color="gray50", hover_color="gray40")
        cancel_button.grid(row=0, column=1, padx=(10, 0), sticky="ew")


    def _load_values(self):
        """Loads values from the config object into the widgets."""
        # Use get() with fallback to prevent errors if section/key doesn't exist yet
        self.lm_url_entry.insert(0, self.config_ref.get('API', 'lm_studio_base_url', fallback='http://localhost:1234/v1'))
        self.fooocus_url_entry.insert(0, self.config_ref.get('API', 'fooocus_api_url', fallback='http://localhost:8888/v2/generation/text-to-image-with-ip'))
        self.lm_model_entry.insert(0, self.config_ref.get('Models', 'lm_studio_model_identifier', fallback='loaded-model-placeholder'))
        self.fooocus_model_entry.insert(0, self.config_ref.get('Models', 'fooocus_base_model', fallback='juggernautXL_v8Rundiffusion.safetensors'))

        # For OptionMenus, use set()
        self.aspect_ratio_var.set(self.config_ref.get('Defaults', 'aspect_ratio', fallback='896*1152'))
        self.performance_var.set(self.config_ref.get('Defaults', 'performance', fallback='Speed'))


    def _save_and_close(self):
        """Saves values back to the referenced config object and calls main app's save."""
        print("Saving settings...")
        try:
            # Ensure sections exist before trying to set values
            for section in ['API', 'Models', 'Defaults']:
                if not self.config_ref.has_section(section):
                    self.config_ref.add_section(section)

            # Save values from entry widgets and option menus
            self.config_ref.set('API', 'lm_studio_base_url', self.lm_url_entry.get().strip())
            self.config_ref.set('API', 'fooocus_api_url', self.fooocus_url_entry.get().strip())
            self.config_ref.set('Models', 'lm_studio_model_identifier', self.lm_model_entry.get().strip())
            self.config_ref.set('Models', 'fooocus_base_model', self.fooocus_model_entry.get().strip())
            self.config_ref.set('Defaults', 'aspect_ratio', self.aspect_ratio_var.get())
            self.config_ref.set('Defaults', 'performance', self.performance_var.get())

            # Call the callback function provided by the main app to save the config to file
            self.save_callback()

            print("Settings saved.")
            self.destroy() # Close the settings window

        except Exception as e:
            print(f"Error saving settings: {e}")
            traceback.print_exc() # Print full traceback
            # Show error message to the user
            tkinter.messagebox.showerror("Save Error", f"Could not save settings:\n{e}", parent=self)