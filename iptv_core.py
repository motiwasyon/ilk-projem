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
                        # 🧬 SİSTEM PARAMETRELERİNİN VERİ TABANINA SIZMASINI ÖNLEYEN ANA KALKAN
                        if name in ['font_name', 'font_size', 'height', 'ids', 'italic', 'halign', 'markup', 'font_family', 'font_features', 'font_hinting', 'font_kerning', 'font_script_name', 'is_shortened', 'last_touch', 'limit_render_to_text_bbox', 'line_height', 'max_lines', 'min_state']:
                            name = None
                            continue
                            
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
            if not channel_list:
                return shows
                
            for c in channel_list:
                ch_name = c.get("name", "Kanal")
                url = c.get("url", "")
                
                # 🧬 KİRLİ VERİLERİN SAĞ LİSTEYE GEÇİŞİNİ ENGELLEYEN İKİNCİ BARİYER
                if ch_name in ['font_name', 'font_size', 'height', 'ids', 'italic', 'halign', 'markup', 'font_family', 'font_features', 'font_hinting', 'font_kerning', 'font_script_name', 'is_shortened', 'last_touch', 'limit_render_to_text_bbox', 'line_height', 'max_lines', 'min_state']:
                    continue
                    
                if url:
                    shows[ch_name] = {"url": url}
            return shows
        except:
            return {}


