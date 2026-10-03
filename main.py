# -*- coding: utf-8 -*-
import os
import sys
from datetime import datetime

# 🔑 Önce Kivy çekirdeğini ayağa kaldırıyoruz
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
from kivy.network.urlrequest import UrlRequest
from kivy.metrics import dp 

# 📦 Birinci parçayı içeri aktarıyoruz
from iptv_core import IPTVCoreLogic

class CinemaIPTVAndroid(BoxLayout):
    def __init__(self, **kwargs):
        try:
            super().__init__(**kwargs)
            self.orientation = 'horizontal'
            self.core = IPTVCoreLogic()
            self.current_volume = 0.7
            self.is_fullscreen = False
            
            Window.bind(on_key_down=self.on_key_down)
            Window.bind(on_motion=self.on_mouse_motion)

            # 📺 SOL PANEL
            self.left_panel = BoxLayout(orientation='vertical', size_hint=(0.30, 1), padding=dp(8), spacing=dp(8))
            self.server_btn = Button(text="🌐 Sunucu Girişi", size_hint_y=0.08, background_color=(0.17, 0.47, 0.89, 1))
            self.server_btn.bind(on_release=self.show_server_popup)
            self.left_panel.addWidget(self.server_btn)

            self.search_input = TextInput(hint_text="Film/Kanal Ara...", multiline=False, size_hint_y=0.07, background_color=(0.12, 0.12, 0.12, 1), foreground_color=(1,1,1,1))
            self.left_panel.addWidget(self.search_input)

            self.scroll_groups = ScrollView(size_hint_y=0.85)
            self.group_layout = GridLayout(cols=1, spacing=dp(4), size_hint_y=None)
            self.group_layout.bind(minimum_height=self.group_layout.setter('height'))
            self.scroll_groups.addWidget(self.group_layout)
            
            self.left_panel.addWidget(Label(text="📁 KATEGORİLER", size_hint_y=0.04, font_size=dp(11)))
            self.left_panel.addWidget(self.scroll_groups)
            self.add_widget(self.left_panel)

            # 📺 ORTA PANEL
            self.center_panel = BoxLayout(orientation='vertical', size_hint=(0.70, 1), padding=dp(8), spacing=dp(4))
            self.status_label = Label(text="📺 SelgeTV Premium", size_hint_y=0.05, font_size=dp(13))
            self.center_panel.addWidget(self.status_label)

            # 📺 SİYAH EKRAN KORUMASI: Başlangıçta boş video motoru yüklenmesini engelliyoruz
            self.video = None
            self.video_container = BoxLayout(size_hint_y=0.80)
            self.video_container.add_widget(Label(text="🍿 Yayın İzlemek İçin Kanal Seçiniz", font_size=dp(14)))
            self.center_panel.add_widget(self.video_container)

            # 📺 ŞEFFAF HUD KUMANDA PANELİ
            self.hud_panel = BoxLayout(orientation='vertical', size_hint_y=0.15, padding=dp(6), spacing=dp(4))
            self.hud_time_row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=0.40)
            self.time_curr = Label(text="00:00:00", size_hint_x=0.15)
            self.timeline = Slider(min=0, max=100, value=0, size_hint_x=0.70)
            self.time_total = Label(text="00:00:00", size_hint_x=0.15)
            self.hud_time_row.addWidget(self.time_curr)
            self.hud_time_row.addWidget(self.timeline)
            self.hud_time_row.addWidget(self.time_total)
            self.hud_panel.addWidget(self.hud_time_row)

            self.hud_ctrl_row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=0.60)
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

            self.center_panel.add_widget(self.hud_panel)
            # Düzen sabitlemesi (Mükerrer left_panel eklemesi kaldırıldı)
            self.add_widget(self.center_panel)


            Clock.schedule_interval(self.update_hud, 1.0)
        except Exception as major_error:
            self.clear_widgets()
            self.add_widget(Label(text=f"🚨 Başlatma Hatası Yakalandı:\n{str(major_error)}"))

    def toggle_play(self, instance=None):
        if self.video and self.video.state == 'play':
            self.video.state = 'stop'
            self.play_btn.text = "▶ Oynat"
        elif self.video:
            self.video.source = self.video.source
            self.video.state = 'play'
            self.play_btn.text = "⏸ Duraklat"

    def update_hud(self, dt):
        if self.video and self.video.duration > 0:
            self.timeline.max = self.video.duration
            self.timeline.value = self.video.position
            self.time_curr.text = str(int(self.video.position))
            self.time_total.text = str(int(self.video.duration))

    def show_server_popup(self, instance):
        try:
            from kivy.uix.spinner import Spinner
            from kivy.app import App
            
            content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
            safe_dir = App.get_running_app().user_data_dir
            
            # Klasördeki tüm m3u dosyalarını otomatik tarar
            m3u_files = [f for f in os.listdir(safe_dir) if f.endswith('.m3u')]
            if not m3u_files:
                m3u_files = ["playlist.m3u"]
                
            # 🔄 Tıklayınca 10 listeyi de açan akıllı drop-down menü
            self.file_spinner = Spinner(text=m3u_files, values=m3u_files, size_hint_y=0.40, background_color=(0.2, 0.2, 0.2, 1))
            load_btn = Button(text="Seçilen Listeyi Yükle", background_color=(0.4, 0.76, 0.23, 1), size_hint_y=0.40)
            
            content.add_widget(Label(text="İzlemek İstediğiniz IPTV Listesini Seçin:", size_hint_y=0.20))
            content.add_widget(self.file_spinner)
            content.add_widget(load_btn)
            popup = Popup(title='Çoklu IPTV Seçim Paneli', content=content, size_hint=(0.7, 0.4))
            
            def do_load(inst):
                try:
                    if self.core.parse_m3u(self.file_spinner.text):
                        self.status_label.text = f"✅ {self.file_spinner.text} Başarıyla Yüklendi!"
                        self.populate_groups()
                        popup.dismiss()
                    else:
                        self.status_label.text = "❌ Liste Okunamadı!"
                except Exception as e:
                    self.status_label.text = "❌ Yükleme Hatası!"
                    
            load_btn.bind(on_release=do_load)
            popup.open()
        except Exception as e:
            self.status_label.text = "❌ Panel Açma Hatası"


    def populate_groups(self):
        self.group_layout.clear_widgets()
        for g_name in sorted(self.core.channels_by_group.keys()):
            btn = Button(text=g_name, size_hint_y=None, height=dp(38), background_color=(0.2, 0.2, 0.2, 1))
            btn.bind(on_release=lambda instance, name=g_name: self.load_channels(name))
            self.group_layout.addWidget(btn)

    def load_channels(self, group_name):
        self.group_layout.clear_widgets()
        back_btn = Button(text="⬅ KATEGORİLERE DÖN", size_hint_y=None, height=dp(40), background_color=(0.8, 0.2, 0.2, 1))
        back_btn.bind(on_release=lambda inst: self.populate_groups())
        self.group_layout.addWidget(back_btn)

        ch_list = self.core.channels_by_group.get(group_name, [])
        grouped_shows = self.core.group_shows(ch_list)

        for show_name, episodes in grouped_shows.items():
            btn = Button(text=f"🎬 {show_name}", size_hint_y=None, height=dp(38))
            if episodes:
                first_ep_url = episodes["url"] if isinstance(episodes, list) else episodes.get("url", "")
                btn.bind(on_release=lambda instance, url=first_ep_url, name=show_name: self.start_playback(url, name))
            self.group_layout.addWidget(btn)

    def start_playback(self, url, name):
        if not self.video:
            self.status_label.text = "⚠️ Video Oynatıcı Aktif Değil."
            return
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
            self.center_panel.size_hint = (1, 1)
            self.is_fullscreen = True
        else:
            self.center_panel.size_hint = (0.70, 1)
            self.add_widget(self.left_panel, index=1)
            self.is_fullscreen = False

    def on_key_down(self, window, key, scancode, codepoint, modifier):
        if key == 273 and self.video: 
            self.current_volume = min(1.0, self.current_volume + 0.05)
            self.video.volume = self.current_volume
        elif key == 274 and self.video: 
            self.current_volume = max(0.0, self.current_volume - 0.05)
            self.video.volume = self.current_volume
        elif key == 32: 
            self.toggle_play()
        return True

    def on_mouse_motion(self, window, etype, motionevent):
        self.hud_panel.opacity = 1.0
        Clock.unschedule(self.fade_hud)
        Clock.schedule_once(self.fade_hud, 3.0)

    def fade_hud(self, dt):
        self.hud_panel.opacity = 0.0

    def take_screenshot(self, instance=None):
        try:
            from kivy.app import App
            safe_dir = App.get_running_app().user_data_dir
            if not os.path.exists(safe_dir):
                os.makedirs(safe_dir)
            save_path = os.path.join(safe_dir, f"ss_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            Window.screenshot(name=save_path)
            self.status_label.text = "📸 Ekran Güvenli Alana Kaydedildi!"
        except Exception as e:
            self.status_label.text = "❌ Ekran Alınamadı (İzin Hatası)"

class CinemaIPTVApp(App):
    def build(self):
        Window.clearcolor = (0.07, 0.07, 0.07, 1)
        return CinemaIPTVAndroid()

if __name__ == "__main__":
    CinemaIPTVApp().run()











