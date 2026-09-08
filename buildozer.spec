[app]
title = 答题助手
package.name = quizapp
package.domain = org.quizapp
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf
version = 1.0.0
requirements = python3,kivy==2.3.0,kivymd==1.2.0,openpyxl,requests,reportlab,python-docx,pillow
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.entrypoint = org.kivy.android.PythonActivity
android.accept_sdk_license = True
p4a.branch = master
build.dir = .buildozer

[buildozer]
log_level = 2
warn_on_root = 1
