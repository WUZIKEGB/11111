[app]
title = 污水池控制系统
package.name = sewagecontrol
package.domain = org.sewage
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

requirements = python3==3.9,kivy==2.3.0,paho-mqtt==1.6.1,certifi,chardet,filetype,idna,urllib3,requests,six

orientation = portrait
fullscreen = 0

android.permissions = INTERNET, ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 26
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True

android.allow_backup = True
android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = 1
