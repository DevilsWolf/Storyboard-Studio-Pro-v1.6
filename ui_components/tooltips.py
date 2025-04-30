import customtkinter as ctk

class ToolTip:
    """ Creates a tooltip for a given widget. """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.enter, add='+')
        self.widget.bind("<Leave>", self.leave, add='+')
        self.widget.bind("<ButtonPress>", self.leave, add='+')
        self.id = None
        self.x = 0
        self.y = 0

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(700, self.showtip)

    def unschedule(self):
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)

    def showtip(self):
        if self.tooltip_window:
            return

        # Calculate position
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 1

        # Create tooltip window
        self.tooltip_window = tw = ctk.CTkToplevel(self.widget)
        tw.wm_overrideredirect(True) # Remove window decorations
        tw.wm_geometry(f"+{x}+{y}") # Set position

        # Get colors from theme or use defaults
        try:
            fg = ctk.ThemeManager.theme["CTkToolTip"]["fg_color"]
            text_c = ctk.ThemeManager.theme["CTkToolTip"]["text_color"]
        except (KeyError, AttributeError):
            # Fallback colors if theme key is not found
            fg = ("#4c4c4c", "#343638") # Dark grey for light/dark mode
            text_c = ("#dce4ee", "#dce4ee") # Light grey/blueish

        # Create and pack label
        label = ctk.CTkLabel(tw, text=self.text, justify='left', fg_color=fg, text_color=text_c, corner_radius=3, font=ctk.CTkFont(size=10), padx=5, pady=3)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tooltip_window
        self.tooltip_window = None # Reset the reference
        if tw:
            try:
                # Check if the window still exists before destroying
                if tw.winfo_exists():
                    tw.destroy()
            except Exception:
                # Ignore errors during destruction
                pass