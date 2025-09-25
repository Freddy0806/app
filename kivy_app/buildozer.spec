[app]
title = Simulador
package.name = simulador
package.domain = org.frea.simulador
source.dir = .
source.include_exts = py,kv,md
version = 0.1.0
requirements = python3,kivy==2.3.0,kivymd==1.2.0
orientation = portrait
fullscreen = 0
android.archs = arm64-v8a, armeabi-v7a
android.minapi = 21
android.api = 33

# Opcional: descomenta si agregas un ícono o imagen de inicio
# icon.filename = %(source.dir)s/data/icon.png
# presplash.filename = %(source.dir)s/data/presplash.png

# Firma debug por defecto
android.release_artifact = apk

[buildozer]
log_level = 2
warn_on_root = 1
