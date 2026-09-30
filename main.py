# -*- coding: utf-8 -*-
import os, sys, re
from datetime import datetime

# Kivy multimedya ve arayüz çekirdeği
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.uix.video import Video
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.network.urlrequest import UrlRequest # Android uyumlu kararlı internet motoru

class IPTVCoreLogic:
    def __init__(self):
        self.channels_by_group = {}
        self.current_group_channels = []

    def parse_m3u(self, file_path):
        self.channels_by_group = {}
        try:
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
class CinemaIPTVAndroid(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.core = IPTVCoreLogic()
        self.current_volume = 0.7
        self.is_fullscreen = False
        
        Window.bind(on_key_down=self.on_key_down)
        Window.bind(on_motion=self.on_mouse_motion)

        # SOL PANEL: Kategoriler ve Arama
        self.left_panel = BoxLayout(orientation='vertical', size_hint=(0.35, 1), padding=10, spacing=10)
        self.server_btn = Button(text="🌐 Sunucu Girişi", size_hint_y=None, height=45, background_color=(0.17, 0.47, 0.89, 1))
        self.server_btn.bind(on_release=self.show_server_popup)
        self.left_panel.addWidget(self.server_btn)

        self.search_input = TextInput(hint_text="Film/Kanal Ara...", multiline=False, size_hint_y=None, height=40, background_color=(0.12, 0.12, 0.12, 1), foreground_color=(1,1,1,1))
        self.left_panel.addWidget(self.search_input)

        self.scroll_groups = ScrollView()
        self.group_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.group_layout.bind(minimum_height=self.group_layout.setter('height'))
        self.scroll_groups.addWidget(self.group_layout)
        self.left_panel.addWidget(Label(text="📁 KATEGORİLER", size_hint_y=None, height=20, font_size=12))
        self.left_panel.addWidget(self.scroll_groups)
        self.add_widget(self.left_panel)

        # ORTA PANEL: Video Alanı
        self.center_panel = BoxLayout(orientation='vertical', size_hint=(0.65, 1), padding=10, spacing=5)
        self.status_label = Label(text="📺 SelgeTV Premium", size_hint_y=None, height=30, font_size=14)
        self.center_panel.addWidget(self.status_label)

        self.video = Video(source='', state='stop', options={'eos': 'loop'})
        self.center_panel.addWidget(self.video)

        # ÇİFT KATMANLI ŞEFFAF HUD KUMANDA PANELİ (Mavi/Koyu Renk Temalı)
        self.hud_panel = BoxLayout(orientation='vertical', size_hint_y=None, height=85, padding=10, spacing=5)
        self.hud_time_row = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=30)
        self.time_curr = Label(text="00:00:00", size_hint_x=None, width=60)
        self.timeline = Slider(min=0, max=100, value=0)
        self.time_total = Label(text="00:00:00", size_hint_x=None, width=60)
        self.hud_time_row.addWidget(self.time_curr)
        self.hud_time_row.addWidget(self.timeline)
        self.hud_time_row.addWidget(self.time_total)
        self.hud_panel.addWidget(self.hud_time_row)

        self.hud_ctrl_row = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=40)
        self.play_btn = Button(text="▶ Oynat", background_color=(0.17, 0.47, 0.89, 1))
        self.play_btn.bind(on_release=self.toggle_play)
        self.ss_btn = Button(text="📸 Ekran Al", background_color=(0.4, 0.76, 0.23, 1))
        self.ss_btn.bind(on_release=self.take_screenshot)
        self.fs_btn = Button(text="📺 Tam Ekran")
        self.fs_btn.bind(on_release=self.toggle_fullscreen_mode)
        
        self.hud_ctrl_row.addWidget(self.play_btn)
        self.hud_ctrl_row.addWidget(self.ss_btn)
        self.hud_ctrl_row.addWidget(self.fs_btn)
        self.hud_panel.addWidget(self.hud_ctrl_row)

        self.center_panel.addWidget(self.hud_panel)
        self.add_widget(self.center_panel)

        Clock.schedule_interval(self.update_hud, 1.0)
    def toggle_play(self, instance=None):
        if self.video.state == 'play':
            self.video.state = 'stop'
            self.play_btn.text = "▶ Oynat"
        else:
            self.video.source = self.video.source
            self.video.state = 'play'
            self.play_btn.text = "⏸ Duraklat"

    def update_hud(self, dt):
        if self.video.duration > 0:
            self.timeline.max = self.video.duration
            self.timeline.value = self.video.position
            self.time_curr.text = str(int(self.video.position))
            self.time_total.text = str(int(self.video.duration))

    def show_server_popup(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.file_input = TextInput(text="playlist.m3u", hint_text="M3U Dosya Adı", multiline=False)
        load_btn = Button(text="Listeyi Yükle", background_color=(0.4, 0.76, 0.23, 1))
        content.addWidget(Label(text="Yerel M3U Dosya Adını Girin:"))
        content.addWidget(self.file_input)
        content.addWidget(load_btn)
        popup = Popup(title='IPTV Yükleme Paneli', content=content, size_hint=(0.8, 0.5))
        
        def do_load(inst):
            if self.core.parse_m3u(self.file_input.text):
                self.status_label.text = "✅ IPTV Listesi Yüklendi!"
                self.populate_groups()
                popup.dismiss()
            else:
                self.status_label.text = "❌ Dosya Bulunamadı!"
        load_btn.bind(on_release=do_load)
        popup.open()

    def populate_groups(self):
        self.group_layout.clear_widgets()
        for g_name in sorted(self.core.channels_by_group.keys()):
            btn = Button(text=g_name, size_hint_y=None, height=40, background_color=(0.2, 0.2, 0.2, 1))
            btn.bind(on_release=lambda instance, name=g_name: self.load_channels(name))
            self.group_layout.addWidget(btn)

    def load_channels(self, group_name):
        self.group_layout.clear_widgets()
        back_btn = Button(text="⬅️ KATEGORİLERE DÖN", size_hint_y=None, height=45, background_color=(0.8, 0.2, 0.2, 1))
        back_btn.bind(on_release=lambda inst: self.populate_groups())
        self.group_layout.addWidget(back_btn)

        ch_list = self.core.channels_by_group.get(group_name, [])
        grouped_shows = self.core.group_shows(ch_list)

        for show_name, episodes in grouped_shows.items():
            btn = Button(text=f"🎬 {show_name} ({len(episodes)} Blm)", size_hint_y=None, height=40)
            if episodes:
                btn.bind(on_release=lambda instance, url=episodes[0]["url"], name=show_name: self.start_playback(url, name))
            self.group_layout.addWidget(btn)

    def start_playback(self, url, name):
        self.video.unload()
        self.video.source = url
        self.video.state = 'play'
        self.play_btn.text = "⏸ Duraklat"
        self.status_label.text = f"📺 Oynatılıyor: {name}"
        
        def on_headers(request, headers):
            sb = int(headers.get('content-length', 0))
            if sb > 0:
                self.status_label.text = f"📺 Oynatılıyor: {name} | 📂 Boyut: {sb // (1024**2)} MB"
        
        UrlRequest(url, on_headers=on_headers, method='HEAD', req_headers={"User-Agent": "Mozilla"})

    def toggle_fullscreen_mode(self, instance=None):
        if not self.is_fullscreen:
            self.remove_widget(self.left_panel)
            self.is_fullscreen = True
        else:
            self.add_widget(self.left_panel, index=1)
            self.is_fullscreen = False

    def on_key_down(self, window, key, scancode, codepoint, modifier):
        if key == 273: # TV Kumandası YUKARI tuşu
            self.current_volume = min(1.0, self.current_volume + 0.05)
            self.video.volume = self.current_volume
        elif key == 274: # TV Kumandası AŞAĞI tuşu
            self.current_volume = max(0.0, self.current_volume - 0.05)
            self.video.volume = self.current_volume
        elif key == 32: # TV Kumandası OK tuşu (Orta tuş)
            self.toggle_play()
        return True

    def on_mouse_motion(self, window, etype, motionevent):
        self.hud_panel.opacity = 1.0
        Clock.unschedule(self.fade_hud)
        Clock.schedule_once(self.fade_hud, 3.0)

    def fade_hud(self, dt):
        self.hud_panel.opacity = 0.0

    def take_screenshot(self, instance=None):
        save_path = f"ss_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        Window.screenshot(name=save_path)
        self.status_label.text = "📸 Tüm Ekran Galeriye Kaydedildi!"

class CinemaIPTVApp(App):
    def build(self):
        Window.clearcolor = (0.07, 0.07, 0.07, 1)
        return CinemaIPTVAndroid()

if __name__ == "__main__":
    CinemaIPTVApp().run()

