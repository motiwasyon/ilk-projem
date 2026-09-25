[app]
title = Selge TV
package.name = selgetv
package.domain = org.selgeproje
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.7

# 🚀 GEREKSİNİMLER: Sunucu kilitlenmelerini önlemek için hafifletilmiş modüller
requirements = python3, kivy, pyjnius, requests, certifi

orientation = all
fullscreen = 1

# =============================================================================
# Android Konfigürasyonu
# =============================================================================
android.accept_sdk_license = True
android.permissions = INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE
android.api = 33
android.minapi = 26

# 🛠️ SDK Build-Tools araçları Android 13 ile tam uyumlu kararlı sürüme sabitlendi
android.build_tools_version = 33.0.2

android.enable_androidx = True

android.add_compile_options = sourceCompatibility = JavaVersion.VERSION_1_8, targetCompatibility = JavaVersion.VERSION_1_8
android.manifest.application_arguments = android:usesCleartextTraffic="true"

# 🎬 Video oynatma işi tamamen harici Just Player'a paslandığı için ExoPlayer kütüphaneleri kaldırıldı
android.gradle_dependencies =

android.manifest.intent_filters = [ {"action": "android.intent.action.MAIN", "category": ["android.intent.category.LEANBACK_LAUNCHER", "android.intent.category.LAUNCHER"]} ]
android.archs = armeabi-v7a, arm64-v8a

# ⚡ NİHAİ ÇÖZÜM: 15 dakikalık sınırı aşan tüm gereksiz devasa harici grafik kütüphanelerinin (libavif, lcms vb.) indirilmesi engellendi!
android.p4a_extra_args = --exclude-libs=libestdc++,test,unittest,tkinter,pydoc,distutils,libjxl,brotli,highway,libavif,lcms,lodepng,sjpeg,skcms,googletest --no-deps

p4a.branch = release-2024.01.21
android.ndk = 25b
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
