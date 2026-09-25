# -*- coding: utf-8 -*-
import os
import requests
import re
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.utils import platform
from kivy.storage.jsonstore import JsonStore
from kivy.clock import Clock

PLAYLIST_FILE = "playlist.m3u"

# 📺 TV BOX OPTİMİZASYONU: Kumanda ile üzerine gelindiğinde renk değiştiren özel buton sınıfı
class TVBoxButton(Button):
    def __init__(self, default_color=(0.15, 0.4, 0.6, 1), **kwargs):
        super(TVBoxButton, self).__init__(**kwargs)
        self.default_color = default_color
        self.background_color = self.default_color
        # Kumanda odağı değiştiğinde rengi güncelle (Seçilince Parlak Turuncu Olur)
        self.bind(focus=self.on_button_focus)

    def on_button_focus(self, instance, value):
        if value:
            self.background_color = (1, 0.5, 0, 1)  # Kumanda ile üstüne gelindiğinde Turuncu
        else:
            self.background_color = self.default_color  # Normal renk

class SelgeTVPremiumApp(App):
    def build(self):
        self.title = "Selge TV Premium v1.6"
        
        self.store = JsonStore('selgetv_settings.json')
        saved_ip = "192.168.1.208"
        saved_single_url = ""
        
        if self.store.exists('settings'):
            saved_ip = self.store.get('settings').get('ip', saved_ip)
            saved_single_url = self.store.get('settings').get('single_url', saved_single_url)
            
        self.all_channels_by_group = {"✨ TÜM KANALLAR": []}
        self.current_group_channels = []
        
        self.main_layout = BoxLayout(orientation='horizontal', spacing=5, padding=5)
        
        # 1. SOL PANEL: KATEGORİLER VE KANALLAR
        self.left_panel = BoxLayout(orientation='vertical', size_hint=(0.4, 1), spacing=5)
        
        self.left_panel.add_widget(Label(text="📁 KATEGORİLER / GRUPLAR", size_hint_y=None, height=30, color=(0, 0.7, 1, 1)))
        self.group_scroll = ScrollView(size_hint=(1, 0.4))
        self.group_grid = GridLayout(cols=1, size_hint_y=None, spacing=3)
        self.group_grid.bind(minimum_height=self.group_grid.setter('height'))
        self.group_scroll.add_widget(self.group_grid)
        self.left_panel.add_widget(self.group_scroll)
        
        self.left_panel.add_widget(Label(text="🎬 İÇERİK LİSTESİ", size_hint_y=None, height=30, color=(0, 1, 0.5, 1)))
        self.channel_scroll = ScrollView(size_hint=(1, 0.6))
        self.channel_grid = GridLayout(cols=1, size_hint_y=None, spacing=3)
        self.channel_grid.bind(minimum_height=self.channel_grid.setter('height'))
        self.channel_scroll.add_widget(self.channel_grid)
        self.left_panel.add_widget(self.channel_scroll)
        
        self.main_layout.add_widget(self.left_panel)
        
        # 2. SAĞ PANEL: SEKMELİ GİRİŞ VE KONTROL ALANI
        self.right_panel = BoxLayout(orientation='vertical', size_hint=(0.6, 1), padding=10, spacing=10)
        self.tab_panel = TabbedPanel(do_default_tab=False, size_hint=(1, 0.4))
        
        # Sekme A: Bilgisayardan Veri Çekme Alanı
        self.tab_pc = TabbedPanelItem(text='🌐 PC Bağlantısı')
        pc_layout = BoxLayout(orientation='vertical', padding=10, spacing=5)
        ip_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=45, spacing=5)
        ip_row.add_widget(Label(text="PC IP:", size_hint_x=0.2))
        self.ip_input = TextInput(text=saved_ip, multiline=False, size_hint_x=0.5, font_size=16)
        ip_row.add_widget(self.ip_input)
        
        connect_btn = TVBoxButton(text="Listeyi Çek", size_hint_x=0.3, default_color=(0, 0.5, 0.8, 1))
        connect_btn.bind(on_release=lambda instance: self.download_m3u_from_pc())
        ip_row.add_widget(connect_btn)
        pc_layout.add_widget(ip_row)
        pc_layout.add_widget(Label(text="PC'deki özel klasörden playlist.m3u dosyasını Wi-Fi ile indirir.", font_size=12))
        self.tab_pc.add_widget(pc_layout)
        self.tab_panel.add_tab(self.tab_pc)
        
        # Sekme B: Tekli Link Oynatma Alanı
        self.tab_single = TabbedPanelItem(text='🔗 Tekli Link')
        single_layout = BoxLayout(orientation='vertical', padding=10, spacing=5)
        link_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=45, spacing=5)
        link_row.add_widget(Label(text="Link:", size_hint_x=0.15))
        self.single_url_input = TextInput(text=saved_single_url, placeholder_text="http://...", multiline=False, size_hint_x=0.5, font_size=14)
        link_row.add_widget(self.single_url_input)
        
        play_single_btn = TVBoxButton(text="▶ Yayını Aç", size_hint_x=0.35, default_color=(0, 0.7, 0, 1))
        play_single_btn.bind(on_release=lambda instance: self.play_single_link())
        link_row.add_widget(play_single_btn)
        single_layout.add_widget(link_row)
        single_layout.add_widget(Label(text="Canlı yayın veya maç linkini açar.", font_size=12))
        self.tab_single.add_widget(single_layout)
        self.tab_panel.add_tab(self.tab_single)
        
        self.right_panel.add_widget(self.tab_panel)
        
        # Arama Çubuğu
        search_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=45, spacing=5)
        search_layout.add_widget(Label(text="🔍 Ara:", size_hint_x=0.2))
        self.search_bar = TextInput(placeholder_text="Kanal adı yazıp Enter'a basın...", multiline=False, size_hint_x=0.8)
        self.search_bar.bind(on_text_validate=self.filter_channels_by_search)
        search_layout.add_widget(self.search_bar)
        self.right_panel.add_widget(search_layout)
        
        self.status_label = Label(text="Selge TV Aktif. Xiaomi TV Box modunda kumanda desteklenir.", halign="center", font_size=14)
        self.right_panel.add_widget(self.status_label)
        self.main_layout.add_widget(self.right_panel)
        
        return self.main_layout

    def on_start(self):
        Clock.schedule_once(lambda dt: self.parse_m3u_file(), 0.5)
   
    def download_m3u_from_pc(self):
        current_ip = self.ip_input.text.strip()
        self.store.put('settings', ip=current_ip, single_url=self.single_url_input.text.strip())
        self.status_label.text = f"⏳ {current_ip} sunucusundan liste isteniyor..."
        
        def run_download():
            m3u_url = f"http://{current_ip}:9090/playlist.m3u"
            try:
                r = requests.get(m3u_url, timeout=5)
                if r.status_code == 200:
                    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
                        f.write(r.text)
                    Clock.schedule_once(lambda dt: self.on_download_success(), 0)
                else:
                    Clock.schedule_once(lambda dt: self.on_download_error(f"❌ Sunucu Hatası: {r.status_code}"), 0)
            except Exception:
                Clock.schedule_once(lambda dt: self.on_download_error(f"❌ Bilgisayara Bağlanılamadı!"), 0)
        
        threading.Thread(target=run_download, daemon=True).start()

    def on_download_success(self):
        self.status_label.text = "✅ Liste Başarıyla Güncellendi!"
        self.parse_m3u_file()

    def on_download_error(self, message):
        self.status_label.text = message

    def parse_m3u_file(self):
        self.all_channels_by_group = {"✨ TÜM KANALLAR": []}
        if os.path.exists(PLAYLIST_FILE):
            try:
                with open(PLAYLIST_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                channel_name = "Bilinmeyen Kanal"
                group_name = "Diğer"
                for line in lines:
                    line = line.strip()
                    if line.startswith("#EXTINF"):
                        g_match = re.search(r'group-title="([^"]+)"', line)
                        group_name = g_match.group(1).strip() if g_match else "Diğer"
                        if "," in line:
                            channel_name = line.split(",", 1)[-1].strip()
                    elif line.startswith("http"):
                        channel_data = {"name": channel_name, "url": line}
                        if group_name not in self.all_channels_by_group:
                            self.all_channels_by_group[group_name] = []
                        self.all_channels_by_group[group_name].append(channel_data)
                        self.all_channels_by_group["✨ TÜM KANALLAR"].append(channel_data)
                        channel_name = "Bilinmeyen Kanal"
            except Exception:
                pass
        self.group_grid.clear_widgets()
        if len(self.all_channels_by_group) > 1:
            for g in sorted(self.all_channels_by_group.keys()):
                count = len(self.all_channels_by_group[g])
                btn = TVBoxButton(text=f"{g} ({count})", size_hint_y=None, height=45, default_color=(0.2, 0.2, 0.2, 1))
                btn.bind(on_release=lambda instance, name=g: self.load_channels_of_group(name))
                self.group_grid.add_widget(btn)
            self.load_channels_of_group("✨ TÜM KANALLAR")
        else:
            self.status_label.text = "📂 Kayıtlı liste bulunamadı!\nLütfen PC'den liste çekin."

    def load_channels_of_group(self, group_name):
        self.channel_grid.clear_widgets()
        self.current_group_channels = self.all_channels_by_group.get(group_name, [])
        self.status_label.text = f"📂 Kategori: {group_name}\nToplam {len(self.current_group_channels)} içerik listelendi."
        for channel in self.current_group_channels:
            btn = TVBoxButton(text=channel['name'], size_hint_y=None, height=50, default_color=(0.15, 0.4, 0.6, 1))
            btn.bind(on_release=lambda instance, url=channel['url']: self.play_iptv_channel(url))
            self.channel_grid.add_widget(btn)

    def filter_channels_by_search(self, instance):
        query = self.search_bar.text.strip().lower()
        if not query:
            self.load_channels_of_group("✨ TÜM KANALLAR")
            return
            
        self.channel_grid.clear_widgets()
        match_count = 0
        for channel in self.all_channels_by_group["✨ TÜM KANALLAR"]:
            if query in channel['name'].lower():
                match_count += 1
                btn = TVBoxButton(text=channel['name'], size_hint_y=None, height=50, default_color=(0.15, 0.4, 0.6, 1))
                btn.bind(on_release=lambda instance, url=channel['url']: self.play_iptv_channel(url))
                self.channel_grid.add_widget(btn)
        self.status_label.text = f"🔍 Arama: '{query}'\n{match_count} adet kanal bulundu."

    def play_single_link(self):
        url = self.single_url_input.text.strip()
        if not url or not url.startswith("http"):
            self.status_label.text = "❌ Geçersiz link!"
            return
        self.store.put('settings', ip=self.ip_input.text.strip(), single_url=url)
        self.status_label.text = f"🎬 Tekli Link Başlatılıyor:\n{url}"
        self.play_iptv_channel(url)

    def play_iptv_channel(self, stream_url):
        if platform == 'android':
            try:
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                
                video_uri = Uri.parse(stream_url)
                intent = Intent(Intent.ACTION_VIEW)
                
                if ".m3u8" in stream_url.lower():
                    intent.setDataAndType(video_uri, "application/x-mpegURL")
                else:
                    intent.setDataAndType(video_uri, "video/*")
                
                # 🚀 Xiaomi TV Box için Just Player zorlaması
                intent.setPackage("com.brouken.player")
                current_activity = PythonActivity.mActivity
                current_activity.startActivity(intent)
            except Exception:
                try:
                    self.status_label.text = "ℹ️ Just Player bulunamadı. Android TV Play Store açılıyor..."
                    market_uri = Uri.parse("market://details?id=com.brouken.player")
                    market_intent = Intent(Intent.ACTION_VIEW, market_uri)
                    current_activity.startActivity(market_intent)
                except Exception as e2:
                    self.status_label.text = f"❌ Mağaza Hatası: {e2}"

if __name__ == '__main__':
    SelgeTVPremiumApp().run()
