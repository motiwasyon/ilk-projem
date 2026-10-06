[app]
title = Selge TV
package.name = selgetv
package.domain = org.selgeproje
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,m3u
version = 1.8
source.exclude_dirs = tests, test, bst, bin, venv, env

# 🚀 GEREKSİNİMLER
requirements = python3,kivy==2.3.0,openssl,requests,urllib3,chardet,certifi,idna

orientation = landscape
fullscreen = 1

# =============================================================================
# Android Konfigürasyonu
# =============================================================================
android.accept_sdk_license = True
android.permissions = INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE, READ_MEDIA_VIDEO, READ_MEDIA_IMAGES
android.api = 33
android.minapi = 24
android.ndk_api = 24
android.build_tools_version = 33.0.2
android.enable_androidx = True

android.add_compile_options = sourceCompatibility = JavaVersion.VERSION_1_8, targetCompatibility = JavaVersion.VERSION_1_8
android.manifest.application_arguments = android:usesCleartextTraffic="true"
android.gradle_dependencies =

# ÇÖKMEYE SEBEP OLAN INTENT_FILTERS SATIRI KALDIRILDI! (YUKARIDAKİ WORKFLOW OTOMATİK HALLEDECEK)

android.archs = arm64-v8a
p4a.branch = release-2024.01.21
android.ndk = 25b
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1

