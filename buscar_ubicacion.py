import argparse
import re
import unicodedata
from math import pi, sqrt
from pathlib import Path

from geopy.exc import GeocoderServiceError
from geopy.geocoders import Nominatim

from crear_area_kmz import crear_area_kmz


def normalizar_unidad(unidad: str) -> str:
    texto = unicodedata.normalize("NFKD", unidad)
    texto = texto.encode("ascii", "ignore").decode("ascii").lower()
    unidades = {
        "km": "km",
        "kilometro": "km",
        "kilometros": "km",
        "m": "m",
        "metro": "m",
        "metros": "m",
        "ha": "ha",
        "hectarea": "ha",
        "hectareas": "ha",
        "mi": "mi",
        "milla": "mi",
        "millas": "mi",
    }

    try:
        return unidades[texto]
    except KeyError as error:
        raise argparse.ArgumentTypeError(
            "la unidad debe ser km, m, ha o mi."
        ) from error


def convertir_a_kilometros(valor: float, unidad: str) -> float:
    if valor <= 0:
        raise ValueError("El radio o área debe ser mayor que cero.")

    if unidad == "km":
        return valor
    if unidad == "m":
        return valor / 1000
    if unidad == "mi":
        return valor * 1.609344
    if unidad == "ha":
        return sqrt(valor * 10_000 / pi) / 1000

    raise ValueError(f"Unidad no reconocida: {unidad}")


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


def crear_nombre_kmz(
    ubicacion: str,
    radio: float,
    unidad: str = "km",
) -> str:
    """
    Crea un nombre de archivo válido a partir de la ubicación buscada.
    """
    texto_sin_acentos = unicodedata.normalize("NFKD", ubicacion)
    texto_ascii = texto_sin_acentos.encode("ascii", "ignore").decode("ascii")
    nombre = re.sub(r"[^a-zA-Z0-9]+", "_", texto_ascii)
    nombre = nombre.strip("_").lower()[:80]

    if not nombre:
        nombre = "ubicacion"

    radio_texto = f"{radio:g}".replace(".", "_")
    return f"{nombre}_{radio_texto}{unidad}.kmz"


def crear_nombre_coordenadas_kmz(
    latitud: float,
    longitud: float,
    radio: float,
    unidad: str = "km",
) -> str:
    latitud_texto = f"{abs(latitud):g}".replace(".", "_")
    longitud_texto = f"{abs(longitud):g}".replace(".", "_")
    hemisferio_latitud = "n" if latitud >= 0 else "s"
    hemisferio_longitud = "e" if longitud >= 0 else "o"
    radio_texto = f"{radio:g}".replace(".", "_")

    return (
        f"coordenadas_{latitud_texto}{hemisferio_latitud}_"
        f"{longitud_texto}{hemisferio_longitud}_"
        f"{radio_texto}{unidad}.kmz"
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
        help=(
            "Radio del área; con hectáreas representa la superficie "
            "(por defecto: 10)."
        ),
    )
    parser.add_argument(
        "--unidad",
        type=normalizar_unidad,
        default="km",
        help="Unidad del radio: km, m, mi o ha (por defecto: km).",
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
        radio_km = convertir_a_kilometros(
            argumentos.radio,
            argumentos.unidad,
        )

        if argumentos.coordenadas is not None:
            latitud, longitud = argumentos.coordenadas
            archivo_salida = argumentos.salida
            if archivo_salida is None:
                archivo_salida = crear_nombre_coordenadas_kmz(
                    latitud,
                    longitud,
                    argumentos.radio,
                    argumentos.unidad,
                )

            ruta, latitud, longitud, referencia = (
                crear_area_desde_coordenadas(
                    latitud=latitud,
                    longitud=longitud,
                    radio_km=radio_km,
                    archivo_salida=archivo_salida,
                    numero_vertices=argumentos.vertices,
                )
            )
        else:
            archivo_salida = argumentos.salida
            if archivo_salida is None:
                archivo_salida = crear_nombre_kmz(
                    argumentos.ubicacion,
                    argumentos.radio,
                    argumentos.unidad,
                )

            ruta, latitud, longitud, referencia = crear_area_desde_ubicacion(
                ubicacion=argumentos.ubicacion,
                radio_km=radio_km,
                archivo_salida=archivo_salida,
                numero_vertices=argumentos.vertices,
                idioma=argumentos.idioma,
            )
    except (ValueError, GeocoderServiceError) as error:
        raise SystemExit(f"Error: {error}") from error

    print(f"Referencia: {referencia}")
    print(f"Latitud: {latitud}")
    print(f"Longitud: {longitud}")
    print(f"Radio geodésico utilizado: {radio_km:g} km")
    print(f"Archivo creado: {ruta}")


if __name__ == "__main__":
    main()
