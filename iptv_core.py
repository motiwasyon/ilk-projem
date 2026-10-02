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
            # 📱 Android işletim sisteminde dosya yolunu korumalı alana yönlendiriyoruz
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
        except Exception as e:
            return False

    def group_shows(self, channel_list):
        shows = {}
        for c in channel_list:
            ch_name = c["name"]
            match = re.search(r'(.*?)\s+([Ss]\d+\s*[Ee]\d+|[Ss]\d+[Ee]\d+|[Ss]ezon\s+\d+|[Bb]ölüm\s+\d+)', ch_name)
            if match:
                show_name = match.group(1).strip()
                ep_name = match.group(2).strip()
                remaining = ch_name[match.end():].strip()
                if remaining: ep_name = f"{ep_name} {remaining}"
            else:
                show_name = ch_name
                ep_name = "Oynat"
            if show_name not in shows: shows[show_name] = []
            shows[show_name].append({"ep_name": ep_name, "url": c["url"], "full_name": ch_name})
        return shows
