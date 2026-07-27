from pathlib import Path

import simplekml
from geopy.distance import geodesic


def crear_area_kmz(
    latitud: float,
    longitud: float,
    radio_km: float,
    archivo_salida: str = "area_influencia.kmz",
    numero_vertices: int = 180,
) -> Path:
    """
    Crea un área circular geodésica alrededor de un punto
    y la exporta como KMZ.

    Parámetros
    ----------
    latitud:
        Latitud del punto central.
    longitud:
        Longitud del punto central.
    radio_km:
        Radio del área en kilómetros.
    archivo_salida:
        Nombre o ruta del archivo KMZ.
    numero_vertices:
        Número de puntos utilizados para aproximar el círculo.
    """

    if not -90 <= latitud <= 90:
        raise ValueError("La latitud debe estar entre -90 y 90.")

    if not -180 <= longitud <= 180:
        raise ValueError("La longitud debe estar entre -180 y 180.")

    if radio_km <= 0:
        raise ValueError("El radio debe ser mayor que cero.")

    if numero_vertices < 36:
        raise ValueError(
            "Se recomienda utilizar al menos 36 vértices."
        )

    centro = (latitud, longitud)
    coordenadas_perimetro = []

    # Generamos puntos alrededor del centro.
    for indice in range(numero_vertices):
        rumbo = indice * 360 / numero_vertices

        destino = geodesic(
            kilometers=radio_km
        ).destination(
            centro,
            bearing=rumbo
        )

        # GeoPy utiliza: latitud, longitud.
        # KML utiliza: longitud, latitud.
        coordenadas_perimetro.append(
            (destino.longitude, destino.latitude)
        )

    # Cerramos explícitamente el polígono.
    coordenadas_perimetro.append(
        coordenadas_perimetro[0]
    )

    # Creamos el documento KML.
    kml = simplekml.Kml()
    kml.document.name = (
        f"Área de influencia de {radio_km} km"
    )

    # Añadimos el punto central.
    punto = kml.newpoint(
        name="Punto central",
        description=(
            f"Latitud: {latitud}<br>"
            f"Longitud: {longitud}<br>"
            f"Radio: {radio_km} km"
        ),
        coords=[(longitud, latitud)]
    )

    punto.style.iconstyle.color = simplekml.Color.red
    punto.style.iconstyle.scale = 1.2

    # Añadimos el área circular.
    poligono = kml.newpolygon(
        name=f"Área de {radio_km} km",
        description=(
            f"Área situada a un máximo aproximado de "
            f"{radio_km} km geodésicos del centro."
        ),
        outerboundaryis=coordenadas_perimetro
    )

    # Pegamos el polígono al terreno.
    poligono.altitudemode = (
        simplekml.AltitudeMode.clamptoground
    )

    # Contorno.
    poligono.style.linestyle.color = simplekml.Color.red
    poligono.style.linestyle.width = 3

    # Relleno rojo transparente.
    poligono.style.polystyle.color = (
        simplekml.Color.changealphaint(
            80,
            simplekml.Color.red
        )
    )

    poligono.style.polystyle.fill = 1
    poligono.style.polystyle.outline = 1

    # Guardamos como KMZ.
    ruta_salida = Path(archivo_salida).resolve()
    kml.savekmz(str(ruta_salida))

    return ruta_salida


if __name__ == "__main__":
    archivo = crear_area_kmz(
        latitud=41.5632,
        longitud=2.0089,
        radio_km=10,
        archivo_salida="area_terrassa_10km.kmz",
        numero_vertices=180
    )

    print(f"Archivo creado correctamente:")
    print(archivo)
