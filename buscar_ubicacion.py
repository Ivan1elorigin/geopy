import argparse
import re
import unicodedata
from pathlib import Path

from geopy.exc import GeocoderServiceError
from geopy.geocoders import Nominatim

from crear_area_kmz import crear_area_kmz


def buscar_coordenadas(
    ubicacion: str,
    idioma: str = "es",
    timeout: int = 10,
) -> tuple[float, float, str]:
    """
    Busca una ubicación y devuelve latitud, longitud y dirección completa.
    """
    ubicacion = ubicacion.strip()
    if not ubicacion:
        raise ValueError("La ubicación de búsqueda no puede estar vacía.")

    idioma = idioma.strip()
    if not idioma:
        raise ValueError("El idioma no puede estar vacío.")

    geolocalizador = Nominatim(
        user_agent="curso-geopy-ivan-a/1.0",
        timeout=timeout,
    )
    resultado = geolocalizador.geocode(
        ubicacion,
        language=idioma,
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


def crear_nombre_coordenadas_kmz(
    latitud: float,
    longitud: float,
    radio_km: float,
) -> str:
    latitud_texto = f"{abs(latitud):g}".replace(".", "_")
    longitud_texto = f"{abs(longitud):g}".replace(".", "_")
    hemisferio_latitud = "n" if latitud >= 0 else "s"
    hemisferio_longitud = "e" if longitud >= 0 else "o"
    radio = f"{radio_km:g}".replace(".", "_")

    return (
        f"coordenadas_{latitud_texto}{hemisferio_latitud}_"
        f"{longitud_texto}{hemisferio_longitud}_{radio}km.kmz"
    )


def crear_area_desde_ubicacion(
    ubicacion: str,
    radio_km: float,
    archivo_salida: str | None = None,
    numero_vertices: int = 180,
    idioma: str = "es",
) -> tuple[Path, float, float, str]:
    """
    Busca una ubicación y crea un KMZ con un área a su alrededor.
    """
    latitud, longitud, direccion = buscar_coordenadas(
        ubicacion,
        idioma=idioma,
    )

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


def crear_area_desde_coordenadas(
    latitud: float,
    longitud: float,
    radio_km: float,
    archivo_salida: str | None = None,
    numero_vertices: int = 180,
) -> tuple[Path, float, float, str]:
    """
    Crea un KMZ directamente desde un par de coordenadas.
    """
    referencia = f"Coordenadas {latitud:g}, {longitud:g}"

    if archivo_salida is None:
        archivo_salida = crear_nombre_coordenadas_kmz(
            latitud,
            longitud,
            radio_km,
        )

    ruta_kmz = crear_area_kmz(
        latitud=latitud,
        longitud=longitud,
        radio_km=radio_km,
        archivo_salida=archivo_salida,
        numero_vertices=numero_vertices,
    )

    return ruta_kmz, latitud, longitud, referencia


def crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Genera un área KMZ desde una ubicación o unas coordenadas."
        )
    )
    parser.add_argument(
        "ubicacion",
        nargs="?",
        help='Dirección o lugar que se quiere buscar, entre comillas.',
    )
    parser.add_argument(
        "--coordenadas",
        nargs=2,
        type=float,
        metavar=("LATITUD", "LONGITUD"),
        help="Usa directamente una latitud y una longitud.",
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
    parser.add_argument(
        "--idioma",
        default="es",
        help=(
            "Idioma de la dirección devuelta por el buscador "
            "(por defecto: es)."
        ),
    )
    return parser


def main() -> None:
    parser = crear_parser()
    argumentos = parser.parse_args()

    if argumentos.ubicacion is None and argumentos.coordenadas is None:
        parser.error("indica una ubicación o utiliza --coordenadas.")

    if argumentos.ubicacion is not None and argumentos.coordenadas is not None:
        parser.error(
            "no puedes indicar una ubicación y --coordenadas a la vez."
        )

    try:
        if argumentos.coordenadas is not None:
            latitud, longitud = argumentos.coordenadas
            ruta, latitud, longitud, referencia = (
                crear_area_desde_coordenadas(
                    latitud=latitud,
                    longitud=longitud,
                    radio_km=argumentos.radio,
                    archivo_salida=argumentos.salida,
                    numero_vertices=argumentos.vertices,
                )
            )
        else:
            ruta, latitud, longitud, referencia = crear_area_desde_ubicacion(
                ubicacion=argumentos.ubicacion,
                radio_km=argumentos.radio,
                archivo_salida=argumentos.salida,
                numero_vertices=argumentos.vertices,
                idioma=argumentos.idioma,
            )
    except (ValueError, GeocoderServiceError) as error:
        raise SystemExit(f"Error: {error}") from error

    print(f"Referencia: {referencia}")
    print(f"Latitud: {latitud}")
    print(f"Longitud: {longitud}")
    print(f"Archivo creado: {ruta}")


if __name__ == "__main__":
    main()
