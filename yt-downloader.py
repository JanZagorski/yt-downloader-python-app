import tkinter as tk
from tkinter import ttk, messagebox
import subprocess

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
    run_command(cmd)

def download_video():
    url = url_entry.get()
    if not url:
        messagebox.showerror("Błąd", "Podaj URL!")
        return

    cmd = [
        "yt-dlp",
        "-f", "bv+ba/bestvideo+bestaudio",
        "--merge-output-format", "mp4",
        url
    ]
    run_command(cmd)

def run_command(cmd):
    try:
        subprocess.run(cmd, check=True)
        messagebox.showinfo("Sukces", "Pobrano!")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Błąd", f"Błąd pobierania:\n{e}")

# GUI setup
root = tk.Tk()
root.title("YouTube Downloader - yt-dlp GUI")
root.geometry("400x250")

tk.Label(root, text="Wklej link do YouTube:").pack(pady=5)
url_entry = tk.Entry(root, width=50)
url_entry.pack()

# MP3 Quality dropdown
tk.Label(root, text="Wybierz jakość MP3:").pack(pady=5)
quality_var = tk.StringVar(value="192K")
quality_dropdown = ttk.Combobox(root, textvariable=quality_var, values=["160K", "192K", "256K"])
quality_dropdown.pack()

# Buttons
tk.Button(root, text="Pobierz jako MP3", command=download_mp3).pack(pady=10)
tk.Button(root, text="Pobierz jako Video (MP4, 4K)", command=download_video).pack(pady=5)

root.mainloop()
