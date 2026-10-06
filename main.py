# -*- coding: utf-8 -*-
import os
import sys
import re
from datetime import datetime

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
                            if not ch_name or ch_name.startswith('<kivy.') or 'font_' in ch_name or 'halign' in ch_name:
                                continue
                                
                            if aranan_kelime in ch_name.lower():
                                btn = Button(text=f"📺 {ch_name}", size_hint_y=None, height=dp(40), background_color=(0.15, 0.15, 0.15, 1))
                                btn.bind(on_release=lambda instance, url=ch.get("url", ""), name=ch_name: self.start_playback(url, name))
                                self.group_layout.add_widget(btn)
                    self.status_label.text = f"🔍 '{self.search_input.text}' için arama sonuçları listelendi."
            
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
            self.ss_btn.bind(on_release=self.take_screenshot)
            self.fs_btn = Button(text="📺 Tam Ekran")
            self.fs_btn.bind(on_release=self.toggle_fullscreen_mode)
            
            self.hud_ctrl_row.add_widget(self.play_btn)
            self.hud_ctrl_row.add_widget(self.ss_btn)
            self.hud_ctrl_row.add_widget(self.fs_btn)
            self.hud_panel.add_widget(self.hud_ctrl_row)

            self.center_panel.add_widget(self.hud_panel)
            self.add_widget(self.center_panel)

            # 🚀 GÜVENLİK ADIMI: Zamanlayıcı aktif fakat çökerten otomatik yükleme mekanizması kaldırıldı.
            Clock.schedule_interval(self.update_hud, 1.0)
            self.status_label.text = "📺 SelgeTV Hazır. Listeyi Yüklemek İçin Giriş Yapın."

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
            from kivy.uix.textinput import TextInput
            from kivy.uix.gridlayout import GridLayout
            from kivy.uix.spinner import Spinner
            from kivy.app import App
            
            def get_system_clipboard():
                from kivy.utils import platform
                if platform == 'android':
                    try:
                        from jnius import autoclass
                        PythonActivity = autoclass('org.kivy.android.PythonActivity')
                        Context = autoclass('android.content.Context')
                        clipboard_service = PythonActivity.mActivity.getSystemService(Context.CLIPBOARD_SERVICE)
                        if clipboard_service.hasPrimaryClip():
                            primary_clip = clipboard_service.getPrimaryClip()
                            if primary_clip.getItemCount() > 0:
                                return str(primary_clip.getItemAt(0).getText())
                    except Exception:
                        pass
                else:
                    try:
                        from kivy.core.clipboard import Clipboard
                        text = str(Clipboard.paste()).strip()
                        if not text.startswith('<kivy.') and 'font_' not in text and 'halign' not in text:
                            return text
                    except Exception:
                        pass
                return ""

            content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(6))
            safe_dir = App.get_running_app().user_data_dir
            
            hafizadaki_listeler = []
            if os.path.exists(safe_dir):
                hafizadaki_listeler = [f.replace("slot_", "").replace(".m3u", "") for f in os.listdir(safe_dir) if f.startswith("slot_") and f.endswith(".m3u")]
            
            if not hafizadaki_listeler:
                hafizadaki_listeler = ["Kayıtlı Liste Bulunmuyor"]
                
            # 🎯 KESİN TAMİR: Spinner metnine listenin kendisi değil, sadece ilk elemanın string hali veriliyor
            self.file_spinner = Spinner(text=str(hafizadaki_listeler[0]), values=hafizadaki_listeler, size_hint_y=0.15, background_color=(0.2, 0.2, 0.2, 1))
            content.add_widget(Label(text="📱 Kayıtlı Listeleriniz:", size_hint_y=0.05, font_size=dp(11)))
            content.add_widget(self.file_spinner)
            
            grid = GridLayout(cols=3, spacing=dp(6), size_hint_y=0.55)
            
            grid.add_widget(Label(text="URL:", size_hint_x=0.15, font_size=dp(12)))
            self.server_input = TextInput(text="", multiline=False, size_hint_x=0.65, background_color=(0.12, 0.12, 0.12, 1), foreground_color=(1,1,1,1), input_type='text', keyboard_suggestions=False)
            grid.add_widget(self.server_input)
            url_paste = Button(text="📋", size_hint_x=0.20, background_color=(0.3, 0.3, 0.3, 1))
            url_paste.bind(on_release=lambda x: setattr(self.server_input, 'text', get_system_clipboard()))
            grid.add_widget(url_paste)
            
            grid.add_widget(Label(text="User:", size_hint_x=0.15, font_size=dp(12)))
            self.user_input = TextInput(hint_text="Kullanici Adi", multiline=False, size_hint_x=0.65, background_color=(0.12, 0.12, 0.12, 1), foreground_color=(1,1,1,1))
            grid.add_widget(self.user_input)
            user_paste = Button(text="📋", size_hint_x=0.20, background_color=(0.3, 0.3, 0.3, 1))
            user_paste.bind(on_release=lambda x: setattr(self.user_input, 'text', get_system_clipboard()))
            grid.add_widget(user_paste)
            
            grid.add_widget(Label(text="Pass:", size_hint_x=0.15, font_size=dp(12)))
            self.pass_input = TextInput(hint_text="Sifre", password=False, multiline=False, size_hint_x=0.65, background_color=(0.12, 0.12, 0.12, 1), foreground_color=(1,1,1,1))
            grid.add_widget(self.pass_input)
            pass_paste = Button(text="📋", size_hint_x=0.20, background_color=(0.3, 0.3, 0.3, 1))
            pass_paste.bind(on_release=lambda x: setattr(self.pass_input, 'text', get_system_clipboard()))
            grid.add_widget(pass_paste)
            
            grid.add_widget(Label(text="İsim:", size_hint_x=0.15, font_size=dp(12)))
            self.name_input = TextInput(hint_text="Liste İsmi (Örn: Spor)", multiline=False, size_hint_x=0.65, background_color=(0.12, 0.12, 0.12, 1), foreground_color=(1,1,1,1))
            grid.add_widget(self.name_input)
            name_paste = Button(text="📋", size_hint_x=0.20, background_color=(0.3, 0.3, 0.3, 1))
            name_paste.bind(on_release=lambda x: setattr(self.name_input, 'text', get_system_clipboard()))
            grid.add_widget(name_paste)
            
            content.add_widget(grid)
            
            btn_row = BoxLayout(orientation='horizontal', spacing=dp(6), size_hint_y=0.25)
            load_btn = Button(text="Hafızadan Aç", background_color=(0.4, 0.76, 0.23, 1))
            download_btn = Button(text="Yeni İndir ve Kaydet", background_color=(0.17, 0.47, 0.89, 1))
            btn_row.add_widget(load_btn)
            btn_row.add_widget(download_btn)
            content.add_widget(btn_row)
            
            popup = Popup(title='🌐 10 Yuvalı Xtream Playlist Manager', content=content, size_hint=(0.85, 0.65))
            
            def do_load_stored(inst):
                secilen = self.file_spinner.text
                if "Bulunmuyor" in secilen:
                    self.status_label.text = "❌ Açılacak kayıtlı liste yok!"
                    return
                safe_path = os.path.join(safe_dir, f"slot_{secilen}.m3u")
                aktif_yol = os.path.join(safe_dir, "aktif_xtream_liste.m3u")
                try:
                    import shutil
                    shutil.copy2(safe_path, aktif_yol)
                    if self.core.parse_m3u(aktif_yol):
                        self.status_label.text = f"💾 Çevrimdışı Mod: {secilen} Hafızadan Yüklendi!"
                        popup.dismiss()
                        Clock.schedule_once(lambda dt: self.populate_groups(), 0.5)
                except Exception:
                    self.status_label.text = "❌ Hafızadan Okuma Hatası!"

            def do_download(inst):
                srv = self.server_input.text.strip()
                usr = self.user_input.text.strip()
                pas = self.pass_input.text.strip()
                liste_ismi = self.name_input.text.strip()
                
                if not srv or not usr or not pas or not liste_ismi:
                    self.status_label.text = "❌ Lütfen tüm alanları doldurun!"
                    return
                    
                liste_ismi = re.sub(r'[^\w\-_]', '', liste_ismi)
                if not srv.startswith("http"): srv = "http://" + srv
                if srv.endswith('/'): srv = srv[:-1]
                    
                self.status_label.text = "🔄 Sunucuya bağlanılıyor, liste indiriliyor..."
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
                            self.status_label.text = f"✅ {liste_ismi} Başarıyla İndirildi!"
                            popup.dismiss()
                            Clock.schedule_once(lambda dt: self.populate_groups(), 0.5)
                        else:
                            self.status_label.text = "❌ İndirilen liste çözümlenemedi!"
                    except Exception:
                        self.status_label.text = "❌ Dosya Yazma Hatası!"

                def on_failure(req, result): self.status_label.text = "❌ Sunucu bağlantısı başarısız!"
                def on_error(req, error): self.status_label.text = "❌ Bağlantı hatası veya zaman aşımı!"
                UrlRequest(full_url, on_success=on_success, on_failure=on_failure, on_error=on_error, timeout=25)
                
            load_btn.bind(on_release=do_load_stored)
            download_btn.bind(on_release=do_download)
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
        try:
            self.group_layout.clear_widgets()
            back_btn = Button(text="⬅ KATEGORİLERE DÖN", size_hint_y=None, height=dp(42), background_color=(0.8, 0.2, 0.2, 1))
            back_btn.bind(on_release=lambda inst: self.populate_groups())
            self.group_layout.add_widget(back_btn)

            ch_list = self.core.channels_by_group.get(group_name, [])
            grouped_shows = self.core.group_shows(ch_list)

            if isinstance(grouped_shows, dict):
                for show_name, idx_data in grouped_shows.items():
                    # 🧬 SAĞ LİSTEYE KIVY REFERANSLARININ SIZMASINI ÖNLEYEN GÜVENLİK BARİYERİ
                    safe_show_name = str(show_name).strip()
                    if not safe_show_name or safe_show_name.startswith('<kivy.') or 'font_' in safe_show_name or 'halign' in safe_show_name:
                        continue
                        
                    btn = Button(text=f"🎬 {safe_show_name}", size_hint_y=None, height=dp(40), background_color=(0.15, 0.15, 0.15, 1))
                    if isinstance(idx_data, dict):
                        first_ep_url = idx_data.get("url", "")
                        if first_ep_url:
                            btn.bind(on_release=lambda instance, url=first_ep_url, name=safe_show_name: self.start_playback(url, name))
                    self.group_layout.add_widget(btn)
            self.status_label.text = f"📂 {group_name} kategorisi yüklendi."
        except Exception as e:
            self.status_label.text = f"🚨 Sağ Liste Hatası: {str(e)[:25]}"

    def start_playback(self, url, name):
        try:
            self.status_label.text = f"⏳ Harici Motor Tetikleniyor: {name}"
            from kivy.utils import platform
            if platform == 'android':
                try:
                    from jnius import autoclass
                    Intent = autoclass('android.content.Intent')
                    Uri = autoclass('android.net.Uri')
                    PythonActivity = autoclass('org.kivy.android.PythonActivity')
                    currentActivity = PythonActivity.mActivity
                    video_uri = Uri.parse(url)
                    intent = Intent(Intent.ACTION_VIEW)
                    intent.setDataAndType(video_uri, "*/*")
                    chooser = Intent.createChooser(intent, "Yayını İzlemek İçin Oynatıcı Seçin:")
                    currentActivity.startActivity(chooser)
                    return
                except Exception as inner_err:
                    self.status_label.text = f"🚨 Android Köprü Hatası: {str(inner_err)[:20]}"
                    return
            if not self.video:
                self.video_container.clear_widgets()
                self.video = Video(source='', state='stop', options={'eos': 'loop'}, size_hint_y=1)
                self.video_container.add_widget(self.video)
            self.video.unload()
            self.video.source = url
            self.video.state = 'play'
            self.play_btn.text = "⏸ Duraklat"
            self.status_label.text = f"📺 Oynatılıyor: {name}"
        except Exception as e:
            self.status_label.text = f"🚨 Sistem Hatası: {str(e)[:20]}"

    def toggle_fullscreen_mode(self, instance=None):
        if not self.is_fullscreen:
            self.remove_widget(self.left_panel)
            self.center_panel.size_hint = (1, 1)
            self.is_fullscreen = True
            self.fs_btn.text = "📱 Normal Ekran"
        else:
            self.center_panel.size_hint = (0.70, 1)
            self.add_widget(self.left_panel, index=0)
            self.is_fullscreen = False
            self.fs_btn.text = "📺 Tam Ekran"

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

    def on_stop(self):
        try:
            from jnius import autoclass
            Activity = autoclass('org.kivy.android.PythonActivity').mActivity
            Build = autoclass('android.os.Build$VERSION')
            if Build.SDK_INT >= 26:
                Activity.enterPictureInPictureMode()
        except Exception:
            pass

if __name__ == "__main__":
    CinemaIPTVApp().run()






















































































































































