import argparse
import re
import unicodedata
from pathlib import Path

from geopy.exc import GeocoderServiceError
from geopy.geocoders import Nominatim

from crear_area_kmz import crear_area_kmz


def buscar_coordenadas(
    ubicacion: str,
    timeout: int = 10,
) -> tuple[float, float, str]:
    """
    Busca una ubicación y devuelve latitud, longitud y dirección completa.
    """
    ubicacion = ubicacion.strip()
    if not ubicacion:
        raise ValueError("La ubicación de búsqueda no puede estar vacía.")

    geolocalizador = Nominatim(
        user_agent="curso-geopy-ivan-a/1.0",
        timeout=timeout,
    )
    resultado = geolocalizador.geocode(
        ubicacion,
        language="es",
        exactly_one=True,
    )

    if resultado is None:
        raise ValueError(
            f"No se encontraron coordenadas para: {ubicacion}"
        )

    return resultado.latitude, resultado.longitude, resultado.address


def crear_nombre_kmz(ubicacion: str, radio_km: float) -> str:
    """
    Crea un nombre de archivo válido a partir de la ubicación buscada.
    """
    texto_sin_acentos = unicodedata.normalize("NFKD", ubicacion)
    texto_ascii = texto_sin_acentos.encode("ascii", "ignore").decode("ascii")
    nombre = re.sub(r"[^a-zA-Z0-9]+", "_", texto_ascii)
    nombre = nombre.strip("_").lower()[:80]

    if not nombre:
        nombre = "ubicacion"

    radio = f"{radio_km:g}".replace(".", "_")
    return f"{nombre}_{radio}km.kmz"


def crear_area_desde_ubicacion(
    ubicacion: str,
    radio_km: float,
    archivo_salida: str | None = None,
    numero_vertices: int = 180,
) -> tuple[Path, float, float, str]:
    """
    Busca una ubicación y crea un KMZ con un área a su alrededor.
    """
    latitud, longitud, direccion = buscar_coordenadas(ubicacion)

    if archivo_salida is None:
        archivo_salida = crear_nombre_kmz(ubicacion, radio_km)

    ruta_kmz = crear_area_kmz(
        latitud=latitud,
        longitud=longitud,
        radio_km=radio_km,
        archivo_salida=archivo_salida,
        numero_vertices=numero_vertices,
    )

    return ruta_kmz, latitud, longitud, direccion


def crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Busca las coordenadas de una ubicación y genera un área KMZ."
        )
    )
    parser.add_argument(
        "ubicacion",
        help='Dirección o lugar que se quiere buscar, entre comillas.',
    )
    parser.add_argument(
        "--radio",
        type=float,
        default=10,
        help="Radio del área en kilómetros (por defecto: 10).",
    )
    parser.add_argument(
        "--salida",
        help="Nombre opcional del archivo KMZ de salida.",
    )
    parser.add_argument(
        "--vertices",
        type=int,
        default=180,
        help="Número de vértices del círculo (por defecto: 180).",
    )
    return parser


def main() -> None:
    argumentos = crear_parser().parse_args()

    try:
        ruta, latitud, longitud, direccion = crear_area_desde_ubicacion(
            ubicacion=argumentos.ubicacion,
            radio_km=argumentos.radio,
            archivo_salida=argumentos.salida,
            numero_vertices=argumentos.vertices,
        )
    except (ValueError, GeocoderServiceError) as error:
        raise SystemExit(f"Error: {error}") from error

    print(f"Ubicación encontrada: {direccion}")
    print(f"Latitud: {latitud}")
    print(f"Longitud: {longitud}")
    print(f"Archivo creado: {ruta}")


if __name__ == "__main__":
    main()
