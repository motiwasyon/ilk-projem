# -*- coding: utf-8 -*-
import os
import sys
import re  # re kütüphanesini üste aldık
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

# 📦 Birinci parçayı içeri aktarıyoruz (Çift olan satır teke düşürüldü)
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
            self.left_panel.add_widget(self.server_btn)

            self.search_input = TextInput(hint_text="Film/Kanal Ara...", multiline=False, size_hint_y=0.07, background_color=(0.12, 0.12, 0.12, 1), foreground_color=(1,1,1,1))
            self.left_panel.add_widget(self.search_input)

            self.scroll_groups = ScrollView(size_hint_y=0.85)
            self.group_layout = GridLayout(cols=1, spacing=dp(4), size_hint_y=None)
            self.group_layout.bind(minimum_height=self.group_layout.setter('height'))
            self.scroll_groups.add_widget(self.group_layout)
            
            self.left_panel.add_widget(Label(text="📁 KATEGORİLER", size_hint_y=0.04, font_size=dp(11)))
            self.left_panel.add_widget(self.scroll_groups)
            self.add_widget(self.left_panel)

            # 📺 ORTA PANEL
            self.center_panel = BoxLayout(orientation='vertical', size_hint=(0.70, 1), padding=dp(8), spacing=dp(4))
            self.status_label = Label(text="📺 SelgeTV Premium", size_hint_y=0.05, font_size=dp(13))
            self.center_panel.add_widget(self.status_label)

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
            self.hud_time_row.add_widget(self.time_curr)
            self.hud_time_row.add_widget(self.timeline)
            self.hud_time_row.add_widget(self.time_total)
            self.hud_panel.add_widget(self.hud_time_row)

            self.hud_ctrl_row = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=0.60)
            self.play_btn = Button(text="▶ Oynat", background_color=(0.17, 0.47, 0.89, 1))
            self.play_btn.bind(on_release=self.toggle_play)
            self.ss_btn = Button(text="📸 Ekran Al", background_color=(0.4, 0.76, 0.23, 1))
            self.ss_btn.bind(on_release=self.take_screenshot)
            self.fs_btn = Button(text="📺 Tam Ekran")
            self.fs_btn.bind(on_release=self.toggle_fullscreen_mode)
            
            self.hud_ctrl_row.add_widget(self.play_btn)
            self.hud_ctrl_row.add_widget(self.ss_btn)
            self.hud_ctrl_row.add_widget(self.fs_btn)
            self.hud_panel.add_widget(self.hud_ctrl_row)

            self.center_panel.add_widget(self.hud_panel)
            # Düzen sabitlemesi (Mükerrer left_panel eklemesi kaldırıldı)
            self.add_widget(self.center_panel)


            Clock.schedule_interval(self.update_hud, 1.0)
        
            # 💾 OTOMATİK HAFIZA AÇILIŞI: En son yüklenen listeyi otomatik hatırlar
            safe_dir = App.get_running_app().user_data_dir
            son_liste_yolu = os.path.join(safe_dir, "aktif_yerel_liste.m3u")
            if os.path.exists(son_liste_yolu):
                if self.core.parse_m3u(son_liste_yolu):
                    self.populate_groups()
                    self.status_label.text = "💾 Kayıtlı IPTV Listesi Hafızadan Yüklendi."  
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
            
            # 🖥️ BİLGİSAYARINIZIN SABİT IP ADRESİ
            # Kendi bilgisayarınızın IP'sini öğrendiğinizde buradaki "192.168.1.50" yazısını güncelleyin!
            bilgisayar_ip = "192.168.1.208" 
            yerel_sunucu_url = f"http://{bilgisayar_ip}:8080"
            
            # 📂 10 LİSTE HAFIZA YUVASI: Tablette kayıtlı duran 10 yuvayı tarar
            hafizadaki_listeler = []
            if os.path.exists(safe_dir):
                hafizadaki_listeler = [f for f in os.listdir(safe_dir) if f.startswith("slot_") and f.endswith(".m3u")]
            
            # Kullanıcıya gösterilecek temiz isimleri ayıklar (Örn: slot_spor.m3u -> spor.m3u)
            gosterim_isimleri = [f.replace("slot_", "") for f in hafizadaki_listeler]
            
            if not gosterim_isimleri:
                gosterim_isimleri = ["liste1.m3u", "liste2.m3u", "liste3.m3u", "liste4.m3u", "liste5.m3u", "liste6.m3u", "liste7.m3u", "liste8.m3u", "liste9.m3u", "liste10.m3u"]
                
            self.file_spinner = Spinner(text=gosterim_isimleri, values=gosterim_isimleri, size_hint_y=0.40, background_color=(0.2, 0.2, 0.2, 1))
            load_btn = Button(text="Yerel Ağdan Güncelle ve Yükle", background_color=(0.4, 0.76, 0.23, 1), size_hint_y=0.40)
            
            content.add_widget(Label(text="İzlemek/İndirmek İstediğiniz Listeyi Seçin:", size_hint_y=0.20))
            content.add_widget(self.file_spinner)
            content.add_widget(load_btn)
            popup = Popup(title='🏠 10 Yuvalı Yerel Wi-Fi Kontrolü', content=content, size_hint=(0.8, 0.4))
            
            # 🔍 AKILLI TARAYICI: Spinner tip uyuşmazlığı düzeltilmiş hatasız fonksiyon
            def klasor_tara_success(req, html_result):
                try:
                    bulunan_dosyalar = re.findall(r'href="([^"]+\.m3u)"', html_result)
                    if bulunan_dosyalar:
                        temiz_list = sorted(list(set(bulunan_dosyalar)))
                        self.file_spinner.values = temiz_list
                        self.file_spinner.text = temiz_list[0] # ✅ DÜZELTİLDİ: Spinner'ın başlangıç metni olarak listenin ilk dosyasını seçer
                except:
                    pass

            UrlRequest(yerel_sunucu_url, on_success=klasor_tara_success, timeout=3)
            
            def do_load(inst):
                try:
                    secilen_dosya = self.file_spinner.text
                    tam_yerel_url = f"{yerel_sunucu_url}/{secilen_dosya}"
                    
                    # Tabletin kendi içindeki kalıcı yuva adı
                    safe_path = os.path.join(safe_dir, f"slot_{secilen_dosya}")
                    aktif_yol = os.path.join(safe_dir, "aktif_yerel_liste.m3u")
                    
                    # 🚀 A: Bilgisayar Açıksa -> Bilgisayardan indirip kaydeder
                    def on_success(req, result):
                        try:
                            with open(safe_path, "w", encoding="utf-8", errors="ignore") as f:
                                f.write(result if isinstance(result, str) else result.decode('utf-8', errors='ignore'))
                            
                            # Aktif çalma listesi olarak kopyala
                            with open(aktif_yol, "w", encoding="utf-8") as f:
                                f.write(result if isinstance(result, str) else result.decode('utf-8', errors='ignore'))
                                
                            if self.core.parse_m3u(aktif_yol):
                                self.status_label.text = f"✅ {secilen_dosya} Bilgisayardan İndirildi ve Kaydedildi!"
                                self.populate_groups()
                                popup.dismiss()
                        except:
                            self.status_label.text = "❌ Kayıt Hatası!"

                    # 🚀 B: Bilgisayar Kapalıysa -> Daha önce tablete kaydettiği yuvadan okur
                    def on_offline_mode(req, error_msg):
                        if os.path.exists(safe_path):
                            try:
                                import shutil
                                shutil.copy2(safe_path, aktif_yol)
                                if self.core.parse_m3u(aktif_yol):
                                    self.status_label.text = f"💾 Çevrimdışı Mod: {secilen_dosya} Hafızadan Yüklendi!"
                                    self.populate_groups()
                                    popup.dismiss()
                            except:
                                self.status_label.text = "❌ Çevrimdışı Liste Okuma Hatası!"
                        else:
                            self.status_label.text = "❌ Bilgisayar Kapalı ve Bu Liste Henüz Kaydedilmemiş!"

                    # Wi-Fi üzerinden bilgisayarı yoklar
                    UrlRequest(tam_yerel_url, on_success=on_success, on_failure=on_offline_mode, on_error=on_offline_mode, timeout=4)
                except Exception as e:
                    self.status_label.text = "❌ İşlem Hatası!"
                    
            load_btn.bind(on_release=do_load)
            popup.open()
        except Exception as e:
            self.status_label.text = f"❌ Panel Hatası: {str(e)[:30]}"

    def populate_groups(self):
        self.group_layout.clear_widgets()
        for g_name in sorted(self.core.channels_by_group.keys()):
            btn = Button(text=g_name, size_hint_y=None, height=dp(38), background_color=(0.2, 0.2, 0.2, 1))
            btn.bind(on_release=lambda instance, name=g_name: self.load_channels(name))
            self.group_layout.add_widget(btn)

    def load_channels(self, group_name):
        self.group_layout.clear_widgets()
        back_btn = Button(text="⬅ KATEGORİLERE DÖN", size_hint_y=None, height=dp(40), background_color=(0.8, 0.2, 0.2, 1))
        back_btn.bind(on_release=lambda inst: self.populate_groups())
        self.group_layout.add_widget(back_btn)

        ch_list = self.core.channels_by_group.get(group_name, [])
        grouped_shows = self.core.group_shows(ch_list)

        for show_name, episodes in grouped_shows.items():
            btn = Button(text=f"🎬 {show_name}", size_hint_y=None, height=dp(38))
            if episodes:
                first_ep_url = episodes["url"] if isinstance(episodes, list) else episodes.get("url", "")
                btn.bind(on_release=lambda instance, url=first_ep_url, name=show_name: self.start_playback(url, name))
            self.group_layout.add_widget(btn)

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

















































































