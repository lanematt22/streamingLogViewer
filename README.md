# Streaming Log Viewer

This is a small GUI application for viewing log files as they are written. It is based on Python and Tkinter so it works on Windows with a standard Python installation.

## Features
* Select a log file from a file dialog.
* Display existing log content and automatically append new lines as they are written.
* Continue streaming until you select a new file or close the program.
* Pause and resume streaming so you can inspect the log without new lines
  shifting the view.

## Requirements
* Python 3.8 or newer (with Tkinter, included in standard Python installers).

## Running the Application
```
python log_viewer.py
```

## Building a Windows Executable
You can create a standalone Windows executable using [PyInstaller](https://pyinstaller.org/).
Install PyInstaller and build the exe:

```
pip install pyinstaller
pyinstaller --onefile --windowed log_viewer.py
```

The executable will be placed in the `dist` directory.

## Pausing Streaming
Use the **Pause** button at the bottom of the window to temporarily stop
reading the active log file. Click **Resume** to continue streaming from
the point where you paused.
