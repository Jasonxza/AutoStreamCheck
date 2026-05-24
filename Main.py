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
LOCAL_VERSION = 1.2
VERSION_URL = "https://raw.githubusercontent.com/Jasonxza/AutoStreamCheck/main/version.txt"
CODE_URL = "https://raw.githubusercontent.com/Jasonxza/AutoStreamCheck/main/Main.py"

def check_for_updates():
    try:
        response = requests.get(VERSION_URL, timeout=5)
        if response.status_code == 200:
            remote_version = float(response.text.strip())
            if remote_version > LOCAL_VERSION:
                new_code = requests.get(CODE_URL, timeout=10).text
                with open(__file__, 'w', encoding='utf-8') as f: f.write(new_code)
                os.execv(sys.executable, ['python'] + sys.argv)
    except: pass

def run_setup_ui():
    setup_root = tk.Tk()
    setup_root.title("Initial Setup")
    setup_root.geometry("400x380")
    setup_root.configure(bg='#18181b')
    tk.Label(setup_root, text="WELCOME", bg='#18181b', fg='#a970ff', font=('Segoe UI', 16, 'bold')).pack(pady=20)
    id_entry = tk.Entry(setup_root, bg='#242427', fg='#efeff1', width=40)
    id_entry.pack(pady=5)
    secret_entry = tk.Entry(setup_root, bg='#242427', fg='#efeff1', show="*", width=40)
    secret_entry.pack(pady=5)
    streamer_entry = tk.Entry(setup_root, bg='#242427', fg='#efeff1', width=40)
    streamer_entry.pack(pady=5)
    def save():
        with open(CONFIG_FILE, 'w') as f:
            json.dump({'CLIENT_ID': id_entry.get(), 'CLIENT_SECRET': secret_entry.get(), 'STREAMER_LOGIN': streamer_entry.get().lower()}, f)
        setup_root.destroy()
    tk.Button(setup_root, text="Save", command=save).pack()
    setup_root.mainloop()

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f: return json.load(f)
    return None

class TwitchDashboard:
    def __init__(self, root, config):
        self.root = root
        self.client_id = config['CLIENT_ID']
        self.client_secret = config['CLIENT_SECRET']
        self.streamer_login = config['STREAMER_LOGIN']
        self.root.geometry("520x480")
        self.root.configure(bg='#18181b')
        self.token = None
        self.total_watch_seconds = 0
        self.live_session_count = 0
        self.load_stats()
        self.status_text = tk.StringVar(value="MONITORING...")
        self.status_card = tk.Label(root, textvariable=self.status_text, bg='#242427', fg='#efeff1', font=('Arial', 16))
        self.status_card.pack(pady=20)
        threading.Thread(target=self.monitor, daemon=True).start()

    def load_stats(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f: data = json.load(f)
                self.total_watch_seconds = data.get('watch_seconds', 0)
            except: pass
    
    def save_stats(self):
        with open(DATA_FILE, 'w') as f: json.dump({'watch_seconds': self.total_watch_seconds}, f)

    def monitor(self):
        while True:
            try:
                if not self.token:
                    url = f"https://id.twitch.tv/oauth2/token?client_id={self.client_id}&client_secret={self.client_secret}&grant_type=client_credentials"
                    self.token = requests.post(url).json()['access_token']
                
                headers = {'Client-Id': self.client_id, 'Authorization': f'Bearer {self.token}'}
                data = requests.get(f"https://api.twitch.tv/helix/streams?user_login={self.streamer_login}", headers=headers).json()['data']
                
                if data:
                    self.status_text.set("STATUS: LIVE")
                    self.total_watch_seconds += 35
                    self.save_stats()
                else:
                    self.status_text.set("STATUS: OFFLINE")
            except: self.token = None
            time.sleep(API_CHECK_INTERVAL)

if __name__ == "__main__":
    check_for_updates()
    cfg = load_config()
    if not cfg: run_setup_ui(); cfg = load_config()
    if cfg:
        root = tk.Tk()
        app = TwitchDashboard(root, cfg)
        root.mainloop()
