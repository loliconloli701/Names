[app]
title = Photo Diary Luxury
package.name = photodiary
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

# --- ГЛАВНОЕ ИСПРАВЛЕНИЕ ---
# Используем Kivy 2.3.0 (совместим с Python 3.10+ и Cython 3)
requirements = python3,kivy==2.3.0,kivymd,pillow,numpy,android

# Разрешения
android.permissions = CAMERA,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# --- ОПТИМИЗАЦИЯ ПАМЯТИ ---
# Собираем только под 64-битные процессоры (все телефоны с 2016 года).
# Это ускорит сборку в 2 раза и спасет от вылетов по памяти.
android.archs = arm64-v8a

# Настройки экрана
orientation = portrait
fullscreen = 0
android.allow_backup = True

# Используем стабильную ветку python-for-android
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
