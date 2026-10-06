# -*- coding: utf-8 -*-
import os
import re

class IPTVCoreLogic:
    def __init__(self):
        # Gruplara göre kanalları tutan ana sözlük
        self.channels_by_group = {}

    def parse_m3u(self, file_path):
        """
        M3U formatındaki IPTV listesini ayrıştırır ve gruplara göre hafızaya alır.
        Kivy dahili bileşenlerinin sızmasını önlemek için sıkı tip kontrolü içerir.
        """
        self.channels_by_group = {}
        try:
            # Eğer yol mutlak (absolute) değilse, Kivy'nin güvenli kullanıcı veri dizini ile birleştirir
            if not os.path.isabs(file_path):
                from kivy.app import App
                file_path = os.path.join(App.get_running_app().user_data_dir, file_path)
                
            if not os.path.exists(file_path):
                return False

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                name, group = None, "Diğer"
                
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                        
                    if line.startswith("#EXTINF"):
                        # group-title verisini güvenli bir şekilde ayıklar
                        g_match = re.search(r'group-title="([^"]+)"', line)
                        group = g_match.group(1).strip() if g_match else "Diğer"
                        
                        # Kanal adını sondaki virgülden sonra arar
                        idx = line.rfind(',')
                        if idx != -1:
                            name = line[idx+1:].strip()
                        else:
                            name = "Kanal"
                            
                    elif line.startswith("http") and name:
                        # 🧬 KİRLİ VERİ VE KIVY SIZMA ENGELEYİCİSİ (ANA KALKAN)
                        # Kanal adının kesinlikle saf bir string olmasını garanti ediyoruz.
                        # Eğer gelen veri Kivy nesne referansıysa string dönüşümü '<kivy.' ile başlar.
                        safe_name = str(name).strip()
                        
                        if (not safe_name or 
                            safe_name.startswith('<kivy.') or 
                            safe_name.startswith('property') or 
                            'font_' in safe_name or 
                            safe_name in ['height', 'ids', 'italic', 'halign', 'markup', 'line_height', 'max_lines']):
                            name = None
                            continue
                            
                        # Kanalı ilgili gruba kaydeder
                        if group not in self.channels_by_group:
                            self.channels_by_group[group] = []
                            
                        self.channels_by_group[group].append({
                            "name": safe_name, 
                            "url": line.strip()
                        })
                        name = None
            return True
        except Exception:
            return False

    def group_shows(self, channel_list):
        """
        Kanal listesini arayüzün (sağ liste) güvenle tüketebileceği 
        temiz bir sözlük (dict) yapısına dönüştürür.
        """
        shows = {}
        if not channel_list:
            return shows
            
        try:
            for c in channel_list:
                if not isinstance(c, dict):
                    continue
                    
                ch_name = c.get("name", "Kanal")
                url = c.get("url", "")
                
                # Veriyi string olarak kesinleştir ve sızma kontrollerini yap
                safe_show_name = str(ch_name).strip()
                if (not safe_show_name or 
                    safe_show_name.startswith('<kivy.') or 
                    'font_' in safe_show_name or 
                    safe_show_name in ['height', 'ids', 'italic', 'halign', 'markup']):
                    continue
                    
                if url:
                    shows[safe_show_name] = {"url": str(url).strip()}
            return shows
        except Exception:
            return {}



