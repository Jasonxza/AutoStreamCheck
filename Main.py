import tkinter as tk
from tkinter import messagebox
import threading
import requests
import webbrowser
import time
import json
import os
import sys

API_CHECK_INTERVAL = 35  
DATA_FILE = 'twitch_data.json'
CONFIG_FILE = 'config.json'
LOCAL_VERSION = 1.1
VERSION_URL = "https://raw.githubusercontent.com/Jasonxza/AutoStreamCheck/main/version.txt"
CODE_URL = "https://raw.githubusercontent.com/Jasonxza/AutoStreamCheck/main/Main.py"
def check_for_updates():
    print(f"Current version: {LOCAL_VERSION}. Checking for updates...")
    try:
        response = requests.get(VERSION_URL, timeout=5)
        if response.status_code == 200:
            remote_version = float(response.text.strip())
            
            if remote_version > LOCAL_VERSION:
                print(f"New version ({remote_version}) found! Downloading...")
                new_code = requests.get(CODE_URL, timeout=10).text
                
                with open(__file__, 'w', encoding='utf-8') as f:
                    f.write(new_code)
                
                print("Update complete! Restarting...")
                os.execv(sys.executable, ['python'] + sys.argv)
            else:
                print("You are on the latest version.")
    except Exception as e:
        print(f"Auto-update check bypassed (No internet or error): {e}")
def run_setup_ui():
    """Opens a UI to collect API keys if config.json doesn't exist."""
    setup_root = tk.Tk()
    setup_root.title("Initial Setup")
    setup_root.geometry("400x380")
    setup_root.resizable(False, False)
    setup_root.configure(bg='#18181b')

    tk.Label(setup_root, text="WELCOME", bg='#18181b', fg='#a970ff', font=('Segoe UI', 16, 'bold')).pack(pady=(20, 5))
    tk.Label(setup_root, text="Please enter your Twitch API details.", bg='#18181b', fg='#adadb8', font=('Segoe UI', 9)).pack(pady=(0, 20))

    tk.Label(setup_root, text="Twitch Client ID", bg='#18181b', fg='#efeff1', font=('Segoe UI', 9, 'bold')).pack(anchor="w", padx=40)
    id_entry = tk.Entry(setup_root, bg='#242427', fg='#efeff1', insertbackground='white', width=40, font=('Segoe UI', 10), bd=0)
    id_entry.pack(pady=(5, 15), ipady=5)

    tk.Label(setup_root, text="Twitch Client Secret", bg='#18181b', fg='#efeff1', font=('Segoe UI', 9, 'bold')).pack(anchor="w", padx=40)
    secret_entry = tk.Entry(setup_root, bg='#242427', fg='#efeff1', insertbackground='white', show="*", width=40, font=('Segoe UI', 10), bd=0)
    secret_entry.pack(pady=(5, 15), ipady=5)

    tk.Label(setup_root, text="Target Streamer Username", bg='#18181b', fg='#efeff1', font=('Segoe UI', 9, 'bold')).pack(anchor="w", padx=40)
    streamer_entry = tk.Entry(setup_root, bg='#242427', fg='#efeff1', insertbackground='white', width=40, font=('Segoe UI', 10), bd=0)
    streamer_entry.pack(pady=(5, 25), ipady=5)

    def save_and_close():
        c_id = id_entry.get().strip()
        c_sec = secret_entry.get().strip()
        streamer = streamer_entry.get().strip().lower()

         if not c_id or not c_sec or not streamer:
            messagebox.showerror("Error", "All fields must be filled out!")
            return

        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({
                    'CLIENT_ID': c_id,
                    'CLIENT_SECRET': c_sec,
                    'STREAMER_LOGIN': streamer
                }, f)
            setup_root.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file: {e}")

    save_btn = tk.Button(setup_root, text="Save & Continue", bg='#a970ff', fg='white', font=('Segoe UI', 10, 'bold'), 
                         activebackground='#9146ff', activeforeground='white', bd=0, cursor="hand2", command=save_and_close)
    save_btn.pack(fill="x", padx=40, ipady=5)

    setup_root.mainloop()

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

