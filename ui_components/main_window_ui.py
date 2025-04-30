# storyboard_app/ui_components/main_window_ui.py
import customtkinter as ctk
from tkinter import Menu # Needed for menu creation
# Import ToolTip class assuming it's in the same directory or accessible
try:
    from .tooltips import ToolTip
except ImportError:
    print("Warning: ToolTip class not found in ui_components.tooltips. Tooltips will not be shown.")
    # Define a dummy ToolTip class if import fails, so the code doesn't crash
    class ToolTip:
        def __init__(self, widget, text): pass

def create_input_column(master, app_instance):
    """Creates and returns the frame for the input column (Column 1)."""
    frame = ctk.CTkFrame(master, corner_radius=5)
    frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
    # Configure rows to allow buttons at bottom
    frame.grid_rowconfigure(1, weight=1) # Story textbox expands
    frame.grid_rowconfigure(3, weight=1) # Key elements textbox expands
    frame.grid_rowconfigure(4, weight=10) # Spacer row pushes buttons down
    frame.grid_rowconfigure(5, weight=0) # Generate scenes btn
    frame.grid_rowconfigure(6, weight=0) # Export btn
    frame.grid_rowconfigure(7, weight=0) # Clear DB btn
    frame.grid_rowconfigure(8, weight=0) # Exit btn

    # --- Widgets ---
    ctk.CTkLabel(frame, text="1. Story Input", font=app_instance.title_font).grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")
    app_instance.story_textbox = ctk.CTkTextbox(frame, wrap="word", height=200, font=app_instance.label_font, border_width=1)
    app_instance.story_textbox.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="nsew")

    ctk.CTkLabel(frame, text="Key Elements (Optional)", font=app_instance.title_font).grid(row=2, column=0, padx=15, pady=(10, 5), sticky="w")
    app_instance.key_elements_textbox = ctk.CTkTextbox(frame, wrap="word", height=150, font=app_instance.label_font, border_width=1)
    app_instance.key_elements_textbox.insert("1.0", "e.g.:\nProtagonist: Name, brief appearance, clothing.\nSetting: Key location details, mood.")
    app_instance.key_elements_textbox.grid(row=3, column=0, padx=15, pady=(0, 10), sticky="nsew")
    ToolTip(app_instance.key_elements_textbox, "Describe key characters/settings here\nfor better visual consistency.")

    app_instance.generate_scenes_button = ctk.CTkButton(frame, text="Generate Scenes", command=app_instance.handle_generate_scenes, font=app_instance.label_font, height=35)
    app_instance.generate_scenes_button.grid(row=5, column=0, padx=15, pady=5, sticky="ew")
    ToolTip(app_instance.generate_scenes_button, "Generate scene descriptions from the\nstory using the configured LLM.")

    app_instance.export_button = ctk.CTkButton(frame, text="Export Storyboard", command=app_instance.handle_export, font=app_instance.label_font, height=35, fg_color=("SeaGreen", "DarkSeaGreen"))
    app_instance.export_button.grid(row=6, column=0, padx=15, pady=5, sticky="ew")
    ToolTip(app_instance.export_button, "Export generated images and text\nfor all scenes to a selected folder.")

    app_instance.clear_db_button = ctk.CTkButton(frame, text="Clear All Data", command=app_instance.handle_clear_database, font=app_instance.label_font, height=30, fg_color=("#db5454", "#a83a3a"), hover_color=("#b84040", "#8f2c2c"))
    app_instance.clear_db_button.grid(row=7, column=0, padx=15, pady=(15, 5), sticky="ew")
    ToolTip(app_instance.clear_db_button, "WARNING: Deletes all saved data!")

    app_instance.exit_button = ctk.CTkButton(frame, text="Exit Application", command=app_instance.handle_exit, font=app_instance.label_font, height=30, fg_color=("gray60", "gray40"), hover_color=("gray70", "gray25"))
    app_instance.exit_button.grid(row=8, column=0, padx=15, pady=(5, 10), sticky="ew")
    ToolTip(app_instance.exit_button, "Close the application.")

    return frame # Return the created frame

