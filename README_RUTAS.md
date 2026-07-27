# 🗺️ Generador de rutas KMZ

El módulo `crear_ruta_kmz.py` calcula una ruta entre varias ubicaciones o
coordenadas y la guarda en un archivo KMZ compatible con Google Earth y otros
programas cartográficos.

La ruta respeta el orden de los puntos introducidos. No intenta encontrar un
orden más corto.

## 📦 Requisitos

Activa el entorno Conda del proyecto:

```powershell
conda activate geopyEnv
```

Instala las dependencias si todavía no están disponibles:

```powershell
python -m pip install geopy simplekml
```

El programa necesita conexión a Internet para buscar ubicaciones y calcular
la ruta.

## 🚗 Uso básico

Indica dos o más ubicaciones entre comillas y selecciona el medio de
transporte con `--medio`:

```powershell
python crear_ruta_kmz.py "Terrassa, España" "Sabadell, España" "Barcelona, España" --medio coche
```

El valor de `--medio` debe formar parte de la misma orden. Los medios
disponibles son:

| Valor | Medio |
|---|---|
| `coche` | 🚗 Automóvil |
| `bici` | 🚲 Bicicleta |
| `caminando` | 🚶 Desplazamiento a pie |

## 📍 Uso de coordenadas

Las coordenadas deben escribirse entre comillas con el formato:

```text
"latitud,longitud"
```

Ejemplo:

```powershell
python crear_ruta_kmz.py "41.5632,2.0089" "41.5463,2.1078" --medio bici
```

Es importante respetar el orden `latitud,longitud`.

## 🔀 Mezclar ubicaciones y coordenadas

Una misma ruta puede contener nombres y coordenadas:

```powershell
python crear_ruta_kmz.py "41.5632,2.0089" "Sabadell, España" "Barcelona, España" --medio caminando
```

Los puntos se recorren exactamente en el orden en el que aparecen en la
orden.

## 🌍 Seleccionar el idioma

La flag `--idioma` establece el idioma de las direcciones encontradas. El
valor predeterminado es `es`.

```powershell
python crear_ruta_kmz.py "Girona" "Perpignan" --medio coche --idioma ca
```

Algunos códigos habituales:

| Código | Idioma |
|---|---|
| `es` | Español |
| `ca` | Catalán |
| `en` | Inglés |
| `fr` | Francés |
| `de` | Alemán |

## 💾 Elegir el archivo de salida

El programa crea automáticamente un nombre formado por:

```text
ruta_ORIGEN_DESTINO_DISTANCIAkm.kmz
```

Ejemplo:

```text
ruta_terrassa_barcelona_35_42km.kmz
```

La distancia siempre se expresa en kilómetros. Para elegir otro nombre,
utiliza `--salida`:

```powershell
python crear_ruta_kmz.py "Terrassa" "Barcelona" --medio coche --salida ruta_trabajo.kmz
```

## ⚙️ Flags disponibles

| Argumento | Obligatorio | Descripción |
|---|---:|---|
| `puntos` | Sí | Lista ordenada de ubicaciones o coordenadas. |
| `--medio` | Sí | `coche`, `bici` o `caminando`. |
| `--idioma` | No | Idioma de las direcciones. Por defecto, `es`. |
| `--salida` | No | Nombre o ruta del archivo KMZ. |

Para consultar la ayuda desde la terminal:

```powershell
python crear_ruta_kmz.py --help
```

## ⚠️ Ubicaciones ignoradas

El programa muestra un aviso e ignora:

- Ubicaciones que no encuentra Nominatim.
- Ubicaciones cuyos dos mejores resultados tienen una relevancia muy
  parecida y, por tanto, se consideran ambiguas.
- Coordenadas con una latitud fuera de `-90` a `90`.
- Coordenadas con una longitud fuera de `-180` a `180`.

Después de ignorar estos elementos deben quedar al menos dos puntos válidos.
En caso contrario, no se genera ninguna ruta.

Para reducir ambigüedades, añade municipio, provincia o país:

```powershell
python crear_ruta_kmz.py "Sant Cugat del Vallès, Barcelona, España" "Vic, Barcelona, España" --medio coche
```

## 📄 Contenido del KMZ

El archivo generado contiene:

- La línea completa de la ruta.
- Un marcador numerado para cada parada válida.
- La distancia total en kilómetros.
- La duración estimada del recorrido.
- El medio de transporte empleado.
- La atribución correspondiente a OpenStreetMap.

## 🌐 Servicios utilizados

El cálculo de rutas utiliza
[`routing.openstreetmap.de`](https://routing.openstreetmap.de/about.html),
un servicio público basado en OSRM y datos de OpenStreetMap. No requiere una
clave ni tiene coste, pero está destinado a un uso normal y moderado:

- Máximo de una petición por segundo.
- No se permite el uso intensivo ni la extracción masiva.
- El servicio puede no estar disponible temporalmente.

La búsqueda de ubicaciones utiliza
[Nominatim](https://operations.osmfoundation.org/policies/nominatim/), que
también limita las consultas a una petición por segundo. El programa realiza
las búsquedas de forma secuencial para respetar este límite.

## 🧭 Ejemplos completos

Ruta en coche:

```powershell
python crear_ruta_kmz.py "Terrassa, España" "Sabadell, España" "Barcelona, España" --medio coche
```

Ruta en bicicleta con coordenadas:

```powershell
python crear_ruta_kmz.py "41.5632,2.0089" "41.5463,2.1078" --medio bici --salida ruta_bici.kmz
```

Ruta a pie combinando tipos de punto:

```powershell
python crear_ruta_kmz.py "Plaça de Catalunya, Barcelona" "41.3870,2.1701" "Sagrada Família, Barcelona" --medio caminando
```
