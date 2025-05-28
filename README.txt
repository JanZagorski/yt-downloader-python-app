YouTube Downloader - yt-dlp GUI (Python + Tkinter)

A simple graphical application that allows downloading YouTube videos and audio using yt-dlp.

Features:
- Download MP3 audio with selectable quality (160K, 192K, 256K)
- Download MP4 video in the best available quality
- Easy-to-use graphical interface built with Tkinter

Requirements:
- Python 3.7 or higher
- yt-dlp:
    pip install yt-dlp
- ffmpeg (required for audio/video processing):

  Windows (with Chocolatey):
    choco install ffmpeg

  Ubuntu/Debian:
    sudo apt install ffmpeg

  Arch Linux:
    sudo pacman -S ffmpeg

  macOS:
    brew install ffmpeg

- Tkinter (usually included with Python, but if missing on Linux):

  Ubuntu/Debian:
    sudo apt install python3-tk

  Arch Linux:
    sudo pacman -S tk

How to Run:
Simply run the Python script:
    python downloader.py

Legal Notice:
Downloading copyrighted content from YouTube may violate its terms of service.
Use this application responsibly and only for content you have the right to download.

License:
Copyright (c) 2025 Jan Zagorski