def create_scenes_column(master, app_instance):
    """Creates and returns the frame for the scenes column (Column 2)."""
    frame = ctk.CTkFrame(master, corner_radius=5)
    frame.grid(row=0, column=1, padx=5, pady=10, sticky="nsew")
    frame.grid_rowconfigure(1, weight=3); frame.grid_rowconfigure(3, weight=1); frame.grid_rowconfigure(4, weight=0)
    frame.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(frame, text="2. Scenes", font=app_instance.title_font).grid(row=0, column=0, columnspan=2, padx=15, pady=(10, 5), sticky="w")
    app_instance.scene_scrollable_frame = ctk.CTkScrollableFrame(frame, label_text="", corner_radius=3, fg_color="transparent")
    app_instance.scene_scrollable_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=0, sticky="nsew")
    app_instance.no_scenes_label = ctk.CTkLabel(app_instance.scene_scrollable_frame, text="Scenes will appear here...", font=app_instance.placeholder_font, text_color="gray")
    app_instance.no_scenes_label.pack(pady=30, padx=10)

    ctk.CTkLabel(frame, text="Selected Scene Prompt", font=app_instance.title_font).grid(row=2, column=0, columnspan=2, padx=15, pady=(15, 5), sticky="w")
    app_instance.prompt_textbox = ctk.CTkTextbox(frame, wrap="word", height=100, font=app_instance.label_font, state="disabled", fg_color=("gray85", "gray16"), border_width=1)
    app_instance.prompt_textbox.grid(row=3, column=0, columnspan=2, padx=15, pady=(0, 10), sticky="nsew")
    ToolTip(app_instance.prompt_textbox, "Displays/Edit the generated prompt.")

    # Frame for prompt buttons
    button_frame = ctk.CTkFrame(frame, fg_color="transparent"); button_frame.grid(row=4, column=0, columnspan=2, padx=15, pady=(5, 10), sticky="ew"); button_frame.grid_columnconfigure(0, weight=1); button_frame.grid_columnconfigure(1, weight=1)
    app_instance.generate_prompt_button = ctk.CTkButton(button_frame, text="Generate Prompt", command=app_instance.handle_generate_prompt, state="disabled", font=app_instance.label_font, height=35)
    app_instance.generate_prompt_button.grid(row=0, column=0, padx=(0, 5), sticky="ew"); ToolTip(app_instance.generate_prompt_button, "Generate prompt for selected scene.")
    app_instance.regenerate_prompt_button = ctk.CTkButton(button_frame, text="Regenerate Prompt", command=app_instance.handle_regenerate_prompt, state="disabled", font=app_instance.label_font, height=35, fg_color=("gray70", "gray30"))
    app_instance.regenerate_prompt_button.grid(row=0, column=1, padx=(5, 0), sticky="ew"); ToolTip(app_instance.regenerate_prompt_button, "Generate a NEW prompt for selected scene.")

    return frame # Return the created frame

def create_output_column(master, app_instance):
    """Creates and returns the frame for the output column (Column 3)."""
    frame = ctk.CTkFrame(master, corner_radius=5)
    frame.grid(row=0, column=2, padx=(5, 10), pady=10, sticky="nsew")
    frame.grid_rowconfigure(1, weight=1); frame.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(frame, text="3. Image Output", font=app_instance.title_font).grid(row=0, column=0, padx=15, pady=(10, 10), sticky="w")
    app_instance.image_container_frame = ctk.CTkFrame(frame, corner_radius=3, fg_color=("gray90", "gray10"))
    app_instance.image_container_frame.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="nsew"); app_instance.image_container_frame.grid_rowconfigure(0, weight=1); app_instance.image_container_frame.grid_columnconfigure(0, weight=1)
    # Note: Actual image label (self.image_label) is created/destroyed dynamically by _set_placeholder_image_text and display_image in main app
    app_instance.image_progress_bar = ctk.CTkProgressBar(app_instance.image_container_frame, indeterminate_speed=1.0, mode='indeterminate', height=10)

    # Frame for image buttons
    output_button_frame = ctk.CTkFrame(frame, fg_color="transparent"); output_button_frame.grid(row=2, column=0, padx=15, pady=(0, 10), sticky="ew"); output_button_frame.grid_columnconfigure(0, weight=1); output_button_frame.grid_columnconfigure(1, weight=1)
    app_instance.generate_image_button = ctk.CTkButton(output_button_frame, text="Generate Image", command=app_instance.handle_generate_image, state="disabled", font=app_instance.label_font, height=35)
    app_instance.generate_image_button.grid(row=0, column=0, padx=(0, 5), sticky="ew"); ToolTip(app_instance.generate_image_button, "Generate image using current prompt.")
    app_instance.regenerate_image_button = ctk.CTkButton(output_button_frame, text="Regenerate Image", command=app_instance.handle_regenerate_image, state="disabled", font=app_instance.label_font, height=35, fg_color=("gray70", "gray30"))
    app_instance.regenerate_image_button.grid(row=0, column=1, padx=(5, 0), sticky="ew"); ToolTip(app_instance.regenerate_image_button, "Generate NEW image using current prompt.")

    return frame # Return the created frame

def create_status_bar(master, app_instance):
    """Creates and returns the status bar frame."""
    frame = ctk.CTkFrame(master, height=25, corner_radius=0, border_width=1, border_color=("gray70", "gray30"))
    frame.grid(row=1, column=0, columnspan=3, padx=0, pady=0, sticky="ew")
    app_instance.status_label = ctk.CTkLabel(frame, text="", font=app_instance.small_font, anchor="w")
    app_instance.status_label.pack(side="left", padx=10, pady=2)
    return frame # Return the created frame

def create_main_menu(master, app_instance):
    """Creates and attaches the main application menu."""
    # 'master' here is the main CTk window (app_instance)
    menu_bar = Menu(master)
    master.configure(menu=menu_bar) # Use master's configure method

    # File Menu
    file_menu = Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Settings...", command=app_instance.open_settings_window)
    file_menu.add_separator()
    file_menu.add_command(label="Export Storyboard...", command=app_instance.handle_export)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=app_instance.handle_exit)

    # Help Menu (Optional)
    help_menu = Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(label="About", command=app_instance.show_about)

    return menu_bar # Return the menu bar object