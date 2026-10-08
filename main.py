# -*- coding: utf-8 -*-
import os
import sys
import re

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.network.urlrequest import UrlRequest
from kivy.metrics import dp

class CinemaIPTVAndroid(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.is_fullscreen = False
        
        # 🧬 AÇILIŞI HIZLANDIRAN AKILLI İZİN MOTORU:
        # İzin isteme motorunu ana iş parçacığını yormasın diye 1 saniye gecikmeli (Clock) tetikliyoruz.
        Clock.schedule_once(self.request_android_permissions, 1.0)
            
        from iptv_core import IPTVCoreLogic
        self.core = IPTVCoreLogic()

        # SOL PANEL (Kategoriler ve Sunucu Girişi)
        self.left_panel = BoxLayout(orientation='vertical', size_hint=(0.35, 1), padding=dp(8), spacing=dp(8))
        self.server_btn = Button(text="🌐 Sunucu Girişi / Düzenle", size_hint_y=0.10, background_color=(0.17, 0.47, 0.89, 1))
        self.server_btn.bind(on_release=self.show_server_popup)
        self.left_panel.add_widget(self.server_btn)

        # 🔍 AKILLI TV BOX ARAMA SATIRI
        search_row = BoxLayout(orientation='horizontal', size_hint_y=0.10, spacing=dp(4))
        self.search_input = TextInput(hint_text="Kanal/Film Ara...", multiline=False, size_hint_x=0.70, background_color=(0.12, 0.12, 0.12, 1), foreground_color=(1,1,1,1))
        search_btn = Button(text="🔍 ARA", size_hint_x=0.30, background_color=(0.17, 0.47, 0.89, 1), font_size=dp(11), font_weight='bold')
        
        search_btn.bind(on_release=self.filter_channels_by_search)
        search_row.add_widget(self.search_input)
        search_row.add_widget(search_btn)
        self.left_panel.add_widget(search_row)

        self.scroll_groups = ScrollView(size_hint_y=0.80)
        self.group_layout = GridLayout(cols=1, spacing=dp(4), size_hint_y=None)
        self.group_layout.bind(minimum_height=self.group_layout.setter('height'))
        self.scroll_groups.add_widget(self.group_layout)
        
        self.left_panel.add_widget(self.scroll_groups)
        self.add_widget(self.left_panel)

        # MERKEZ PANEL (TV Box Kumanda ve Rehber Paneli)
        self.center_panel = BoxLayout(orientation='vertical', size_hint=(0.65, 1), padding=dp(12), spacing=dp(8))
        self.status_label = Label(text="📺 SelgeTV v3.0 Premium", size_hint_y=0.20, font_size=dp(16), font_weight='bold')
        self.center_panel.add_widget(self.status_label)

        # Devasa rehber kutusu
        self.guide_box = BoxLayout(size_hint_y=0.60, orientation='vertical', padding=dp(10))
        self.guide_label = Label(text="🍿 TELEVİZO MOTORU AKTİF\n\nSoldan bir kategori seçin ve yayına tıklayın.\nSistem otomatik olarak Just Player'ı dışarıdan\ntam ekran ve sıfır donmayla ayağa kaldıracaktır.", font_size=dp(12), halign='center')
        self.guide_box.add_widget(self.guide_label)
        self.center_panel.add_widget(self.guide_box)

        # Alt Bilgi Barı
        self.hud_panel = BoxLayout(orientation='horizontal', size_hint_y=0.20, padding=dp(6), spacing=dp(8))
        self.info_label = Label(text="Durum: Liste Hazır", size_hint_x=0.60, font_size=dp(11))
        self.fs_btn = Button(text="📺 Sol Paneli Gizle", size_hint_x=0.40, background_color=(0.2, 0.2, 0.2, 1))
        self.fs_btn.bind(on_release=self.toggle_fullscreen_mode)
        self.hud_panel.add_widget(self.info_label)
        self.hud_panel.add_widget(self.fs_btn)
        self.center_panel.add_widget(self.hud_panel)
        
        self.add_widget(self.center_panel)

    def request_android_permissions(self, dt):
        """Açılış hızını baltalamamak için izinleri arka planda ister"""
        try:
            from kivy.utils import platform
            if platform == 'android':
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.INTERNET, 
                    Permission.ACCESS_NETWORK_STATE,
                    Permission.ACCESS_WIFI_STATE,
                    Permission.READ_EXTERNAL_STORAGE
                ])
        except Exception: pass

    def filter_channels_by_search(self, instance):
        aranan_kelime = self.search_input.text.strip().lower()
        if aranan_kelime:
            self.group_layout.clear_widgets()
            back_btn = Button(text="⬅ KATEGORİLERE DÖN", size_hint_y=None, height=dp(42), background_color=(0.8, 0.2, 0.2, 1))
            back_btn.bind(on_release=lambda x: self.populate_groups())
            self.group_layout.add_widget(back_btn)
            
            for g_name, ch_list in self.core.channels_by_group.items():
                for ch in ch_list:
                    ch_name = str(ch.get("name", "")).strip()
                    if aranan_kelime in ch_name.lower():
                        btn = Button(text=f"📺 {ch_name}", size_hint_y=None, height=dp(40))
                        btn.bind(on_release=lambda inst, url=ch.get("url", ""), name=ch_name: self.start_playback(url, name))
                        self.group_layout.add_widget(btn)

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
            self.server_input = TextInput(hint_text="http://sunucu.com:8080", multiline=False)
            self.user_input = TextInput(hint_text="Kullanici Adi", multiline=False)
            self.pass_input = TextInput(hint_text="Sifre", multiline=False)
            self.name_input = TextInput(hint_text="Liste Ismi", multiline=False)
            
            grid.add_widget(self.server_input)
            grid.add_widget(self.user_input)
            grid.add_widget(self.pass_input)
            grid.add_widget(self.name_input)
            content.add_widget(grid)
            
            btn_row = BoxLayout(orientation='horizontal', spacing=dp(6), size_hint_y=0.25)
            load_btn = Button(text="Hafizadan Yukle", background_color=(0.4, 0.76, 0.23, 1))
            download_btn = Button(text="Listeyi Indir", background_color=(0.17, 0.47, 0.89, 1))
            btn_row.add_widget(load_btn)
            btn_row.add_widget(download_btn)
            content.add_widget(btn_row)
            
            popup = Popup(title='SelgeTV Xtream Portal Manager', content=content, size_hint=(0.90, 0.75))
            
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
                
                if not srv or not usr or not pas or not liste_ismi: return
                liste_ismi = re.sub(r'[^\w\-_]', '', liste_ismi)
                if not srv.startswith("http"): srv = "http://" + srv
                if srv.endswith('/'): srv = srv[:-1]
                
                full_url = f"{srv}/get.php?username={usr}&password={pas}&output=ts&type=m3u_plus"
                self.info_label.text = "⏳ Sunucuya bağlanılıyor..."
                
                def on_success(req, result):
                    try:
                        safe_path = os.path.join(safe_dir, f"slot_{liste_ismi}.m3u")
                        aktif_yol = os.path.join(safe_dir, "aktif_xtream_liste.m3u")
                        
                        data_to_write = result if isinstance(result, str) else result.decode('utf-8', errors='ignore')
                        with open(safe_path, "w", encoding="utf-8", errors="ignore") as f:
                            f.write(data_to_write)
                        with open(aktif_yol, "w", encoding="utf-8", errors="ignore") as f:
                            f.write(data_to_write)
                            
                        if self.core.parse_m3u(aktif_yol):
                            popup.dismiss()
                            self.info_label.text = "✅ Liste Yüklendi!"
                            Clock.schedule_once(lambda dt: self.populate_groups(), 0.5)
                    except Exception as e:
                        self.info_label.text = f"❌ Kayıt Hatası: {str(e)}"

                def on_failure(req, result): self.info_label.text = "❌ Sunucu yanıt vermedi!"
                def on_error(req, result): self.info_label.text = "❌ Bağlantı hatası oluştu!"

                UrlRequest(full_url, on_success=on_success, on_failure=on_failure, on_error=on_error, timeout=30)

            load_btn.bind(on_release=do_load_stored)
            download_btn.bind(on_release=do_download)
            popup.open()
        except Exception as e: self.info_label.text = str(e)

    def populate_groups(self):
        self.group_layout.clear_widgets()
        for g_name in sorted(self.core.channels_by_group.keys()):
            btn = Button(text=str(g_name), size_hint_y=None, height=dp(42))
            btn.bind(on_release=lambda instance, name=g_name: self.load_channels(name))
            self.group_layout.add_widget(btn)

    def load_channels(self, group_name):
        try:
            self.group_layout.clear_widgets()
            back_btn = Button(text="⬅ KATEGORİLER", size_hint_y=None, height=dp(44), background_color=(0.8, 0.2, 0.2, 1))
            back_btn.bind(on_release=lambda inst: self.populate_groups())
            self.group_layout.add_widget(back_btn)

            ch_list = self.core.channels_by_group.get(group_name, [])
            for ch in ch_list:
                ch_name = str(ch.get("name", "")).strip()
                btn = Button(text=f"📺 {ch_name}", size_hint_y=None, height=dp(40))
                btn.bind(on_release=lambda instance, url=ch.get("url", ""), name=ch_name: self.start_playback(url, name))
                self.group_layout.add_widget(btn)
        except Exception: pass

    def start_playback(self, url, name):
        """
        🧬 TELEVİZO KALİTESİNDE JUST PLAYER KİLİTLEME MOTORU:
        Gecikmeli yükleme (Lazy Load) yöntemi ile jnius kütüphanesini sadece 
        bu satır tetiklendiğinde çağırarak "Loading" takılmasını tamamen yok ediyoruz.
        """
        self.status_label.text = f"🎬 Açılıyor: {name}"
        try:
            from kivy.utils import platform
            if platform == 'android':
                # 🎯 KİLİT SATIRLAR: Java sınıflarını açılışta değil, tam şu salisede belleğe alıyoruz
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')
                currentActivity = autoclass('org.kivy.android.PythonActivity').mActivity
                
                video_uri = Uri.parse(url)
                intent = Intent(Intent.ACTION_VIEW)
                
                if ".m3u8" in url.lower():
                    intent.setDataAndType(video_uri, "application/x-mpegURL")
                else:
                    intent.setDataAndType(video_uri, "video/mp4")
                
                intent.setPackage("com.brouken.player")
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                
                currentActivity.startActivity(intent)
                return
        except Exception as e:
            self.status_label.text = f"❌ Just Player Hatası: {str(e)}"

    def toggle_fullscreen_mode(self, instance=None):
        if not self.is_fullscreen:
            self.remove_widget(self.left_panel)
            self.center_panel.size_hint = (1, 1)
            self.fs_btn.text = "📺 Sol Paneli Göster"
            self.is_fullscreen = True
        else:
            self.center_panel.size_hint = (0.65, 1)
            self.add_widget(self.left_panel, index=0)
            self.fs_btn.text = "📺 Sol Paneli Gizle"
            self.is_fullscreen = False

class CinemaIPTVApp(App):
    def build(self):
        return CinemaIPTVAndroid()

if __name__ == "__main__":
    CinemaIPTVApp().run()


























































































































































