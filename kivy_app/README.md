# Simulador (KivyMD)

Esta es una versión móvil (Kivy/KivyMD) del simulador. Incluye pestañas:

- RNG: Generador congruencial (mixto o multiplicativo)
- Números: Vista de los números generados
- Variables: Genera variables Exponencial, Normal, Poisson, Geométrica y Binomial a partir de índices de U
- Var. Generadas: Resumen de variables y metadatos
- Colas: Tabla de colas a partir de dos variables (llegada y atención)
- Entregas: Simulación de reabastecimiento con capacidad máxima, pedido/entrega y costos

## Requisitos locales

Se recomienda un entorno virtual. Instala dependencias:

```
pip install -r requirements.txt
```

Ejecutar en PC:

```
python main.py
```

## Campos y uso (Entregas)
- Demanda: lista separada por comas, ej: `10,12,9,11`
- Inv. inicial
- Pedido (cantidad)
- Frecuencia (días)
- Capacidad máx.
- Costos: ordenar, inventario/u, faltante/u

La tabla muestra: Día, Pedido, Entrega, Inventario inicial, Demanda, Ventas, Inventario final, Costos y Promedio.

La entrega recibida está limitada por `capacidad máx. - inventario actual`.

## Compilar a Android (APK) con Buildozer

1) Usar Linux o WSL2 en Windows.
2) Instalar buildozer y dependencias (ver guía oficial):
   https://buildozer.readthedocs.io
3) Inicializar proyecto (desde `kivy_app/`):

```
buildozer init
```

4) Editar `buildozer.spec`:

- requirements = python3,kivy==2.3.0,kivymd==1.2.0
- source.include_exts = py,kv,md
- title = Simulador
- package.name = simulador
- package.domain = org.tu.dominio

5) Construir APK:

```
buildozer android debug
```

El APK quedará en `bin/`. Transfiérelo al teléfono e instálalo (habilitar orígenes desconocidos).

## Notas
- MDDataTable incluye scroll; además se agrega `ScrollView` externo para scroll horizontal en móvil.
- Las pestañas comparten estado en memoria (números y variables generadas) mientras corre la app.
- Si necesitas persistencia (guardar/cargar), se puede agregar fácilmente (JSON en almacenamiento local).
