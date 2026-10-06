# -*- coding: utf-8 -*-
import os
import sys
import re
from datetime import datetime

from kivy.config import Config
Config.set('graphics', 'resizable', '0')

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

class CinemaIPTVAndroid(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        
        # Dinamik core yüklemesi ile açılış güvenliği
        from iptv_core import IPTVCoreLogic
        self.core = IPTVCoreLogic()
        
        self.current_volume = 0.7
        self.is_fullscreen = False
        
        Window.bind(on_key_down=self.on_key_down)

        # SOL PANEL (Kategoriler ve Giriş)
        self.left_panel = BoxLayout(orientation='vertical', size_hint=(0.30, 1), padding=dp(8), spacing=dp(8))
        self.server_btn = Button(text="🌐 Sunucu Girişi", size_hint_y=0.08, background_color=(0.17, 0.47, 0.89, 1))
        self.server_btn.bind(on_release=self.show_server_popup)
        self.left_panel.add_widget(self.server_btn)

        search_row = BoxLayout(orientation='horizontal', size_hint_y=0.08, spacing=dp(4))
        self.search_input = TextInput(text="", multiline=False, size_hint_x=0.75, background_color=(0.12, 0.12, 0.12, 1), foreground_color=(1,1,1,1), input_type='text', keyboard_suggestions=False)
        search_btn = Button(text="🔍 ARA", size_hint_x=0.25, background_color=(0.17, 0.47, 0.89, 1), font_size=dp(11), font_weight='bold')
        
        def filter_channels_by_search(inst):
            aranan_kelime = self.search_input.text.strip().lower()
            if aranan_kelime:
                self.group_layout.clear_widgets()
                back_btn = Button(text="⬅ KATEGORİLERE DÖN", size_hint_y=None, height=dp(42), background_color=(0.8, 0.2, 0.2, 1))
                back_btn.bind(on_release=lambda x: self.populate_groups())
                self.group_layout.add_widget(back_btn)
                
                for g_name, ch_list in self.core.channels_by_group.items():
                    for ch in ch_list:
                        ch_name = str(ch.get("name", "")).strip()
                        if not ch_name or ch_name.startswith('<kivy.') or 'font_' in ch_name:
                            continue
                        if aranan_kelime in ch_name.lower():
                            btn = Button(text=f"📺 {ch_name}", size_hint_y=None, height=dp(40), background_color=(0.15, 0.15, 0.15, 1))
                            btn.bind(on_release=lambda instance, url=ch.get("url", ""), name=ch_name: self.start_playback(url, name))
                            self.group_layout.add_widget(btn)
                self.status_label.text = f"🔍 Arama tamamlandı."
        
        search_btn.bind(on_release=filter_channels_by_search)
        search_row.add_widget(self.search_input)
        search_row.add_widget(search_btn)
        self.left_panel.add_widget(search_row)

        self.scroll_groups = ScrollView(size_hint_y=0.85)
        self.group_layout = GridLayout(cols=1, spacing=dp(4), size_hint_y=None)
        self.group_layout.bind(minimum_height=self.group_layout.setter('height'))
        self.scroll_groups.add_widget(self.group_layout)
        
        self.left_panel.add_widget(Label(text="📁 KATEGORİLER", size_hint_y=0.04, font_size=dp(11)))
        self.left_panel.add_widget(self.scroll_groups)
        self.add_widget(self.left_panel)

        # MERKEZ PANEL (Oynatıcı Ekranı)
        self.center_panel = BoxLayout(orientation='vertical', size_hint=(0.70, 1), padding=dp(8), spacing=dp(4))
        self.status_label = Label(text="📺 SelgeTV Premium", size_hint_y=0.05, font_size=dp(13))
        self.center_panel.add_widget(self.status_label)

        self.video = None
        self.video_container = BoxLayout(size_hint_y=0.80)
        self.video_container.add_widget(Label(text="🍿 Yayın İzlemek İçin Kanal Seçiniz", font_size=dp(14)))
        self.center_panel.add_widget(self.video_container)

        self.hud_panel = BoxLayout(orientation='vertical', size_hint_y=0.15, padding=dp(6), spacing=dp(4))
        self.hud_time_row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=0.40)
        self.time_curr = Label(text="00:00:00", size_hint_x=0.15)
        self.timeline = Slider(min=0, max=100, value=0, size_hint_x=0.70)
        self.time_total = Label(text="00:00:00", size_hint_x=0.15)
        self.hud_time_row.add_widget(self.time_curr)
        self.hud_time_row.add_widget(self.timeline)
        self.hud_time_row.add_widget(self.time_total)
        self.hud_panel.add_widget(self.hud_time_row)

        self.hud_ctrl_row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=0.60)
        self.play_btn = Button(text="▶ Oynat", background_color=(0.17, 0.47, 0.89, 1))
        self.play_btn.bind(on_release=self.toggle_play)
        self.ss_btn = Button(text="📸 Ekran Al", background_color=(0.4, 0.76, 0.23, 1))
        self.fs_btn = Button(text="📺 Tam Ekran")
        self.fs_btn.bind(on_release=self.toggle_fullscreen_mode)
        
        self.hud_ctrl_row.add_widget(self.play_btn)
        self.hud_ctrl_row.add_widget(self.ss_btn)
        self.hud_ctrl_row.add_widget(self.fs_btn)
        self.hud_panel.add_widget(self.hud_ctrl_row)

        self.center_panel.add_widget(self.hud_panel)
        self.add_widget(self.center_panel)

        Clock.schedule_interval(self.update_hud, 1.0)

    # 🧬 ANDROID UYUMLU DOKUNMATİK PANEL GÖSTERGESİ
    def on_touch_down(self, touch):
        # Tıklama algılandığında alt kontrol panelini gösterir
        self.hud_panel.opacity = 1.0
        Clock.unschedule(self.fade_hud)
        Clock.schedule_once(self.fade_hud, 4.0)
        return super().on_touch_down(touch)

    def fade_hud(self, dt):
        self.hud_panel.opacity = 0.0

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
            content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(6))
            safe_dir = App.get_running_app().user_data_dir
            
            hafizadaki_listeler = []
            if os.path.exists(safe_dir):
                hafizadaki_listeler = [f.replace("slot_", "").replace(".m3u", "") for f in os.listdir(safe_dir) if f.startswith("slot_") and f.endswith(".m3u")]
            
            if not hafizadaki_listeler:
                hafizadaki_listeler = ["Bos Slot"]
                
            self.file_spinner = Spinner(text=str(hafizadaki_listeler[0] if hafizadaki_listeler else "Bos Slot"), values=hafizadaki_listeler, size_hint_y=0.15)
            content.add_widget(self.file_spinner)
            
            grid = GridLayout(cols=2, spacing=dp(6), size_hint_y=0.60)
            self.server_input = TextInput(hint_text="Sunucu URL", multiline=False)
            self.user_input = TextInput(hint_text="Kullanici", multiline=False)
            self.pass_input = TextInput(hint_text="Sifre", multiline=False)
            self.name_input = TextInput(hint_text="Liste Ismi", multiline=False)
            
            grid.add_widget(self.server_input)
            grid.add_widget(self.user_input)
            grid.add_widget(self.pass_input)
            grid.add_widget(self.name_input)
            content.add_widget(grid)
            
            btn_row = BoxLayout(orientation='horizontal', spacing=dp(6), size_hint_y=0.25)
            load_btn = Button(text="Hafizadan Ac", background_color=(0.4, 0.76, 0.23, 1))
            download_btn = Button(text="Indir", background_color=(0.17, 0.47, 0.89, 1))
            btn_row.add_widget(load_btn)
            btn_row.add_widget(download_btn)
            content.add_widget(btn_row)
            
            popup = Popup(title='Xtream Manager', content=content, size_hint=(0.85, 0.65))
            
            def do_load_stored(inst):
                secilen = self.file_spinner.text
                if "Bos" in secilen: return
                safe_path = os.path.join(safe_dir, f"slot_{secilen}.m3u")
                aktif_yol = os.path.join(safe_dir, "aktif_xtream_liste.m3u")
                try:
                    import shutil
                    shutil.copy2(safe_path, aktif_yol)
                    if self.core.parse_m3u(aktif_yol):
                        popup.dismiss()
                        Clock.schedule_once(lambda dt: self.populate_groups(), 0.5)
                except Exception: pass

            def do_download(inst):
                srv = self.server_input.text.strip()
                usr = self.user_input.text.strip()
                pas = self.pass_input.text.strip()
                liste_ismi = self.name_input.text.strip()
                
                if not srv or not usr or not pas or not liste_ismi:
                    return
                liste_ismi = re.sub(r'[^\w\-_]', '', liste_ismi)
                if not srv.startswith("http"): srv = "http://" + srv
                if srv.endswith('/'): srv = srv[:-1]
                
                full_url = f"{srv}/get.php?username={usr}&password={pas}&output=ts&type=m3u_plus"
                
                def on_success(req, result):
                    try:
                        safe_path = os.path.join(safe_dir, f"slot_{liste_ismi}.m3u")
                        aktif_yol = os.path.join(safe_dir, "aktif_xtream_liste.m3u")
                        with open(safe_path, "w", encoding="utf-8", errors="ignore") as f:
                            f.write(result if isinstance(result, str) else result.decode('utf-8', errors='ignore'))
                        with open(aktif_yol, "w", encoding="utf-8") as f:
                            f.write(result if isinstance(result, str) else result.decode('utf-8', errors='ignore'))
                        if self.core.parse_m3u(aktif_yol):
                            popup.dismiss()
                            Clock.schedule_once(lambda dt: self.populate_groups(), 0.5)
                    except Exception: pass

                UrlRequest(full_url, on_success=on_success, timeout=25)

            load_btn.bind(on_release=do_load_stored)
            download_btn.bind(on_release=do_download)
            popup.open()
        except Exception: pass

    def populate_groups(self):
        self.group_layout.clear_widgets()
        for g_name in sorted(self.core.channels_by_group.keys()):
            btn = Button(text=str(g_name), size_hint_y=None, height=dp(38))
            btn.bind(on_release=lambda instance, name=g_name: self.load_channels(name))
            self.group_layout.add_widget(btn)

    def load_channels(self, group_name):
        try:
            self.group_layout.clear_widgets()
            back_btn = Button(text="⬅ KATEGORILER", size_hint_y=None, height=dp(42), background_color=(0.8, 0.2, 0.2, 1))
            back_btn.bind(on_release=lambda inst: self.populate_groups())
            self.group_layout.add_widget(back_btn)

            ch_list = self.core.channels_by_group.get(group_name, [])
            for ch in ch_list:
                ch_name = str(ch.get("name", "")).strip()
                if not ch_name or ch_name.startswith('<kivy.') or 'font_' in ch_name:
                    continue
                btn = Button(text=f"📺 {ch_name}", size_hint_y=None, height=dp(40))
                btn.bind(on_release=lambda instance, url=ch.get("url", ""), name=ch_name: self.start_playback(url, name))
                self.group_layout.add_widget(btn)
        except Exception: pass

    def start_playback(self, url, name):
        try:
            from kivy.utils import platform
            if platform == 'android':
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')
                currentActivity = autoclass('org.kivy.android.PythonActivity').mActivity
                intent = Intent(Intent.ACTION_VIEW)
                intent.setDataAndType(Uri.parse(url), "*/*")
                currentActivity.startActivity(Intent.createChooser(intent, "Oynatici Secin:"))
                return
            if not self.video:
                self.video_container.clear_widgets()
                self.video = Video(source='', state='stop', size_hint_y=1)
                self.video_container.add_widget(self.video)
            self.video.unload()
            self.video.source = url
            self.video.state = 'play'
        except Exception: pass

    def toggle_fullscreen_mode(self, instance=None):
        if not self.is_fullscreen:
            self.remove_widget(self.left_panel)
            self.center_panel.size_hint = (1, 1)
            self.is_fullscreen = True
        else:
            self.center_panel.size_hint = (0.70, 1)
            self.add_widget(self.left_panel, index=0)
            self.is_fullscreen = False

    def on_key_down(self, window, key, scancode, codepoint, modifier):
        if key == 32: self.toggle_play()
        return True

class CinemaIPTVApp(App):
    def build(self):
        Window.clearcolor = (0.07, 0.07, 0.07, 1)
        return CinemaIPTVAndroid()

if __name__ == "__main__":
    CinemaIPTVApp().run()
























































































































































