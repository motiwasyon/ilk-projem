# -*- coding: utf-8 -*-
import os
import re

class IPTVCoreLogic:
    def __init__(self):
        self.channels_by_group = {}
        self.current_group_channels = []

    def parse_m3u(self, file_path):
        self.channels_by_group = {}
        try:
            if not os.path.isabs(file_path):
                from kivy.app import App
                file_path = os.path.join(App.get_running_app().user_data_dir, file_path)
                
            if not os.path.exists(file_path):
                return False

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                name, group = None, "Diger"
                for line in f:
                    line = line.strip()
                    if line.startswith("#EXTINF"):
                        g_match = re.search(r'group-title="([^"]+)"', line)
                        group = g_match.group(1).strip() if g_match else "Diger"
                        idx = line.rfind(',')
                        name = line[idx+1:].strip() if idx != -1 else "Kanal"
                    elif line.startswith("http") and name:
                        if group not in self.channels_by_group:
                            self.channels_by_group[group] = []
                        self.channels_by_group[group].append({"name": name, "url": line})
                        name = None
            return True
        except:
            return False

    def group_shows(self, channel_list):
        try:
            shows = {}
            for c in channel_list:
                ch_name = c.get("name", "Kanal")
                url = c.get("url", "")
                if url:
                    # Kivy bileşen kodlarının veri setine sızmasını engelleyen koruma
                    if ch_name in ['font_name', 'font_size', 'height', 'ids', 'italic']:
                        continue
                    # main.py ile %100 uyumlu sözlük (dict) biçimlendirmesi
                    shows[ch_name] = {"url": url}
            return shows
        except:
            return {}

