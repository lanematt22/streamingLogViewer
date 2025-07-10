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

        control_frame = tk.Frame(self)
        control_frame.pack(fill='x', side='bottom')
        self.pause_button = tk.Button(control_frame, text="Pause", command=self.toggle_pause)
        self.pause_button.pack(side='right', padx=5, pady=5)

        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.thread = None
        self.log_file = None
        self.history_thread = None
        self.history_file = None
        self.history_pos = 0
        # Load roughly 100 recent lines first
        self.initial_lines = 100
        self.history_chunk_lines = 500
        self.filepath = None

    def open_file(self):
        filepath = filedialog.askopenfilename(title="Select log file", filetypes=[("Log files", "*.log *.txt"), ("All files", "*.*")])
        if not filepath:
            return
        self.start_stream(filepath)

    def start_stream(self, filepath):
        self.stop_stream()
        self.filepath = filepath
        try:
            initial_lines, self.history_pos, file_end = self._read_last_lines(filepath, self.initial_lines)
            self.log_file = open(filepath, 'r', encoding='utf-8', errors='replace')
            self.log_file.seek(file_end)
            self.history_file = open(filepath, 'rb')
            self.history_file.seek(self.history_pos)
        except OSError as e:
            messagebox.showerror("Error", f"Failed to open file: {e}")
            return
        self.text_area.configure(state='normal')
        self.text_area.delete(1.0, tk.END)
        self.text_area.configure(state='disabled')
        for line in initial_lines:
            self._insert_top(line)
        self.stop_event.clear()
        self.pause_event.clear()
        self.pause_button.config(text="Pause")
        self.thread = threading.Thread(target=self._follow, daemon=True)
        self.thread.start()
        self.history_thread = threading.Thread(target=self._load_history, daemon=True)
        self.history_thread.start()
        self.title(f"Streaming Log Viewer - {os.path.basename(filepath)}")

    def stop_stream(self):
        if self.thread and self.thread.is_alive():
            self.stop_event.set()
            self.thread.join(timeout=1)
        if self.history_thread and self.history_thread.is_alive():
            self.history_thread.join(timeout=1)
        if self.log_file:
            try:
                self.log_file.close()
            except Exception:
                pass
            self.log_file = None
        if self.history_file:
            try:
                self.history_file.close()
            except Exception:
                pass
            self.history_file = None
        self.thread = None
        self.history_thread = None
        self.history_pos = 0
        self.filepath = None
        self.pause_event.clear()
        self.pause_button.config(text="Pause")

    def toggle_pause(self):
        if not self.thread:
            return
        if self.pause_event.is_set():
            self.pause_event.clear()
            self.pause_button.config(text="Pause")
        else:
            self.pause_event.set()
            self.pause_button.config(text="Resume")

    def _follow(self):
        f = self.log_file
        while not self.stop_event.is_set():
            if self.pause_event.is_set():
                time.sleep(0.1)
                continue
            where = f.tell()
            line = f.readline()
            if not line:
                time.sleep(0.5)
                f.seek(where)
            else:
                self._insert_top(line)

    def _insert_top(self, text):
        self.text_area.configure(state='normal')
        self.text_area.insert('1.0', text)
        self.text_area.yview_moveto(0)
        self.text_area.configure(state='disabled')

    def _insert_bottom(self, text):
        # Preserve the current view position while inserting at the end
        self.text_area.configure(state='normal')
        yview = self.text_area.yview()
        self.text_area.insert(tk.END, text)
        self.text_area.yview_moveto(yview[0])
        self.text_area.configure(state='disabled')

    def _read_last_lines(self, filepath, num_lines=100, chunk_size=4096):
        try:
            with open(filepath, 'rb') as f:
                f.seek(0, os.SEEK_END)
                file_size = f.tell()
                data = b''
                pos = file_size
                lines = []
                while len(lines) <= num_lines and pos > 0:
                    read_size = min(chunk_size, pos)
                    pos -= read_size
                    f.seek(pos)
                    data = f.read(read_size) + data
                    lines = data.splitlines(keepends=True)
                last_lines = lines[-num_lines:] if len(lines) >= num_lines else lines
                start_pos = file_size - sum(len(l) for l in last_lines)
                decoded = [l.decode('utf-8', errors='replace') for l in reversed(last_lines)]
                return decoded, start_pos, file_size
        except Exception:
            return [], 0, 0

    def _read_prev_lines(self, f, end_pos, num_lines=100, chunk_size=4096):
        if end_pos <= 0:
            return [], 0
        data = b''
        pos = end_pos
        lines = []
        while len(lines) <= num_lines and pos > 0:
            read_size = min(chunk_size, pos)
            pos -= read_size
            f.seek(pos)
            data = f.read(read_size) + data
            lines = data.splitlines(keepends=True)
        if not lines:
            return [], 0
        selected = lines[-num_lines:] if len(lines) >= num_lines else lines
        start_pos = end_pos - sum(len(l) for l in selected)
        decoded = [l.decode('utf-8', errors='replace') for l in reversed(selected)]
        return decoded, start_pos

    def _load_history(self):
        if not self.history_file:
            return
        f = self.history_file
        pos = self.history_pos
        while pos > 0 and not self.stop_event.is_set():
            if self.pause_event.is_set():
                time.sleep(0.1)
                continue
            lines, pos = self._read_prev_lines(f, pos, self.history_chunk_lines)
            self.history_pos = pos
            for line in lines:
                self._insert_bottom(line)
            time.sleep(0.01)

    def quit(self):
        self.stop_stream()
        super().quit()

if __name__ == "__main__":
    app = LogViewer()
    app.mainloop()
