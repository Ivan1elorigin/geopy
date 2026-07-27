import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import simplekml
from geopy.exc import GeocoderServiceError
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim


USER_AGENT = "curso-cartografia-digital-ivana/1.0"
UMBRAL_AMBIGUEDAD = 0.03

SERVIDORES_OSRM = {
    "coche": (
        "https://routing.openstreetmap.de/"
        "routed-car/route/v1/driving"
    ),
    "bici": (
        "https://routing.openstreetmap.de/"
        "routed-bike/route/v1/driving"
    ),
    "caminando": (
        "https://routing.openstreetmap.de/"
        "routed-foot/route/v1/driving"
    ),
}

PATRON_COORDENADAS = re.compile(
    r"^\s*"
    r"([+-]?(?:\d+(?:\.\d*)?|\.\d+))"
    r"\s*[,;]\s*"
    r"([+-]?(?:\d+(?:\.\d*)?|\.\d+))"
    r"\s*$"
)


@dataclass(frozen=True)
class PuntoRuta:
    entrada: str
    nombre: str
    latitud: float
    longitud: float


@dataclass(frozen=True)
class RutaCalculada:
    coordenadas: list[tuple[float, float]]
    distancia_km: float
    duracion_segundos: float


def normalizar_medio(medio: str) -> str:
    texto = unicodedata.normalize("NFKD", medio)
    texto = texto.encode("ascii", "ignore").decode("ascii").lower()
    medios = {
        "coche": "coche",
        "auto": "coche",
        "automovil": "coche",
        "bici": "bici",
        "bicicleta": "bici",
        "caminando": "caminando",
        "andando": "caminando",
        "pie": "caminando",
    }

    try:
        return medios[texto]
    except KeyError as error:
        raise argparse.ArgumentTypeError(
            "el medio debe ser coche, bici o caminando."
        ) from error


def interpretar_coordenadas(texto: str) -> tuple[float, float] | None:
    coincidencia = PATRON_COORDENADAS.fullmatch(texto)
    if coincidencia is None:
        return None

    latitud = float(coincidencia.group(1))
    longitud = float(coincidencia.group(2))

    if not -90 <= latitud <= 90:
        raise ValueError("la latitud debe estar entre -90 y 90.")
    if not -180 <= longitud <= 180:
        raise ValueError("la longitud debe estar entre -180 y 180.")

    return latitud, longitud


def es_resultado_ambiguo(resultados: list) -> bool:
    if len(resultados) < 2:
        return False

    importancia_1 = resultados[0].raw.get("importance")
    importancia_2 = resultados[1].raw.get("importance")

    if importancia_1 is None or importancia_2 is None:
        return True

    return abs(float(importancia_1) - float(importancia_2)) <= (
        UMBRAL_AMBIGUEDAD
    )


def resolver_puntos(
    entradas: list[str],
    idioma: str = "es",
    timeout: int = 15,
) -> list[PuntoRuta]:
    geolocalizador = Nominatim(
        user_agent=USER_AGENT,
        timeout=timeout,
    )
    geocode = RateLimiter(
        geolocalizador.geocode,
        min_delay_seconds=1,
        swallow_exceptions=False,
    )
    cache: dict[str, PuntoRuta | None] = {}
    puntos: list[PuntoRuta] = []

    for entrada_original in entradas:
        entrada = entrada_original.strip()
        if not entrada:
            print("Aviso: se ha ignorado una ubicación vacía.", file=sys.stderr)
            continue

        try:
            coordenadas = interpretar_coordenadas(entrada)
        except ValueError as error:
            print(f"Aviso: se ignora '{entrada}': {error}", file=sys.stderr)
            continue

        if coordenadas is not None:
            latitud, longitud = coordenadas
            puntos.append(
                PuntoRuta(
                    entrada=entrada,
                    nombre=f"{latitud:g}, {longitud:g}",
                    latitud=latitud,
                    longitud=longitud,
                )
            )
            continue

        clave_cache = entrada.casefold()
        if clave_cache in cache:
            punto_cacheado = cache[clave_cache]
            if punto_cacheado is not None:
                puntos.append(punto_cacheado)
            continue

        resultados = geocode(
            entrada,
            language=idioma,
            exactly_one=False,
            limit=2,
        )

        if not resultados:
            print(
                f"Aviso: no se ha encontrado '{entrada}'; se ignora.",
                file=sys.stderr,
            )
            cache[clave_cache] = None
            continue

        if not isinstance(resultados, list):
            resultados = [resultados]

        if es_resultado_ambiguo(resultados):
            candidatos = " | ".join(
                resultado.address for resultado in resultados[:2]
            )
            print(
                f"Aviso: '{entrada}' es ambiguo y se ignora. "
                f"Candidatos: {candidatos}",
                file=sys.stderr,
            )
            cache[clave_cache] = None
            continue

        resultado = resultados[0]
        punto = PuntoRuta(
            entrada=entrada,
            nombre=resultado.address,
            latitud=resultado.latitude,
            longitud=resultado.longitude,
        )
        cache[clave_cache] = punto
        puntos.append(punto)

    return puntos