class TwitchDashboard:
    def __init__(self, root, config):
        self.root = root
        
        self.client_id = config.get('CLIENT_ID', '')
        self.client_secret = config.get('CLIENT_SECRET', '')
        self.streamer_login = config.get('STREAMER_LOGIN', '')

        self.root.title("Twitch Auto-Watcher Daemon")
        self.root.geometry("520x480")
        self.root.resizable(False, False)
        self.root.configure(bg='#18181b')
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.is_live = False
        self.was_live = False
        self.token = None
        
        self.total_watch_seconds = 0
        self.live_session_count = 0
        self.viewers_sum = 0
        self.viewers_samples = 0
        self.viewers_min = 99999999
        self.viewers_max = 0
        
        self.load_stats()

        self.status_text = tk.StringVar(value="INITIALIZING...")
        self.watch_time_text = tk.StringVar(value=self.format_time(self.total_watch_seconds))
        self.live_count_text = tk.StringVar(value=str(self.live_session_count))
        self.stream_title = tk.StringVar(value="Waiting for stream...")
        self.stream_game = tk.StringVar(value="Game: N/A")
        self.current_viewers_text = tk.StringVar(value="0")
        
        avg = int(self.viewers_sum / self.viewers_samples) if self.viewers_samples > 0 else 0
        disp_min = 0 if self.viewers_min == 99999999 else self.viewers_min
        
        self.avg_viewers_text = tk.StringVar(value=f"{avg:,}")
        self.min_viewers_text = tk.StringVar(value=f"{disp_min:,}")
        self.max_viewers_text = tk.StringVar(value=f"{self.viewers_max:,}")

        self.build_ui()

        self.monitor_thread = threading.Thread(target=self.background_monitor, daemon=True)
        self.monitor_thread.start()

    def load_stats(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.total_watch_seconds = data.get('watch_seconds', 0)
                    self.live_session_count = data.get('live_sessions', 0)
                    self.viewers_sum = data.get('viewers_sum', 0)
                    self.viewers_samples = data.get('viewers_samples', 0)
                    self.viewers_min = data.get('viewers_min', 99999999)
                    self.viewers_max = data.get('viewers_max', 0)
            except Exception:
                pass

    def save_stats(self):
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump({
                    'watch_seconds': self.total_watch_seconds,
                    'live_sessions': self.live_session_count,
                    'viewers_sum': self.viewers_sum,
                    'viewers_samples': self.viewers_samples,
                    'viewers_min': self.viewers_min,
                    'viewers_max': self.viewers_max
                }, f)
        except Exception:
            pass

    def on_closing(self):
        self.status_text.set("SAVING DATA...")
        self.save_stats()
        self.root.destroy()

    def build_ui(self):
        tk.Label(self.root, text=f"MONITORING: {self.streamer_login.upper()}", bg='#18181b', fg='#a970ff', font=('Segoe UI', 12, 'bold')).pack(pady=(20, 5))
        
        self.status_card = tk.Label(self.root, textvariable=self.status_text, bg='#242427', fg='#efeff1', font=('Segoe UI', 16, 'bold'), width=26, height=2, bd=0)
        self.status_card.pack(pady=5)

        details_frame = tk.Frame(self.root, bg='#18181b')
        details_frame.pack(pady=(10, 5), fill="x", padx=20)
        tk.Label(details_frame, textvariable=self.stream_title, bg='#18181b', fg='#efeff1', font=('Segoe UI', 10, 'italic'), wraplength=460).pack()
        tk.Label(details_frame, textvariable=self.stream_game, bg='#18181b', fg='#a970ff', font=('Segoe UI', 10, 'bold')).pack(pady=(2, 5))

        table_frame = tk.Frame(self.root, bg='#242427', highlightbackground="#3a3a3d", highlightthickness=1)
        table_frame.pack(pady=5)

        headers = ["CURRENT", "AVERAGE", "LOWEST", "HIGHEST"]
        for col, text in enumerate(headers):
            tk.Label(table_frame, text=text, bg='#242427', fg='#adadb8', font=('Segoe UI', 8, 'bold'), width=14).grid(row=0, column=col, pady=(6, 2), padx=2)

        tk.Label(table_frame, textvariable=self.current_viewers_text, bg='#242427', fg='#f4f4f5', font=('Segoe UI', 11, 'bold')).grid(row=1, column=0, pady=(0, 6))
        tk.Label(table_frame, textvariable=self.avg_viewers_text, bg='#242427', fg='#f4f4f5', font=('Segoe UI', 11, 'bold')).grid(row=1, column=1, pady=(0, 6))
        tk.Label(table_frame, textvariable=self.min_viewers_text, bg='#242427', fg='#f4f4f5', font=('Segoe UI', 11, 'bold')).grid(row=1, column=2, pady=(0, 6))
        tk.Label(table_frame, textvariable=self.max_viewers_text, bg='#242427', fg='#f4f4f5', font=('Segoe UI', 11, 'bold')).grid(row=1, column=3, pady=(0, 6))

        stats_frame = tk.Frame(self.root, bg='#18181b')
        stats_frame.pack(pady=(15, 0), fill="x", padx=40)

        watch_card = tk.Frame(stats_frame, bg='#242427', width=200, height=85)
        watch_card.pack_propagate(False)
        watch_card.pack(side="left", padx=10)
        tk.Label(watch_card, text="TOTAL WATCH TIME", bg='#242427', fg='#adadb8', font=('Segoe UI', 9, 'bold')).pack(pady=(10,2))
        tk.Label(watch_card, textvariable=self.watch_time_text, bg='#242427', fg='#f4f4f5', font=('Segoe UI', 14, 'bold')).pack()

        live_card = tk.Frame(stats_frame, bg='#242427', width=180, height=85)
        live_card.pack_propagate(False)
        live_card.pack(side="right", padx=10)
        tk.Label(live_card, text="LIVE SESSIONS", bg='#242427', fg='#adadb8', font=('Segoe UI', 9, 'bold')).pack(pady=(10,2))
        tk.Label(live_card, textvariable=self.live_count_text, bg='#242427', fg='#f4f4f5', font=('Segoe UI', 18, 'bold')).pack()

        tk.Label(self.root, text=f"v{LOCAL_VERSION} | Stats auto-save.", bg='#18181b', fg='#53535f', font=('Segoe UI', 9)).pack(side="bottom", pady=10)

    def get_twitch_token(self):
        url = f"https://id.twitch.tv/oauth2/token?client_id={self.client_id}&client_secret={self.client_secret}&grant_type=client_credentials"
        response = requests.post(url)
        response.raise_for_status()
        return response.json()['access_token']

    def get_stream_data(self):
        url = f"https://api.twitch.tv/helix/streams?user_login={self.streamer_login}"
        headers = {'Client-Id': self.client_id, 'Authorization': f'Bearer {self.token}'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()['data']
        return data[0] if len(data) > 0 else None

    def format_time(self, total_seconds):
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{days}d {hours}h {minutes}m {seconds}s" if days > 0 else f"{hours}h {minutes}m {seconds}s"

    def background_monitor(self):
        api_countdown = 0
        while True:
            if api_countdown <= 0:
                try:
                    if not self.token:
                        self.token = self.get_twitch_token()
                    
                    stream_data = self.get_stream_data()
                    self.is_live = stream_data is not None

                    if self.is_live:
                        title = stream_data.get('title', 'No Title')
                        game = stream_data.get('game_name', 'Unknown Game')
                        current_viewers = stream_data.get('viewer_count', 0)
                        
                        self.stream_title.set(title)
                        self.stream_game.set(f"Playing: {game}")
                        self.current_viewers_text.set(f"{current_viewers:,}")
                        
                        self.viewers_sum += current_viewers
                        self.viewers_samples += 1
                        if current_viewers > self.viewers_max: self.viewers_max = current_viewers
                        if current_viewers < self.viewers_min: self.viewers_min = current_viewers
                            
                        avg = int(self.viewers_sum / self.viewers_samples)
                        self.avg_viewers_text.set(f"{avg:,}")
                        self.max_viewers_text.set(f"{self.viewers_max:,}")
                        self.min_viewers_text.set(f"{self.viewers_min:,}")
                        
                        if not self.was_live:
                            self.status_text.set("STATUS: LIVE")
                            self.status_card.config(fg='#00ff7f')
                            webbrowser.open(f"https://www.twitch.tv/{self.streamer_login}")
                            self.live_session_count += 1
                            self.live_count_text.set(str(self.live_session_count))
                            self.save_stats()
                            self.was_live = True
                    else:
                        self.stream_title.set("Waiting for stream...")
                        self.stream_game.set("Game: N/A")
                        self.current_viewers_text.set("0")

                        if self.was_live:
                            self.status_text.set("STATUS: OFFLINE")
                            self.status_card.config(fg='#efeff1')
                            self.save_stats()
                            self.was_live = False
                        elif not self.was_live:
                            self.status_text.set("STATUS: OFFLINE")
                            self.status_card.config(fg='#efeff1')

                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 401:
                        self.token = None
                    self.status_text.set("API ERROR - RETRYING")
                except Exception as e:
                    self.status_text.set("CONNECTION ERROR")

                api_countdown = API_CHECK_INTERVAL

            if self.is_live:
                self.total_watch_seconds += 1
                self.watch_time_text.set(self.format_time(self.total_watch_seconds))
                if self.total_watch_seconds % 60 == 0:
                    self.save_stats()

            time.sleep(1)
            api_countdown -= 1

if __name__ == "__main__":
    check_for_updates()
    
    app_config = load_config()
    
    if not app_config:
        run_setup_ui()
        app_config = load_config()
    
    if app_config:
        main_root = tk.Tk()
        app = TwitchDashboard(main_root, app_config)
        main_root.mainloop()
    else:
        print("Setup aborted. Exiting...")
