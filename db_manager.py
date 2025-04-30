# storyboard_app/db_manager.py
import sqlite3
import os
from datetime import datetime

DB_FILE = "storyboard.db"

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    # Return rows as dictionaries (makes accessing columns easier)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    print("Initializing database...")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Create stories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    story_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("Checked/Created 'stories' table.")

            # Create scenes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scenes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    story_id INTEGER NOT NULL,
                    scene_number INTEGER NOT NULL,
                    scene_description TEXT NOT NULL,
                    image_prompt TEXT,
                    image_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (story_id) REFERENCES stories (id)
                )
            """)
            print("Checked/Created 'scenes' table.")
            conn.commit() # Save changes
        print("Database initialization complete.")
    except sqlite3.Error as e:
        print(f"Database error during initialization: {e}")
        raise # Re-raise the exception to stop the app if DB fails

def add_story(story_text):
    """Adds a new story to the database and returns its ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO stories (story_text) VALUES (?)", (story_text,))
            conn.commit()
            story_id = cursor.lastrowid # Get the ID of the inserted row
            print(f"Added story with ID: {story_id}")
            return story_id
    except sqlite3.Error as e:
        print(f"Database error adding story: {e}")
        return None

def add_scene(story_id, scene_number, scene_description):
    """Adds a new scene linked to a story."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO scenes (story_id, scene_number, scene_description) VALUES (?, ?, ?)",
                (story_id, scene_number, scene_description)
            )
            conn.commit()
            scene_id = cursor.lastrowid
            print(f"Added scene {scene_number} for story {story_id} with scene ID: {scene_id}")
            return scene_id
    except sqlite3.Error as e:
        print(f"Database error adding scene: {e}")
        return None

def get_scenes_for_story(story_id):
    """Retrieves all scenes for a given story ID, ordered by scene number."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, scene_number, scene_description, image_prompt, image_path FROM scenes WHERE story_id = ? ORDER BY scene_number",
                (story_id,)
            )
            scenes = cursor.fetchall()
            # fetchall returns a list of Row objects (like dictionaries)
            return [dict(scene) for scene in scenes] if scenes else []
    except sqlite3.Error as e:
        print(f"Database error getting scenes: {e}")
        return [] # Return empty list on error

def get_story_by_id(story_id):
    """Retrieves the story text for a given story ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT story_text FROM stories WHERE id = ?", (story_id,))
            story = cursor.fetchone()
            return dict(story) if story else None
    except sqlite3.Error as e:
        print(f"Database error getting story: {e}")
        return None

def get_scene_by_id(scene_id):
    """Retrieves details for a specific scene ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scenes WHERE id = ?", (scene_id,))
            scene = cursor.fetchone()
            return dict(scene) if scene else None
    except sqlite3.Error as e:
        print(f"Database error getting scene details: {e}")
        return None

def update_scene_prompt(scene_id, image_prompt):
    """Updates the generated image prompt for a specific scene."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE scenes SET image_prompt = ? WHERE id = ?",
                (image_prompt, scene_id)
            )
            conn.commit()
            print(f"Updated image prompt for scene ID: {scene_id}")
            return True
    except sqlite3.Error as e:
        print(f"Database error updating scene prompt: {e}")
        return False

def update_scene_image_path(scene_id, image_path):
    """Updates the generated image file path for a specific scene."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE scenes SET image_path = ? WHERE id = ?",
                (image_path, scene_id)
            )
            conn.commit()
            print(f"Updated image path for scene ID: {scene_id}")
            return True
    except sqlite3.Error as e:
        print(f"Database error updating image path: {e}")
        return False

# --- Self-test (Optional: run this file directly to create the DB) ---
if __name__ == "__main__":
    print("Running DB Manager directly to initialize database...")
    if os.path.exists(DB_FILE):
         print(f"Database file '{DB_FILE}' already exists.")
    init_db()
    print("DB Manager self-test finished.")