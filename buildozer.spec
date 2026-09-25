[app]
title = Selge TV
package.name = selgetv
package.domain = org.selgeproje
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.7

# 🚀 GEREKSİNİMLER: Sunucu ve Python 3.11 sürümleri sabitlendi
requirements = python3==3.11.9, hostpython3==3.11.9, kivy==2.3.0, pyjnius, requests, certifi

orientation = all
fullscreen = 1

# =============================================================================
# Android Konfigürasyonu
# =============================================================================
android.accept_sdk_license = True
android.permissions = INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE
android.api = 33
android.minapi = 26

# 🛠️ KESİN ÇÖZÜM: Kararsız Build-Tools 37 yerine Android 13 (API 33) ile tam uyumlu resmi sürüm kilitlendi
android.build_tools_version = 33.0.2

android.enable_androidx = True

android.add_compile_options = sourceCompatibility = JavaVersion.VERSION_1_8, targetCompatibility = JavaVersion.VERSION_1_8
android.manifest.application_arguments = android:usesCleartextTraffic="true"
android.gradle_dependencies = androidx.media3:media3-exoplayer:1.1.0, androidx.media3:media3-ui:1.1.0
android.manifest.intent_filters = [ {"action": "android.intent.action.MAIN", "category": ["android.intent.category.LEANBACK_LAUNCHER", "android.intent.category.LAUNCHER"]} ]
android.archs = armeabi-v7a, arm64-v8a

# ⚡ KESİN ÇÖZÜM SATIRI: Sunucuyu kilitleyen binlerce ağır test ve harici kütüphane dosyasını tamamen pas geçer!
android.p4a_extra_args = --exclude-libs=libestdc++,test,unittest,tkinter,pydoc,distutils,libjxl,brotli,highway --no-deps

p4a.branch = release-2024.01.21
android.ndk = 25b
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
