import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from image_grid import ImageGrid
from clip_model import ClipModel
from image_handler import ImageHandler
from dres_sender import DresSender #WAS USED DURING COMPETITION TO SEND IMAGES TO THE SERVER TO CHECK, DID NOT INCLUDE THIS CLASS
import torch
import os

# Suppress macOS warnings
os.environ['TK_SILENCE_DEPRECATION'] = '1'


class SearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NDBI045 Search System")

        # Initialize components
        self.model = ClipModel()
        self.images = ImageHandler()
        self.dres = DresSender()

        # State management
        self.current_mode = "browse"
        self.current_position = 0
        self.page_size = 20
        self.current_results = []
        self.search_page = 0

        # Create GUI elements first
        self._create_widgets()

        # Then load initial data
        self.load_database_page()

    def _create_widgets(self):
        """Initialize all GUI components"""
        # Search panel
        self.search_frame = ttk.Frame(self.root, padding=10)
        self.search_frame.pack(fill=tk.X)

        self.search_entry = ttk.Entry(self.search_frame, width=50)
        self.search_entry.pack(side=tk.LEFT, padx=5)

        self.search_btn = ttk.Button(
            self.search_frame,
            text="Search",
            command=self.on_search
        )
        self.search_btn.pack(side=tk.LEFT, padx=5)

        # Image grid
        self.grid = ImageGrid(
            self.root,
            rows=4,
            cols=5,
            img_width=200,
            img_height=150,
            click_callback=self.on_image_click
        )
        self.grid.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Navigation controls
        self.nav_frame = ttk.Frame(self.root)
        self.nav_frame.pack(pady=10)

        self.prev_btn = ttk.Button(
            self.nav_frame,
            text="<< Previous",
            command=self.prev_page
        )
        self.prev_btn.pack(side=tk.LEFT, padx=5)

        self.next_btn = ttk.Button(
            self.nav_frame,
            text="Next >>",
            command=self.next_page
        )
        self.next_btn.pack(side=tk.LEFT, padx=5)

        # Status label
        self.status_label = ttk.Label(self.nav_frame, text="")
        self.status_label.pack(side=tk.LEFT, padx=10)

    def update_status(self):
        """Update navigation status display"""
        if self.current_mode == "browse":
            total = len(self.images)
            self.status_label.config(
                text=f"Database: {self.current_position + 1}-{min(self.current_position + self.page_size, total)} of {total}"
            )
        else:
            total = len(self.current_results)
            start = self.search_page * self.page_size + 1
            end = min((self.search_page + 1) * self.page_size, total)
            self.status_label.config(
                text=f"Search results: {start}-{end} of {total}"
            )

    def load_database_page(self):
        """Load images from main database"""
        self.current_mode = "browse"
        indices = list(range(self.current_position, self.current_position + self.page_size))
        self.display_images(indices)

    def display_images(self, indices):
        """Display images in grid from given indices"""
        for i in range(self.page_size):
            self.grid[i] = None

        for i, idx in enumerate(indices):
            if idx >= len(self.images):
                break
            try:
                self.grid[i] = self.images[idx]
            except Exception as e:
                print(f"Error loading image {idx}: {str(e)}")

        self.update_status()

    def next_page(self):
        """Navigate to next page"""
        if self.current_mode == "browse":
            self.current_position += self.page_size
            if self.current_position >= len(self.images):
                self.current_position = 0
            self.load_database_page()
        else:
            if (self.search_page + 1) * self.page_size < len(self.current_results):
                self.search_page += 1
                start = self.search_page * self.page_size
                self.display_images(self.current_results[start:start + self.page_size])

    def prev_page(self):
        """Navigate to previous page"""
        if self.current_mode == "browse":
            self.current_position -= self.page_size
            if self.current_position < 0:
                self.current_position = len(self.images) - self.page_size
            self.load_database_page()
        else:
            if self.search_page > 0:
                self.search_page -= 1
                start = self.search_page * self.page_size
                self.display_images(self.current_results[start:start + self.page_size])

    def on_search(self):
        """Handle search button click"""
        query = self.search_entry.get()
        if not query:
            self.current_mode = "browse"
            self.load_database_page()
            return

        try:
            self.current_results = self.model.search(query).tolist()
            self.current_mode = "search"
            self.search_page = 0
            self.display_images(self.current_results[:self.page_size])
        except Exception as e:
            messagebox.showerror("Search Error", str(e))

    def on_image_click(self, grid_idx):
        """Handle image click - show detail window"""
        try:
            if self.current_mode == "browse":
                idx = self.current_position + grid_idx
            else:
                idx = self.current_results[self.search_page * self.page_size + grid_idx]

            # Create detail window
            detail_win = tk.Toplevel(self.root)
            detail_win.title("Image Details")

            # Display clicked image
            img_path = self.images[idx]
            img = Image.open(img_path)
            img.thumbnail((300, 300))
            img_tk = ImageTk.PhotoImage(img)
            img_label = tk.Label(detail_win, image=img_tk)
            img_label.image = img_tk
            img_label.pack(pady=10)

            # Create buttons
            btn_frame = ttk.Frame(detail_win)
            btn_frame.pack(pady=10)

            ttk.Button(btn_frame, text="Send to Server",
                       command=lambda: self.send_to_server(idx, detail_win)).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Find Similar",
                       command=lambda: self.find_similar(idx, detail_win)).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Close",
                       command=detail_win.destroy).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def send_to_server(self, idx, window):
        """Handle server submission"""
        try:
            success, msg = self.dres.send_result(self.images[idx])
            if success:
                messagebox.showinfo("Submission", "Image submitted successfully!", parent=window)
            else:
                messagebox.showwarning("Submission", f"Submission failed: {msg}", parent=window)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=window)

    def find_similar(self, idx, window):
        """Find and display similar images"""
        try:
            similar_indices = self.model.similarity(idx).tolist()
            self.current_results = similar_indices
            self.current_mode = "search"
            self.search_page = 0
            self.display_images(similar_indices[:self.page_size])
            window.destroy()
            messagebox.showinfo("Search Complete", "Showing similar images!", parent=self.root)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=window)


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.configure("TButton", padding=6, font=('Helvetica', 10))
    style.configure("TEntry", font=('Helvetica', 12))
    app = SearchApp(root)
    root.geometry("1200x800")
    root.mainloop()
