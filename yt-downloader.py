import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import json

downloads = []

def start_download(cmd, title):
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        current = {"title": title, "progress": "0%", "total": "", "downloaded": "", "speed": ""}
        downloads.append(current)
        update_download_list()

        for line in process.stdout:
            print(line.strip())  # Debugging output

            if "[download]" in line:
                if "Destination" in line:
                    current["title"] = line.strip().split("Destination: ")[-1]
                elif "%" in line:
                    try:
                        parts = line.strip().split()
                        current["progress"] = parts[1]
                        current["downloaded"] = parts[3]
                        current["total"] = parts[5]
                        current["speed"] = parts[7] if len(parts) >= 8 else ""
                    except IndexError:
                        pass
                    update_download_list()

        process.wait()
        update_download_list()

    except Exception as e:
        print(f"Błąd podczas pobierania: {e}")
        messagebox.showerror("Błąd", f"Wystąpił problem z pobieraniem:\n{e}")


def update_download_list():
    listbox.delete(0, tk.END)
    for d in downloads:
        listbox.insert(tk.END, f"{d['title']} | {d['progress']} | {d['downloaded']}/{d['total']} | {d['speed']}")

def download_mp3():
    url = url_entry.get()
    bitrate = quality_var.get()
    if not url:
        messagebox.showerror("Błąd", "Podaj URL!")
        return

    cmd = [
        "yt-dlp",
        "-x", "--audio-format", "mp3",
        "--audio-quality", bitrate,
        url
    ]
    threading.Thread(target=start_download, args=(cmd, url), daemon=True).start()

def download_video():
    url = url_entry.get()
    if not url:
        messagebox.showerror("Błąd", "Podaj URL!")
        return

    cmd = [
        "yt-dlp",
        "-f", "bv*[height=2160]+ba/bestvideo+bestaudio",
        "--merge-output-format", "mp4",
        url
    ]
    threading.Thread(target=start_download, args=(cmd, url), daemon=True).start()

# GUI setup
root = tk.Tk()
root.title("YouTube Downloader")
root.geometry("800x400")

frame_top = tk.Frame(root)
frame_top.pack(pady=10, padx=10, fill='x')

tk.Label(frame_top, text="Link YouTube:").grid(row=0, column=0, sticky="w")
url_entry = tk.Entry(frame_top, width=80)
url_entry.grid(row=0, column=1, padx=5)

# Buttons on the same row
button_frame = tk.Frame(frame_top)
button_frame.grid(row=0, column=2, padx=5)
tk.Button(button_frame, text="MP3", width=10, command=download_mp3).pack()
tk.Button(button_frame, text="Video (MP4, 4K)", width=15, command=download_video).pack()

# Quality
tk.Label(root, text="Wybierz jakość MP3:").pack()
quality_var = tk.StringVar(value="192K")
quality_dropdown = ttk.Combobox(root, textvariable=quality_var, values=["160K", "192K", "256K"], width=10)
quality_dropdown.pack()

# List of Downloads
tk.Label(root, text="Status pobierania:").pack(pady=(10, 0))
listbox = tk.Listbox(root, height=10, width=120)
listbox.pack(padx=10, pady=5, fill='both', expand=True)

root.mainloop()
