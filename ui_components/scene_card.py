# storyboard_app/ui_components/scene_card.py
import customtkinter as ctk
from PIL import Image
import os
import gc

# --- Constants defined within the component ---
THUMBNAIL_WIDTH = 100
THUMBNAIL_HEIGHT = 65
COLOR_STATUS_DEFAULT = ("gray60", "gray40")
COLOR_STATUS_PROMPT_DONE = ("#e8e87a", "#b0b04c") # Yellowish
COLOR_STATUS_IMAGE_DONE = ("#7ae89f", "#4cb071") # Greenish
COLOR_CARD_SELECTED_BG = ("gray85", "gray18")
# --- -------------------------------------- ---


class SceneCard(ctk.CTkFrame):
    """
    Custom widget representing a single scene card in the scrollable list.
    Manages its own thumbnail, status indicator, and selection highlighting.
    """
    def __init__(self, master, scene_id, scene_num, scene_desc, select_command, delete_command, **kwargs):
        # Initialize the CTkFrame
        super().__init__(master, border_width=1, border_color="gray40", corner_radius=5, **kwargs)

        self.scene_id = scene_id
        self.scene_num = scene_num
        self.select_command = select_command # Callback function when card is selected
        self.delete_command = delete_command # Callback function for delete button

        self.ctk_thumbnail_ref = None # Holds reference to CTkImage to prevent garbage collection
        self.is_selected = False      # Tracks if the card is currently selected

        # Store default appearance for hover/selection effects
        self.default_fg_color = self.cget("fg_color")
        self.default_border_color = self.cget("border_color")
        self.default_border_width = self.cget("border_width")
        self.hover_fg_color = ctk.ThemeManager.theme.get("CTkFrame", {}).get("hover_color", ("gray75", "gray25")) # Safe theme access

        # --- Configure internal grid layout ---
        self.grid_columnconfigure(0, weight=1) # Text area expands
        self.grid_columnconfigure(1, weight=0) # Thumbnail column fixed width
        self.grid_columnconfigure(2, weight=0) # Actions/Status column fixed width

        # --- Create child widgets ---
        self._create_widgets(scene_num, scene_desc)

        # --- Bind mouse events ---
        self._bind_events()

        # Apply initial status indicator color
        self.update_status_indicator("default")

    def _create_widgets(self, scene_num, scene_desc):
        """Creates the internal widgets of the scene card."""
        # Frame for text content (ensures consistent padding)
        self.text_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.text_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(10, 5))
        self.text_frame.grid_columnconfigure(0, weight=1)

        # Scene Number Label
        self.num_label = ctk.CTkLabel(self.text_frame, text=f"Scene {scene_num}",
                                      font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        self.num_label.grid(row=0, column=0, pady=(5, 2), sticky="w")

        # Scene Description Textbox
        self.desc_box = ctk.CTkTextbox(self.text_frame, wrap="word", activate_scrollbars=False,
                                       font=("Segoe UI", 13), border_width=0, fg_color="transparent",
                                       height=10) # Start small, will try to resize
        self.desc_box.grid(row=1, column=0, pady=(0, 5), sticky="ew")
        self.desc_box.insert("1.0", scene_desc)
        self.desc_box.configure(state="disabled") # Read-only
        # Schedule initial height adjustment
        self.after(150, self._adjust_desc_box_height)

        # Thumbnail Label (placeholder initially)
        self.thumbnail_label = ctk.CTkLabel(self, text="", width=THUMBNAIL_WIDTH, height=THUMBNAIL_HEIGHT,
                                            fg_color=("gray80", "gray20"), corner_radius=3)
        self.thumbnail_label.grid(row=0, column=1, rowspan=2, padx=(0, 5), pady=5, sticky="nsew")

        # Frame for Actions (Delete) and Status Indicator
        self.action_status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_status_frame.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=(0, 10), pady=5)
        self.action_status_frame.grid_rowconfigure(0, weight=0) # Delete button top
        self.action_status_frame.grid_rowconfigure(1, weight=1) # Spacer (pushes status down)
        self.action_status_frame.grid_rowconfigure(2, weight=0) # Status bottom
        self.action_status_frame.grid_columnconfigure(0, weight=1) # Center content horizontally if needed

        # Delete Button
        self.delete_button = ctk.CTkButton(self.action_status_frame, text="X", width=28, height=28,
                                            command=self._on_delete,
                                            font=ctk.CTkFont(size=14, weight="bold"),
                                            fg_color="transparent", border_width=1, border_color=COLOR_STATUS_DEFAULT,
                                            text_color=COLOR_STATUS_DEFAULT, hover_color=("red", "darkred"))
        self.delete_button.grid(row=0, column=0, sticky="ne") # Top-right corner

        # Status Indicator Dot
        self.status_indicator = ctk.CTkFrame(self.action_status_frame, width=12, height=12,
                                             corner_radius=6, fg_color=COLOR_STATUS_DEFAULT[1], # Start with default dark color
                                             border_width=0)
        self.status_indicator.grid(row=2, column=0, sticky="se", pady=(0, 0)) # Bottom-right corner

        # Generating Indicator Label (initially hidden)
        self.generating_indicator = ctk.CTkLabel(self.action_status_frame, text=". . .",
                                                 font=ctk.CTkFont(size=18, weight="bold"),
                                                 text_color=("gray50", "gray60"))
        # This widget is placed/removed dynamically by show_generating_indicator

    def _bind_events(self):
        """Binds hover and click events to the card and relevant children."""
        # Command to execute on click (passed during initialization)
        click_command = lambda event: self.select_command(self.scene_id)

        # Bind click to non-button areas
        self.bind("<Button-1>", click_command)
        self.text_frame.bind("<Button-1>", click_command)
        self.num_label.bind("<Button-1>", click_command)
        self.desc_box.bind("<Button-1>", click_command)
        self.thumbnail_label.bind("<Button-1>", click_command)
        self.status_indicator.bind("<Button-1>", click_command)
        self.action_status_frame.bind("<Button-1>", click_command)

        # Bind hover events for visual feedback
        hover_widgets = [self, self.text_frame, self.num_label, self.desc_box,
                         self.thumbnail_label, self.status_indicator, self.action_status_frame]
        for widget in hover_widgets:
            widget.bind("<Enter>", self._on_enter, add='+')
            widget.bind("<Leave>", self._on_leave, add='+')

    def _on_delete(self):
        """Internal handler for the delete button, calls the provided command."""
        if self.delete_command:
            self.delete_command(self.scene_id, self.scene_num) # Pass scene details back to main app

    def _on_enter(self, event=None):
        """Handles mouse entering the card area."""
        if not self.is_selected: # Apply hover effect only if not selected
            self.configure(fg_color=self.hover_fg_color)

    def _on_leave(self, event=None):
        """Handles mouse leaving the card area."""
        if not self.is_selected: # Revert only if not selected
            self.configure(fg_color=self.default_fg_color)

    def set_selected(self, selected: bool):
        """Sets the visual state of the card (selected or not)."""
        self.is_selected = selected
        if selected:
            # Use theme's button color for border, and specific BG color
            highlight_border_color = ctk.ThemeManager.theme["CTkButton"]["fg_color"][1]
            self.configure(border_color=highlight_border_color, border_width=2, fg_color=COLOR_CARD_SELECTED_BG)
        else:
            # Revert to default appearance
            self.configure(border_color=self.default_border_color, border_width=self.default_border_width, fg_color=self.default_fg_color)

    def update_thumbnail(self, image_path):
        """Loads, resizes, and displays a thumbnail image."""
        if not self.thumbnail_label.winfo_exists(): return

        # Clear previous thumbnail reference first
        self.ctk_thumbnail_ref = None
        gc.collect()

        if image_path and os.path.exists(image_path):
            try:
                pil_image = Image.open(image_path)
                pil_image.thumbnail((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.Resampling.LANCZOS)
                ctk_thumb = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=pil_image.size)
                self.thumbnail_label.configure(image=ctk_thumb, text="")
                self.ctk_thumbnail_ref = ctk_thumb # Store new reference
            except Exception as e:
                print(f"Error creating thumbnail for {image_path}: {e}")
                self.thumbnail_label.configure(image=None, text="Err", font=ctk.CTkFont(size=10))
        else:
            # No valid image path, clear the thumbnail
            self.thumbnail_label.configure(image=None, text="")

    def update_status_indicator(self, status="default"):
        """Updates the color of the status indicator dot."""
        if not hasattr(self, 'status_indicator') or not self.status_indicator.winfo_exists(): return

        color = COLOR_STATUS_DEFAULT
        if status == "prompt_done": color = COLOR_STATUS_PROMPT_DONE
        elif status == "image_done": color = COLOR_STATUS_IMAGE_DONE
        self.status_indicator.configure(fg_color=color)

    def show_generating_indicator(self, show=True):
        """Shows or hides the '...' generating indicator."""
        if not self.action_status_frame.winfo_exists(): return

        if show:
            self.status_indicator.grid_forget() # Hide status dot
            self.generating_indicator.grid(row=2, column=0, sticky="se", pady=(0, 0))
        else:
            self.generating_indicator.grid_forget() # Hide '...'
            # Ensure status indicator is placed back correctly
            if hasattr(self, 'status_indicator') and self.status_indicator.winfo_exists():
                self.status_indicator.grid(row=2, column=0, sticky="se", pady=(0, 0))

    def _adjust_desc_box_height(self):
         """(Experimental) Tries to adjust textbox height based on content lines."""
         if not self.desc_box.winfo_exists(): return
         try:
             # This method is imperfect in Tkinter/CTk without complex font metric calculations
             # A simpler approximation: Count lines (\n) + estimate wrapping
             content = self.desc_box.get("1.0", "end-1c")
             lines = content.count('\n') + 1 # Start with explicit newlines

             # Estimate wrapped lines (very rough guess)
             # Assumes average char width and textbox width
             avg_char_width = 7 # Guess, depends heavily on font/OS
             widget_width = self.desc_box.winfo_width()
             if widget_width > 1: # Avoid division by zero if not rendered yet
                chars_per_line = max(1, widget_width // avg_char_width)
                estimated_wrap_lines = sum( (len(line) + chars_per_line -1) // chars_per_line for line in content.split('\n') )
                lines = max(lines, estimated_wrap_lines) # Use the larger estimate

             font_size = 13 # From definition
             line_height_multiplier = 1.5 # Approximate spacing
             padding = 10
             desired_height = int(lines * font_size * line_height_multiplier) + padding

             max_height = 150; min_height = 40
             final_height = max(min_height, min(desired_height, max_height))

             current_height = self.desc_box.cget("height")
             # Only configure if the change is noticeable to avoid excessive updates
             if abs(current_height - final_height) > 5:
                 # print(f"Adjusting height for scene {self.scene_num} to {final_height} ({lines} lines)")
                 self.desc_box.configure(height=final_height)

         except Exception as e:
             print(f"Error adjusting textbox height for scene {self.scene_num}: {e}")
             # Fallback to a default height if calculation fails
             if self.desc_box.winfo_exists(): self.desc_box.configure(height=70)