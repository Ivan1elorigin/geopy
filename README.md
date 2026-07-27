# GeoPy · Cartografía sencilla en formato KMZ

Convierte lugares, coordenadas y recorridos en mapas listos para explorar.
Este proyecto reúne varias herramientas de línea de comandos para **localizar
puntos**, **dibujar áreas de influencia** y **calcular rutas**, exportando el
resultado a archivos KMZ compatibles con Google Earth y otras aplicaciones
SIG.

No requiere claves de API: las búsquedas se apoyan en Nominatim y las rutas en
OSRM, ambos sobre datos de OpenStreetMap.

## ✨ Qué puedes hacer

- Buscar una dirección o utilizar directamente sus coordenadas.
- Crear áreas circulares geodésicas alrededor de cualquier punto.
- Expresar el radio en kilómetros, metros o millas, o indicar una superficie
  en hectáreas.
- Calcular rutas en coche, bicicleta o a pie.
- Combinar nombres de lugares y coordenadas en un mismo recorrido.
- Optimizar las paradas intermedias manteniendo fijos el origen y el destino.
- Generar archivos KMZ con estilos, marcadores y datos del recorrido.

## 📦 Requisitos e instalación

Necesitas **Python 3.10 o posterior** y conexión a Internet para resolver
ubicaciones y calcular rutas.

```bash
git clone <URL_DEL_REPOSITORIO>
cd geopy
python -m venv .venv
```

Activa el entorno virtual:

```bash
# Linux y macOS
source .venv/bin/activate

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
```

Instala las dependencias:

```bash
python -m pip install geopy simplekml
```

> En algunos sistemas el ejecutable se llama `python3`; puedes sustituir
> `python` por `python3` en todos los ejemplos.

## 🚀 Primeros pasos

### Crear un área desde un lugar

Genera un círculo geodésico de 10 km alrededor de Terrassa:

```bash
python buscar_ubicacion.py "Terrassa, Barcelona, España" --radio 10 --unidad km
```

También puedes trabajar en metros, millas o hectáreas:

```bash
python buscar_ubicacion.py "Sagrada Família, Barcelona" --radio 750 --unidad m
python buscar_ubicacion.py "Parc Natural de Sant Llorenç del Munt" --radio 200 --unidad ha
```

Cuando se usan hectáreas, el valor representa la superficie y el programa
calcula el radio del círculo equivalente.

### Crear un área desde coordenadas

El orden esperado es `latitud longitud`:

```bash
python buscar_ubicacion.py --coordenadas 41.5632 2.0089 --radio 5 --unidad km
```

Puedes controlar el nombre de salida y la suavidad del círculo:

```bash
python buscar_ubicacion.py --coordenadas 41.5632 2.0089 \
  --radio 5 --salida area_personalizada.kmz --vertices 360
```

### Calcular una ruta

Indica al menos dos puntos y el medio de transporte:

```bash
python crear_ruta_kmz.py \
  "Terrassa, España" "Sabadell, España" "Barcelona, España" \
  --medio coche
```

Los medios disponibles son `coche`, `bici` y `caminando`. También puedes
mezclar lugares con coordenadas:

```bash
python crear_ruta_kmz.py \
  "41.5632,2.0089" "Sabadell, España" "Barcelona, España" \
  --medio bici --salida ruta_bici.kmz
```

Para reorganizar las paradas intermedias en busca de un recorrido más corto,
añade `--optimiza`:

```bash
python crear_ruta_kmz.py \
  "Terrassa" "Barcelona" "Sabadell" "Girona" \
  --medio coche --optimiza
```

La optimización conserva el primer punto como origen y el último como destino.
Consulta la [guía completa de rutas](README_RUTAS.md) para ver todas las
opciones y más ejemplos.

## 🧰 Herramientas incluidas

| Archivo | Función |
|---|---|
| `buscar_ubicacion.py` | Geocodifica lugares o acepta coordenadas y genera su área de influencia. |
| `crear_area_kmz.py` | Contiene la función reutilizable que construye círculos geodésicos y los exporta a KMZ. |
| `crear_ruta_kmz.py` | Resuelve puntos, calcula u optimiza recorridos y crea un KMZ con la ruta. |
| `README_RUTAS.md` | Documentación detallada del planificador de rutas. |

Cada comando ofrece ayuda integrada:

```bash
python buscar_ubicacion.py --help
python crear_ruta_kmz.py --help
```

## 🗺️ Resultado

Los archivos `.kmz` se guardan en el directorio actual, salvo que indiques
otra ruta con `--salida`. Puedes abrirlos directamente en Google Earth o
importarlos en una aplicación cartográfica compatible.

Las áreas incluyen el punto central, un contorno y un relleno transparente.
Las rutas incorporan la geometría completa, marcadores numerados, distancia
total, duración estimada y el medio de transporte utilizado.

## 🌐 Servicios y uso responsable

- **Nominatim** convierte nombres de lugares en coordenadas.
- **OSRM** calcula las rutas sobre la red de OpenStreetMap.
- **OpenStreetMap** aporta los datos cartográficos.

Son servicios públicos y pueden limitar las peticiones o no estar disponibles
temporalmente. Utiliza la herramienta de forma moderada y añade suficiente
contexto —municipio, provincia o país— cuando una ubicación pueda ser
ambigua.

---

Hecho para transformar unas pocas coordenadas en mapas claros, portátiles y
fáciles de compartir.
