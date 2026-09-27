
[app]
title = Selge TV
package.name = selgetv
package.domain = org.selgeproje
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.7

# 🚀 GEREKSİNİMLER
requirements = python3, kivy==2.3.0, pyjnius, requests, certifi, urllib3, idna, charset-normalizer, openssl


orientation = all
fullscreen = 1

# =============================================================================
# Android Konfigürasyonu
# =============================================================================
android.accept_sdk_license = True
android.permissions = INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 26
android.build_tools_version = 33.0.2
android.enable_androidx = True

android.add_compile_options = sourceCompatibility = JavaVersion.VERSION_1_8, targetCompatibility = JavaVersion.VERSION_1_8
android.manifest.application_arguments = android:usesCleartextTraffic="true"
android.gradle_dependencies =

android.manifest.intent_filters = [ {"action": "android.intent.action.MAIN", "category": ["android.intent.category.LEANBACK_LAUNCHER", "android.intent.category.LAUNCHER"]} ]
android.archs = armeabi-v7a, arm64-v8a

# ⚡ NİHAİ ÇÖZÜM: Gereksiz kütüphaneler hariç tutuldu
android.p4a_extra_args = --exclude-libs=libestdc++,test,unittest,tkinter,pydoc,distutils,libjxl,brotli,highway,libavif,lcms,lodepng,sjpeg,skcms,googletest,libwebp,libtiff,dav1d,jpeg,png,webp,tiff,brotli --no-deps


p4a.branch = master
android.ndk = 25b
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