def consultar_osrm(url: str, timeout: int) -> dict:
    peticion = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )

    try:
        with urlopen(peticion, timeout=timeout) as respuesta:
            return json.load(respuesta)
    except HTTPError as error:
        raise RuntimeError(
            f"el servidor de rutas respondió con HTTP {error.code}."
        ) from error
    except URLError as error:
        raise RuntimeError(
            f"no se pudo conectar con el servidor de rutas: {error.reason}"
        ) from error
    except JSONDecodeError as error:
        raise RuntimeError(
            "el servidor de rutas devolvió una respuesta no válida."
        ) from error


def convertir_ruta_osrm(ruta: dict) -> RutaCalculada:
    geometria = ruta.get("geometry", {}).get("coordinates")
    if not geometria:
        raise RuntimeError("la ruta recibida no contiene geometría.")

    coordenadas_kml = [
        (float(longitud), float(latitud))
        for longitud, latitud in geometria
    ]
    return RutaCalculada(
        coordenadas=coordenadas_kml,
        distancia_km=float(ruta["distance"]) / 1000,
        duracion_segundos=float(ruta["duration"]),
    )


def solicitar_ruta(
    puntos: list[PuntoRuta],
    medio: str,
    timeout: int = 30,
) -> RutaCalculada:
    if len(puntos) < 2:
        raise ValueError("se necesitan al menos dos puntos válidos.")

    coordenadas_url = ";".join(
        f"{punto.longitud:.7f},{punto.latitud:.7f}"
        for punto in puntos
    )
    parametros = urlencode(
        {
            "overview": "full",
            "geometries": "geojson",
            "steps": "false",
        }
    )
    url = f"{SERVIDORES_OSRM[medio]}/{coordenadas_url}?{parametros}"
    datos = consultar_osrm(url, timeout)

    if datos.get("code") != "Ok" or not datos.get("routes"):
        mensaje = datos.get("message", "no se encontró una ruta.")
        raise RuntimeError(f"error del servidor de rutas: {mensaje}")

    return convertir_ruta_osrm(datos["routes"][0])


def solicitar_ruta_optimizada(
    puntos: list[PuntoRuta],
    medio: str,
    timeout: int = 30,
) -> tuple[RutaCalculada, list[PuntoRuta]]:
    if len(puntos) < 2:
        raise ValueError("se necesitan al menos dos puntos válidos.")

    if len(puntos) == 2:
        return solicitar_ruta(puntos, medio, timeout), puntos

    coordenadas_url = ";".join(
        f"{punto.longitud:.7f},{punto.latitud:.7f}"
        for punto in puntos
    )
    parametros = urlencode(
        {
            "source": "first",
            "destination": "last",
            "roundtrip": "false",
            "overview": "full",
            "geometries": "geojson",
            "steps": "false",
        }
    )
    servidor_trip = SERVIDORES_OSRM[medio].replace(
        "/route/v1/",
        "/trip/v1/",
    )
    url = f"{servidor_trip}/{coordenadas_url}?{parametros}"
    datos = consultar_osrm(url, timeout)

    if datos.get("code") != "Ok" or not datos.get("trips"):
        mensaje = datos.get("message", "no se pudo optimizar la ruta.")
        raise RuntimeError(f"error del servidor de rutas: {mensaje}")

    waypoints = datos.get("waypoints", [])
    if len(waypoints) != len(puntos):
        raise RuntimeError(
            "el servidor no devolvió el orden de todos los puntos."
        )

    indices = [waypoint.get("waypoint_index") for waypoint in waypoints]
    if (
        any(not isinstance(indice, int) for indice in indices)
        or sorted(indices) != list(range(len(puntos)))
    ):
        raise RuntimeError(
            "el servidor devolvió un orden de puntos no válido."
        )

    puntos_ordenados = [
        punto
        for _, punto in sorted(
            zip(indices, puntos),
            key=lambda elemento: elemento[0],
        )
    ]
    ruta = convertir_ruta_osrm(datos["trips"][0])
    return ruta, puntos_ordenados


def limpiar_nombre(texto: str, longitud_maxima: int = 35) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"[^a-zA-Z0-9]+", "_", texto)
    return texto.strip("_").lower()[:longitud_maxima] or "punto"


def crear_nombre_ruta(
    primer_punto: PuntoRuta,
    ultimo_punto: PuntoRuta,
    distancia_km: float,
) -> str:
    origen = limpiar_nombre(primer_punto.entrada)
    destino = limpiar_nombre(ultimo_punto.entrada)
    distancia = f"{distancia_km:.2f}".rstrip("0").rstrip(".")
    distancia = distancia.replace(".", "_")
    return f"ruta_{origen}_{destino}_{distancia}km.kmz"


