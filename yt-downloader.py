import tkinter as tk
from tkinter import ttk, messagebox, font
import threading
import subprocess
import json
import re
import os
import sys # Dla sys.stdout.encoding

# Globalny słownik do przechowywania informacji o pobieraniach
downloads_info = {}

def check_yt_dlp():
    try:
        subprocess.run(["yt-dlp", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Opóźnienie wyświetlenia messagebox, aby root był gotowy
        def show_error():
            messagebox.showerror("Błąd krytyczny", "yt-dlp nie jest zainstalowany lub nie ma go w PATH.\nZainstaluj yt-dlp, aby aplikacja działała poprawnie.")
        # Tkinter może jeszcze nie być w pełni zainicjowany, więc używamy after
        tk._default_root.after(100, show_error) if tk._default_root else print("Błąd krytyczny: yt-dlp nie znaleziono (konsola)")
        return False

class YouTubeDownloaderApp:
    def __init__(self, root_window):
        self.root = root_window
        if not check_yt_dlp():
            # Jeśli check_yt_dlp zwróci False, to opóźniony messagebox powinien się pokazać
            # a my niszczymy okno, jeśli zostało już utworzone (lub nie tworzymy reszty GUI)
            self.root.after(200, self.root.destroy) # Dajmy czas na messagebox
            return

        self.root.title("Pro Downloader")
        self.root.geometry("950x650") # Nieco większe okno

        self.current_mode = "light" # Domyślny tryb
        self.define_colors() # Definiujemy palety kolorów

        self.style = ttk.Style()
        self.setup_styles() # Inicjalne ustawienie stylów (jasny)

        # Główny kontener
        self.main_frame = ttk.Frame(self.root, padding="20 20 20 10", style="Main.TFrame")
        self.main_frame.pack(expand=True, fill=tk.BOTH)

        # Górny pasek (URL i przełącznik trybu)
        top_bar_frame = ttk.Frame(self.main_frame, style="Main.TFrame")
        top_bar_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(top_bar_frame, text="Link YouTube:", style="Header.TLabel").pack(side=tk.LEFT, padx=(0, 10))
        self.url_entry = ttk.Entry(top_bar_frame, width=60, style="Modern.TEntry")
        self.url_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, ipady=6)
        self.setup_entry_context_menu()

        self.mode_toggle_button = ttk.Button(
            top_bar_frame,
            text="🌙", # Domyślnie ikona księżyca (przejdź na ciemny)
            command=self.toggle_mode,
            style="ModeToggle.TButton",
            width=3
        )
        self.mode_toggle_button.pack(side=tk.LEFT, padx=(15, 0))


        # Sekcja kontrolek (jakość, przyciski)
        controls_frame = ttk.Frame(self.main_frame, style="Main.TFrame")
        controls_frame.pack(fill=tk.X, pady=(0, 20))

        mp3_quality_frame = ttk.Frame(controls_frame, style="Main.TFrame")
        mp3_quality_frame.pack(side=tk.LEFT, padx=(0, 30), fill=tk.Y, anchor=tk.N)
        ttk.Label(mp3_quality_frame, text="Jakość MP3:", style="Small.TLabel").pack(anchor=tk.W, pady=(0,2))
        self.quality_var = tk.StringVar(value="192K")
        quality_values = ["128K", "160K", "192K", "256K", "320K (Najlepsza)"]
        # Użycie tk.OptionMenu stylizowanego przez ttk dla lepszego wyglądu niż Combobox w niektórych motywach
        self.quality_dropdown = ttk.Combobox(
            mp3_quality_frame,
            textvariable=self.quality_var,
            values=quality_values,
            width=18, # Zwiększona szerokość
            state="readonly",
            style="Modern.TCombobox"
        )
        self.quality_dropdown.set("192K")
        self.quality_dropdown.pack(anchor=tk.W, ipady=4)
        
        buttons_subframe = ttk.Frame(controls_frame, style="Main.TFrame")
        buttons_subframe.pack(side=tk.RIGHT, fill=tk.Y, anchor=tk.N)

        self.download_mp3_button = ttk.Button(buttons_subframe, text="Pobierz MP3", command=self.trigger_mp3_download, style="Accent.TButton", width=18)
        self.download_mp3_button.pack(side=tk.LEFT, padx=(0,10), ipady=6)

        self.download_video_button = ttk.Button(buttons_subframe, text="Pobierz Video (MP4)", command=self.trigger_video_download, style="Accent.TButton", width=22)
        self.download_video_button.pack(side=tk.LEFT, ipady=6)


        # Sekcja listy pobierania
        downloads_label_frame = ttk.Frame(self.main_frame, style="Main.TFrame")
        downloads_label_frame.pack(fill=tk.X, pady=(0,5)) # Zmniejszony padding dolny
        ttk.Label(downloads_label_frame, text="Aktywne pobierania", style="Header.TLabel").pack(anchor=tk.W)
        
        # Separator
        # ttk.Separator(self.main_frame, orient='horizontal').pack(fill='x', pady=(0, 10)) # Można usunąć dla "czystszego" wyglądu

        # Treeview dla listy pobierania
        tree_frame = ttk.Frame(self.main_frame, style="Main.TFrame") # Ramka dla Treeview i scrollbara
        tree_frame.pack(expand=True, fill=tk.BOTH, pady=(5,0))

        self.tree = ttk.Treeview(tree_frame, columns=("title", "size", "speed", "progress", "status"), show="headings", style="Custom.Treeview")
        self.tree.heading("title", text="Tytuł", anchor=tk.W)
        self.tree.heading("size", text="Rozmiar", anchor=tk.CENTER)
        self.tree.heading("speed", text="Prędkość", anchor=tk.CENTER)
        self.tree.heading("progress", text="Postęp", anchor=tk.CENTER)
        self.tree.heading("status", text="Status", anchor=tk.W)

        self.tree.column("title", width=380, stretch=tk.YES, anchor=tk.W)
        self.tree.column("size", width=100, stretch=tk.NO, anchor=tk.CENTER)
        self.tree.column("speed", width=120, stretch=tk.NO, anchor=tk.CENTER)
        self.tree.column("progress", width=120, stretch=tk.NO, anchor=tk.CENTER)
        self.tree.column("status", width=120, stretch=tk.NO, anchor=tk.W)
        
        self.tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview, style="Modern.Vertical.TScrollbar")
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.download_id_counter = 0
        self.update_mode_dependent_widgets() # Ustaw poprawne kolory na starcie


    def define_colors(self):
        self.colors = {
            "light": {
                "bg": "#F0F0F0", # Jasnoszary tło główne
                "widget_bg": "#FFFFFF", # Białe tło dla widgetów
                "text": "#101010",
                "secondary_text": "#555555",
                "accent": "#007AFF", # Apple Blue
                "accent_fg": "#FFFFFF",
                "accent_active": "#0056b3",
                "tree_header_bg": "#E8E8E8",
                "tree_header_fg": "#333333",
                "tree_row_even": "#FFFFFF",
                "tree_row_odd": "#F9F9F9", # Lekko inny odcień dla pasków zebry
                "tree_selected_bg": "#007AFF",
                "tree_selected_fg": "#FFFFFF",
                "border": "#D0D0D0",
            },
            "dark": {
                "bg": "#1E1E1E", # Ciemne tło główne
                "widget_bg": "#2D2D2D", # Ciemniejsze tło dla widgetów
                "text": "#E0E0E0",
                "secondary_text": "#AAAAAA",
                "accent": "#0A84FF", # Jaśniejszy niebieski
                "accent_fg": "#FFFFFF",
                "accent_active": "#0060C0",
                "tree_header_bg": "#3A3A3A",
                "tree_header_fg": "#E0E0E0",
                "tree_row_even": "#2D2D2D",
                "tree_row_odd": "#333333",
                "tree_selected_bg": "#0A84FF",
                "tree_selected_fg": "#FFFFFF",
                "border": "#454545",
            }
        }

    def is_macos(self):
        return self.root.tk.call('tk', 'windowingsystem') == 'aqua'

    def setup_styles(self):
        mode_colors = self.colors[self.current_mode]
        
        # Użyj 'clam' dla większej kontroli, chyba że macOS gdzie 'aqua' jest ok
        try:
            self.style.theme_use('clam' if not self.is_macos() else 'aqua')
        except tk.TclError:
            self.style.theme_use('default')

        # Czcionki
        default_font_family = "SF Pro Text" if self.is_macos() else "Segoe UI"
        try:
            font.Font(family=default_font_family) # Sprawdzenie
        except tk.TclError:
            default_font_family = font.nametofont("TkDefaultFont").actual()["family"]

        base_font_size = 10
        header_font_size = 15
        entry_font_size = 11
        small_font_size = 9

        # Globalne ustawienia
        self.style.configure(".",
                             font=(default_font_family, base_font_size),
                             background=mode_colors["bg"],
                             foreground=mode_colors["text"])

        self.style.configure("Main.TFrame", background=mode_colors["bg"])
        self.root.configure(bg=mode_colors["bg"])

        self.style.configure("TLabel", background=mode_colors["bg"], foreground=mode_colors["text"])
        self.style.configure("Header.TLabel", font=(default_font_family, header_font_size, "bold"),
                             background=mode_colors["bg"], foreground=mode_colors["text"])
        self.style.configure("Small.TLabel", font=(default_font_family, small_font_size),
                             background=mode_colors["bg"], foreground=mode_colors["secondary_text"])
        
        # Przyciski
        self.style.configure("TButton", font=(default_font_family, base_font_size),
                             padding=(10, 6), relief=tk.FLAT, borderwidth=0)
        self.style.map("TButton",
                       background=[('active', mode_colors["widget_bg"]), ('!disabled', mode_colors["widget_bg"])],
                       foreground=[('!disabled', mode_colors["text"])])

        self.style.configure("Accent.TButton", font=(default_font_family, base_font_size, "bold"),
                             foreground=mode_colors["accent_fg"], background=mode_colors["accent"],
                             borderwidth=0, relief=tk.FLAT, padding=(12,8))
        self.style.map("Accent.TButton",
                       background=[('active', mode_colors["accent_active"]), ('!disabled', mode_colors["accent"])],
                       foreground=[('!disabled', mode_colors["accent_fg"])])
        
        self.style.configure("ModeToggle.TButton", font=(default_font_family, base_font_size + 2), # Większa ikona
                             padding=(6,4), relief=tk.FLAT, borderwidth=1) # Lekka ramka
        self.style.map("ModeToggle.TButton",
                       background=[('active', mode_colors["widget_bg"]), ('!disabled', mode_colors["widget_bg"])],
                       foreground=[('!disabled', mode_colors["accent"])],
                       bordercolor=[('!disabled', mode_colors["border"])])


        # Entry i Combobox
        self.style.configure("Modern.TEntry",
                             font=(default_font_family, entry_font_size),
                             padding=8, # Zwiększony padding wewnętrzny
                             relief=tk.FLAT, # Płaski wygląd
                             fieldbackground=mode_colors["widget_bg"],
                             foreground=mode_colors["text"],
                             borderwidth=1, # Cienka ramka
                             bordercolor=mode_colors["border"])
        self.style.map("Modern.TEntry",
                       bordercolor=[('focus', mode_colors["accent"])],
                       selectbackground=[('focus', mode_colors["accent"])], # Kolor zaznaczenia tekstu
                       selectforeground=[('focus', mode_colors["accent_fg"])])


        self.style.configure("Modern.TCombobox",
                             font=(default_font_family, entry_font_size),
                             padding=5, relief=tk.FLAT, borderwidth=1,
                             arrowsize=15) # Rozmiar strzałki
        self.style.map("Modern.TCombobox",
                       fieldbackground=[('readonly', mode_colors["widget_bg"])],
                       foreground=[('readonly', mode_colors["text"])],
                       bordercolor=[('readonly', mode_colors["border"]), ('focus', mode_colors["accent"])],
                       selectbackground=[('readonly', mode_colors["accent"])],
                       selectforeground=[('readonly', mode_colors["accent_fg"])],
                       background=[('readonly', mode_colors["widget_bg"])]) # Tło samego widżetu

        # Treeview
        treeview_font_obj = font.Font(family=default_font_family, size=base_font_size)
        self.treeview_row_height = treeview_font_obj.metrics("linespace") + 8 # Dodatkowy padding dla czytelności
        
        self.style.configure("Custom.Treeview",
                             font=(default_font_family, base_font_size),
                             background=mode_colors["widget_bg"],
                             fieldbackground=mode_colors["widget_bg"], # Tło komórek
                             foreground=mode_colors["text"],
                             rowheight=self.treeview_row_height,
                             relief=tk.FLAT, borderwidth=0)
        self.style.map("Custom.Treeview",
                       background=[('selected', mode_colors["tree_selected_bg"])],
                       foreground=[('selected', mode_colors["tree_selected_fg"])])
        
        self.style.configure("Custom.Treeview.Heading",
                             font=(default_font_family, base_font_size, "bold"),
                             background=mode_colors["tree_header_bg"],
                             foreground=mode_colors["tree_header_fg"],
                             relief=tk.FLAT, padding=(6,6), borderwidth=0)
        self.style.map("Custom.Treeview.Heading", relief=[('active','groove')]) # Lekki efekt przy najechaniu

        # Paski przewijania
        self.style.configure("Modern.Vertical.TScrollbar",
                             gripcount=0,
                             relief=tk.FLAT,
                             background=mode_colors["widget_bg"], # Tło samego paska
                             troughcolor=mode_colors["bg"], # Tło "rynny"
                             bordercolor=mode_colors["border"],
                             arrowcolor=mode_colors["text"])
        self.style.map("Modern.Vertical.TScrollbar",
                        background=[('active', mode_colors["accent"])])

        # Tag dla pasków zebry w Treeview (jeśli chcemy) - wymaga ręcznego dodawania tagów do wierszy
        # self.tree.tag_configure('oddrow', background=mode_colors["tree_row_odd"])
        # self.tree.tag_configure('evenrow', background=mode_colors["tree_row_even"])

    def update_mode_dependent_widgets(self):
        """Aktualizuje widgety, których kolor nie jest w pełni zarządzany przez ttk.Style"""
        mode_colors = self.colors[self.current_mode]
        self.root.configure(bg=mode_colors["bg"])
        if hasattr(self, 'main_frame'): # Sprawdź, czy main_frame już istnieje
            # Dla ramek i labeli, które mogą mieć własne tło
            for widget in self.main_frame.winfo_children() + self.root.winfo_children():
                if isinstance(widget, (ttk.Frame, ttk.Label, tk.Frame, tk.Label)):
                    try:
                        # Jeśli styl jest ustawiony, to powinien działać, ale dla pewności
                        current_style = widget.cget("style")
                        if not current_style or "TFrame" in current_style or "TLabel" in current_style :
                             widget.configure(background=mode_colors["bg"])
                             if isinstance(widget, ttk.Label) and "Header" not in current_style and "Small" not in current_style:
                                 widget.configure(foreground=mode_colors["text"])
                    except tk.TclError:
                        pass # Niektóre widgety mogą nie mieć opcji 'background'
        
        # Aktualizacja ikonki przycisku trybu
        if hasattr(self, 'mode_toggle_button'):
            self.mode_toggle_button.configure(text="☀️" if self.current_mode == "dark" else "🌙")


    def toggle_mode(self):
        self.current_mode = "dark" if self.current_mode == "light" else "light"
        self.setup_styles() # Zastosuj nowe style
        self.update_mode_dependent_widgets() # Zaktualizuj pozostałe widgety
        # Może być konieczne odświeżenie niektórych widżetów, np. Treeview
        if hasattr(self, 'tree'):
            # Przeładowanie danych Treeview, aby odświeżyć style (jeśli nie działa automatycznie)
            # To jest drastyczne, ale czasami potrzebne.
            # Na razie zakładamy, że zmiana stylu wystarczy.
            pass

    def setup_entry_context_menu(self):
        self.entry_menu = tk.Menu(self.root, tearoff=0)
        self.entry_menu.add_command(label="Wytnij", command=lambda: self.url_entry.event_generate("<<Cut>>"))
        self.entry_menu.add_command(label="Kopiuj", command=lambda: self.url_entry.event_generate("<<Copy>>"))
        self.entry_menu.add_command(label="Wklej", command=lambda: self.url_entry.event_generate("<<Paste>>"))
        self.entry_menu.add_separator()
        self.entry_menu.add_command(label="Zaznacz wszystko", command=lambda: self.url_entry.select_range(0, tk.END))

        self.url_entry.bind("<Button-3>", self.show_entry_context_menu)

    def show_entry_context_menu(self, event):
        self.entry_menu.tk_popup(event.x_root, event.y_root)

    def get_clean_filename(self, text):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        text = ansi_escape.sub('', text)
        return text.strip()

    def _add_tree_item_threadsafe(self, initial_title, download_key):
        item_id = self.tree.insert("", tk.END, iid=download_key, values=(initial_title, "-", "-", "0%", "Oczekuje..."))
        downloads_info[download_key] = {
            "item_id": item_id, "title": initial_title, "progress_str": "0%",
            "total_size": "", "downloaded_size": "", "speed": "", "status": "Oczekuje..."
        }
        self._update_treeview_item_threadsafe(download_key) # Wstępna aktualizacja

    def _update_treeview_item_threadsafe(self, download_key):
        if download_key in downloads_info:
            info = downloads_info[download_key]
            if self.tree.exists(info["item_id"]):
                self.tree.item(info["item_id"], values=(
                    info.get("title", "Ładowanie tytułu..."),
                    info.get("total_size", "-"), info.get("speed", "-"),
                    info.get("progress_str", "0%"), info.get("status", "Inicjowanie...")
                ))

    def _show_messagebox_threadsafe(self, type, title, message):
        if type == "error":
            messagebox.showerror(title, message)
        elif type == "warning":
            messagebox.showwarning(title, message)
        # Dodaj inne typy w razie potrzeby

    def start_download_thread(self, cmd, initial_title, download_key):
        # Dodanie wpisu do Treeview (z głównego wątku)
        self.root.after(0, self._add_tree_item_threadsafe, initial_title, download_key)

        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, bufsize=1, text=True,
                encoding='utf-8', errors='replace'
            )
            
            # Pobranie referencji do current_info PO tym jak _add_tree_item_threadsafe utworzy wpis
            # To wymaga synchronizacji lub lekkiego opóźnienia, albo przekazania info z głównego wątku.
            # Bezpieczniej jest aktualizować słownik z głównego wątku lub przez `root.after`.
            # Na razie polegamy na tym, że _add_tree_item_threadsafe wykona się szybko.
            # Lepsze rozwiązanie: _add_tree_item_threadsafe zwraca/ustawia current_info.
            # Zmiana: current_info jest pobierane z globalnego słownika.
            
            def update_status_in_main_thread(key, status_update):
                if key in downloads_info:
                    downloads_info[key].update(status_update)
                    self._update_treeview_item_threadsafe(key)
            
            self.root.after(0, update_status_in_main_thread, download_key, {"status": "Pobieranie..."})


            progress_regex = re.compile(
                r"\[download\]\s+(?P<progress>[\d\.]+)%\s+of\s+(?P<total_size>~?[\d\.]+\w+)(\s+at\s+(?P<speed>[\d\.]+\w+/s))?(\s+ETA\s+(?P<eta>[\d:]+))?(\s+in\s+[\d:]+)?",
                re.IGNORECASE)
            filename_regex = re.compile(r"\[(?:Merger|ExtractAudio|download)\] Destination:\s*(.*)", re.IGNORECASE)
            ffmpeg_regex = re.compile(r"\[ffmpeg\] Merging formats into \"(.*)\"", re.IGNORECASE)

            # Lokalne info dla tego wątku, synchronizowane z głównym przez root.after
            local_dl_info = {"title": initial_title, "status": "Pobieranie..."}

            for line in process.stdout:
                clean_line = self.get_clean_filename(line)
                try: print(f"YT-DLP: {clean_line}")
                except UnicodeEncodeError: print(f"YT-DLP (escaped): {clean_line.encode('unicode_escape').decode('ascii')}")

                update_payload = {}

                fn_match = filename_regex.search(clean_line)
                if fn_match:
                    new_title = os.path.basename(fn_match.group(1).strip())
                    if not new_title.endswith(('.mp3', '.mp4', '.mkv', '.webm')):
                        if '.part' not in new_title: update_payload["title"] = new_title[:60] + "..." if len(new_title) > 60 else new_title
                    else: update_payload["title"] = new_title

                ffmpeg_match = ffmpeg_regex.search(clean_line)
                if ffmpeg_match:
                    new_title = os.path.basename(ffmpeg_match.group(1).strip())
                    update_payload["title"] = new_title[:60] + "..." if len(new_title) > 60 else new_title

                match = progress_regex.search(clean_line)
                if match:
                    data = match.groupdict()
                    update_payload["progress_str"] = f"{data['progress']}%"
                    try: update_payload["progress_value"] = float(data['progress'])
                    except ValueError: pass
                    update_payload["total_size"] = data['total_size'].replace("~", "") if data['total_size'] else "-"
                    update_payload["speed"] = data['speed'] if data['speed'] else "-"
                    update_payload["status"] = "Pobieranie..."

                if "has already been downloaded" in clean_line:
                    update_payload.update({"status": "Już pobrano", "progress_str": "100%"})
                    self.root.after(0, update_status_in_main_thread, download_key, update_payload)
                    process.terminate()
                    return

                if "[ExtractAudio]" in clean_line and "Destination" in clean_line:
                    update_payload["status"] = "Konwersja MP3..."
                
                if update_payload: # Jeśli są jakieś zmiany do zaktualizowania
                    self.root.after(0, update_status_in_main_thread, download_key, update_payload)

            process.wait()
            
            final_status = {}
            if process.returncode == 0:
                final_status.update({"status": "Zakończono", "progress_str": "100%", "speed": "-"})
            else:
                final_status["status"] = "Błąd"
            self.root.after(0, update_status_in_main_thread, download_key, final_status)

        except FileNotFoundError:
            self.root.after(0, self._show_messagebox_threadsafe, "error", "Błąd", "yt-dlp nie znaleziono.")
            self.root.after(0, update_status_in_main_thread, download_key, {"status": "Błąd (yt-dlp)"})
        except Exception as e:
            error_message = f"Błąd podczas pobierania: {e}"
            try: print(error_message.encode('unicode_escape').decode('ascii'))
            except: print("Błąd podczas przetwarzania komunikatu błędu.")
            self.root.after(0, self._show_messagebox_threadsafe, "error", "Błąd", f"Wystąpił problem z pobieraniem:\n{e}")
            self.root.after(0, update_status_in_main_thread, download_key, {"status": "Błąd"})


    def trigger_download(self, download_type):
        url = self.url_entry.get()
        if not url:
            self._show_messagebox_threadsafe("warning", "Brak URL", "Proszę podać link YouTube!")
            return

        self.download_id_counter += 1
        download_key = f"download_{self.download_id_counter}_{re.sub(r'[^a-zA-Z0-9]', '', url[:20])}"
        
        initial_title = f"Pobieranie: {url[:50]}..." 
        
        cmd_base = ["yt-dlp", "--no-warnings", "--progress", "--newline", "-q"] # -q dla cichszego trybu, mniej logów
        cmd_output_template = "-o", "%(title).70s.%(ext)s" # Ograniczenie długości nazwy pliku w szablonie

        if download_type == "mp3":
            bitrate = self.quality_var.get().split(" ")[0] # Weź tylko wartość np. "320K"
            cmd = cmd_base + [
                "-x", "--audio-format", "mp3", "--audio-quality", bitrate,
                *cmd_output_template, url ]
            initial_title = f"MP3: {url[:50]}..."
        elif download_type == "video":
            cmd = cmd_base + [
                "-f", "bv*[ext=mp4][height<=2160]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b", # Bardziej elastyczny format
                "--merge-output-format", "mp4",
                *cmd_output_template, url ]
            initial_title = f"Video: {url[:50]}..."
        else: return

        threading.Thread(target=self.start_download_thread, args=(cmd, initial_title, download_key), daemon=True).start()
        self.url_entry.delete(0, tk.END)

    def trigger_mp3_download(self): self.trigger_download("mp3")
    def trigger_video_download(self): self.trigger_download("video")

if __name__ == "__main__":
    root = tk.Tk()
    # Umieść check_yt_dlp tutaj, aby root był dostępny dla tk._default_root
    # jeśli aplikacja ma być tworzona warunkowo
    app = YouTubeDownloaderApp(root)
    if hasattr(app, 'root') and app.root.winfo_exists():
         root.mainloop()
    else:
        # Jeśli app.root nie istnieje (np. check_yt_dlp zniszczył okno przed pełną inicjalizacją app)
        # lub zostało zniszczone.
        print("Aplikacja nie została uruchomiona, prawdopodobnie z powodu braku yt-dlp.")
