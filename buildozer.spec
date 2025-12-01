[app]
title = Photo Diary Luxury
package.name = photodiary
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

# ВАЖНО: Список библиотек
requirements = python3,kivy==2.2.0,kivymd,pillow,numpy,android

# Разрешения для Android (Камера и память)
android.permissions = CAMERA,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# Настройки экрана
orientation = portrait
fullscreen = 0
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

# Дополнительные настройки
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