def guardar_ruta_kmz(
    puntos: list[PuntoRuta],
    ruta: RutaCalculada,
    medio: str,
    archivo_salida: str | None = None,
    optimizada: bool = False,
) -> Path:
    if archivo_salida is None:
        archivo_salida = crear_nombre_ruta(
            puntos[0],
            puntos[-1],
            ruta.distancia_km,
        )

    tipo_ruta = "Ruta optimizada" if optimizada else "Ruta"
    kml = simplekml.Kml()
    kml.document.name = (
        f"{tipo_ruta} de {ruta.distancia_km:.2f} km en {medio}"
    )
    kml.document.description = (
        f"{tipo_ruta} calculada con OSRM y datos de OpenStreetMap.<br>"
        "© OpenStreetMap contributors (ODbL).<br>"
        "Corregir el mapa: https://www.openstreetmap.org/fixthemap"
    )

    linea = kml.newlinestring(
        name=f"{tipo_ruta} en {medio}",
        description=(
            f"Distancia total: {ruta.distancia_km:.2f} km<br>"
            f"Duración estimada: {ruta.duracion_segundos / 60:.0f} minutos"
        ),
        coords=ruta.coordenadas,
    )
    linea.altitudemode = simplekml.AltitudeMode.clamptoground
    linea.style.linestyle.width = 5

    colores = {
        "coche": simplekml.Color.red,
        "bici": simplekml.Color.blue,
        "caminando": simplekml.Color.green,
    }
    linea.style.linestyle.color = colores[medio]

    for indice, punto_ruta in enumerate(puntos, start=1):
        punto = kml.newpoint(
            name=f"{indice}. {punto_ruta.nombre}",
            description=(
                f"Entrada: {punto_ruta.entrada}<br>"
                f"Latitud: {punto_ruta.latitud}<br>"
                f"Longitud: {punto_ruta.longitud}"
            ),
            coords=[(punto_ruta.longitud, punto_ruta.latitud)],
        )
        punto.style.iconstyle.color = colores[medio]
        punto.style.iconstyle.scale = 1.1

    ruta_salida = Path(archivo_salida).resolve()
    kml.savekmz(str(ruta_salida))
    return ruta_salida


def crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Calcula una ruta ordenada entre ubicaciones o coordenadas "
            "y la guarda como KMZ."
        )
    )
    parser.add_argument(
        "puntos",
        nargs="+",
        help=(
            "Ubicaciones entre comillas o coordenadas con el formato "
            "\"latitud,longitud\"."
        ),
    )
    parser.add_argument(
        "--medio",
        required=True,
        type=normalizar_medio,
        help="Medio de transporte: coche, bici o caminando.",
    )
    parser.add_argument(
        "--idioma",
        default="es",
        help="Idioma de las direcciones encontradas (por defecto: es).",
    )
    parser.add_argument(
        "--salida",
        help="Nombre opcional del archivo KMZ.",
    )
    parser.add_argument(
        "--optimiza",
        action="store_true",
        help=(
            "Optimiza las paradas intermedias manteniendo fijos "
            "el origen y el destino."
        ),
    )
    return parser


def main() -> None:
    argumentos = crear_parser().parse_args()

    try:
        puntos = resolver_puntos(
            argumentos.puntos,
            idioma=argumentos.idioma,
        )
        if len(puntos) < 2:
            raise ValueError(
                "quedan menos de dos puntos válidos después de ignorar "
                "los no encontrados o ambiguos."
            )

        if argumentos.optimiza:
            ruta, puntos = solicitar_ruta_optimizada(
                puntos,
                argumentos.medio,
            )
        else:
            ruta = solicitar_ruta(puntos, argumentos.medio)

        archivo = guardar_ruta_kmz(
            puntos,
            ruta,
            argumentos.medio,
            argumentos.salida,
            optimizada=argumentos.optimiza,
        )
    except (ValueError, RuntimeError, GeocoderServiceError) as error:
        raise SystemExit(f"Error: {error}") from error

    print(f"Puntos válidos: {len(puntos)}")
    print(f"Medio: {argumentos.medio}")
    print(
        "Optimización: "
        f"{'activada' if argumentos.optimiza else 'desactivada'}"
    )
    print("Orden final:")
    for indice, punto in enumerate(puntos, start=1):
        print(f"  {indice}. {punto.nombre}")
    print(f"Distancia total: {ruta.distancia_km:.2f} km")
    print(f"Duración estimada: {ruta.duracion_segundos / 60:.0f} minutos")
    print(f"Archivo creado: {archivo}")


if __name__ == "__main__":
    main()
