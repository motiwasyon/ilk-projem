# -*- coding: utf-8 -*-
import os
import re

class IPTVCoreLogic:
    def __init__(self):
        self.channels_by_group = {}

    def parse_m3u(self, file_path):
        self.channels_by_group = {}
        try:
            # 🎯 Kivy App nesnesini hafıza kilitlenmesi yaratmasın diye sadece fonksiyon içinde çağırıyoruz
            if not os.path.isabs(file_path):
                from kivy.app import App
                running_app = App.get_running_app()
                if running_app:
                    file_path = os.path.join(running_app.user_data_dir, file_path)
                
            if not os.path.exists(file_path):
                return False

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                name, group = None, "Diger"
                for line in f:
                    line = line.strip()
                    if line.startswith("#EXTINF"):
                        g_match = re.search(r'group-title="([^"]+)"', line)
                        # 📝 TÜRKÇE HARF ARINDIRMA: "Diğer" yerine evrensel "Diger" formatına çektik
                        group = g_match.group(1).strip() if g_match else "Diger"
                        idx = line.rfind(',')
                        name = line[idx+1:].strip() if idx != -1 else "Kanal"
                    elif line.startswith("http") and name:
                        safe_name = str(name).strip()
                        
                        # 🧬 KIVY ÖZELLİKLERİNİN VERİ TABANINA SIZMASINI ÖNLEYEN KESİN KALKAN
                        if (not safe_name or 
                            safe_name.startswith('<kivy.') or 
                            'font_' in safe_name or 
                            'halign' in safe_name or 
                            'valign' in safe_name or 
                            safe_name in ['height', 'ids', 'italic', 'markup', 'line_height', 'max_lines', 'min_state', 'font_family', 'font_features', 'font_hinting', 'font_kerning', 'font_name', 'font_size']):
                            name = None
                            continue
                            
                        if group not in self.channels_by_group:
                            self.channels_by_group[group] = []
                        self.channels_by_group[group].append({"name": safe_name, "url": line.strip()})
                        name = None
            return True
        except Exception:
            return False

    def group_shows(self, channel_list):
        shows = {}
        if not channel_list:
            return shows
        try:
            for c in channel_list:
                if not isinstance(c, dict):
                    continue
                ch_name = c.get("name", "Kanal")
                url = c.get("url", "")
                
                safe_show_name = str(ch_name).strip()
                # 🧬 SAĞ LİSTE İÇİN İKİNCİ EMNİYET BARİYERİ
                if (not safe_show_name or 
                    safe_show_name.startswith('<kivy.') or 
                    'font_' in safe_show_name or 
                    'halign' in safe_show_name or 
                    safe_show_name in ['height', 'ids', 'italic', 'markup', 'line_height', 'max_lines']):
                    continue
                    
                if url:
                    shows[safe_show_name] = {"url": str(url).strip()}
            return shows
        except Exception:
            return {}



