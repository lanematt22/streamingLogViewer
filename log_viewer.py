import os
import threading
import time
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox

class LogViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Streaming Log Viewer")
        self.geometry("800x600")

        self.text_area = scrolledtext.ScrolledText(self, state='disabled', wrap=tk.WORD)
        self.text_area.pack(expand=True, fill='both')

        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

        self.stop_event = threading.Event()
        self.thread = None
        self.log_file = None

    def open_file(self):
        filepath = filedialog.askopenfilename(title="Select log file", filetypes=[("Log files", "*.log *.txt"), ("All files", "*.*")])
        if not filepath:
            return
        self.start_stream(filepath)

    def start_stream(self, filepath):
        self.stop_stream()
        try:
            f = open(filepath, 'r', encoding='utf-8', errors='replace')
        except OSError as e:
            messagebox.showerror("Error", f"Failed to open file: {e}")
            return
        self.log_file = f
        self.text_area.configure(state='normal')
        self.text_area.delete(1.0, tk.END)
        self.text_area.configure(state='disabled')
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._follow, daemon=True)
        self.thread.start()
        self.title(f"Streaming Log Viewer - {os.path.basename(filepath)}")

    def stop_stream(self):
        if self.thread and self.thread.is_alive():
            self.stop_event.set()
            self.thread.join(timeout=1)
        if self.log_file:
            try:
                self.log_file.close()
            except Exception:
                pass
            self.log_file = None

    def _follow(self):
        f = self.log_file
        # Read existing contents first
        for line in f:
            self._append_text(line)
        while not self.stop_event.is_set():
            where = f.tell()
            line = f.readline()
            if not line:
                time.sleep(0.5)
                f.seek(where)
            else:
                self._append_text(line)

    def _append_text(self, text):
        self.text_area.configure(state='normal')
        self.text_area.insert(tk.END, text)
        self.text_area.see(tk.END)
        self.text_area.configure(state='disabled')

    def quit(self):
        self.stop_stream()
        super().quit()

if __name__ == "__main__":
    app = LogViewer()
    app.mainloop()
