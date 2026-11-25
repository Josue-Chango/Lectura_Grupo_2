"""Dashboard de seguridad en Pichincha.

API + servidor Flask en el puerto 5000. Los datos se procesan con pandas
dentro del entorno virtual `.env`.

Uso:
    .\\.env\\Scripts\\python.exe app.py
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from flask import Flask, Response, jsonify, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / os.getenv("CSV_NOMBRE", "dataset_seguridad_pichincha_2020_2026_hasta_febrero.csv")
PUERTO = int(os.getenv("PUERTO", "5000"))

MESES_ES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def cargar_datos() -> pd.DataFrame:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"No se encontró el dataset: {CSV_PATH}")

    datos = pd.read_csv(CSV_PATH, encoding="utf-8")
    datos["fecha"] = pd.to_datetime(datos["fecha"])
    datos["anio"] = datos["fecha"].dt.year
    return datos


df = cargar_datos()

ANIOS = sorted(df["anio"].unique().tolist())
CANTONES = sorted(df["canton"].unique().tolist())
CATEGORIAS = sorted(df["categoria"].unique().tolist())

app = Flask(__name__)


@app.after_request
def permitir_live_server(respuesta: Response) -> Response:
    """El HTML se puede abrir desde Live Server (p. ej. :5500) y consumir esta API."""
    respuesta.headers["Access-Control-Allow-Origin"] = "*"
    respuesta.headers["Access-Control-Allow-Headers"] = "Content-Type"
    respuesta.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    return respuesta


def param(nombre: str, opciones: list) -> object | None:
    valor = (request.args.get(nombre) or "").strip()
    if not valor or valor.lower() == "todos":
        return None
    return valor if valor in [str(op) for op in opciones] else None


def filtrar() -> pd.DataFrame:
    anio = param("anio", ANIOS)
    canton = param("canton", CANTONES)
    categoria = param("categoria", CATEGORIAS)

    filtro = df
    if anio is not None:
        filtro = filtro[filtro["anio"] == int(anio)]
    if canton is not None:
        filtro = filtro[filtro["canton"] == canton]
    if categoria is not None:
        filtro = filtro[filtro["categoria"] == categoria]
    return filtro


def etiqueta_mes(periodo: pd.Period) -> str:
    return f"{MESES_ES[periodo.month - 1]} {periodo.year}"


def serie_mensual(filtro: pd.DataFrame) -> list[dict]:
    if filtro.empty:
        return []

    agrupado = filtro.groupby(filtro["fecha"].dt.to_period("M"))["casos"].sum().sort_index()
    rango = pd.period_range(agrupado.index.min(), agrupado.index.max(), freq="M")
    agrupado = agrupado.reindex(rango, fill_value=0)

    return [
        {"periodo": str(periodo), "etiqueta": etiqueta_mes(periodo), "casos": int(valor)}
        for periodo, valor in agrupado.items()
    ]


def variacion(filtro: pd.DataFrame, serie: list[dict]) -> dict:
    anio = param("anio", ANIOS)
    actual = int(filtro["casos"].sum())

    if anio is not None:
        anio_actual = int(anio)
        anterior = df[df["anio"] == anio_actual - 1]
        canton = param("canton", CANTONES)
        categoria = param("categoria", CATEGORIAS)
        if canton is not None:
            anterior = anterior[anterior["canton"] == canton]
        if categoria is not None:
            anterior = anterior[anterior["categoria"] == categoria]
        previo = int(anterior["casos"].sum())
        referencia = str(anio_actual - 1)
    else:
        valores = [punto["casos"] for punto in serie]
        actual = sum(valores[-12:])
        previo = sum(valores[-24:-12])
        referencia = "últimos 12 meses"

    if previo <= 0:
        return {"porcentaje": None, "referencia": referencia}

    return {"porcentaje": round((actual - previo) / previo * 100, 1), "referencia": referencia}


@app.get("/")
def index() -> Response:
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/api/filtros")
def api_filtros() -> Response:
    return jsonify(
        {
            "anios": ANIOS,
            "cantones": CANTONES,
            "categorias": CATEGORIAS,
            "desde": df["fecha"].min().strftime("%Y-%m"),
            "hasta": df["fecha"].max().strftime("%Y-%m"),
            "total_registros": int(len(df)),
        }
    )


@app.get("/api/datos")
def api_datos() -> Response:
    filtro = filtrar()
    serie = serie_mensual(filtro)

    por_canton = (
        filtro.groupby("canton")["casos"].sum().sort_values(ascending=False)
        if not filtro.empty
        else pd.Series(dtype="int64")
    )
    por_categoria = (
        filtro.groupby("categoria")["casos"].sum().sort_values(ascending=False)
        if not filtro.empty
        else pd.Series(dtype="int64")
    )
    top_combos = (
        filtro.groupby(["canton", "categoria"])["casos"].sum().nlargest(6)
        if not filtro.empty
        else pd.Series(dtype="int64")
    )

    mapa = (
        filtro.pivot_table(index="canton", columns="categoria", values="casos", aggfunc="sum", fill_value=0)
        if not filtro.empty
        else pd.DataFrame()
    )
    if not mapa.empty:
        mapa = mapa.reindex(index=CANTONES, columns=CATEGORIAS, fill_value=0)

    mes_pico = max(serie, key=lambda punto: punto["casos"]) if serie else None

    return jsonify(
        {
            "resumen": {
                "total_casos": int(filtro["casos"].sum()),
                "registros": int(len(filtro)),
                "meses": len(serie),
                "promedio_mensual": round(int(filtro["casos"].sum()) / len(serie)) if serie else 0,
                "canton_lider": por_canton.index[0] if not por_canton.empty else "—",
                "categoria_lider": por_categoria.index[0] if not por_categoria.empty else "—",
                "mes_pico": mes_pico,
                "variacion": variacion(filtro, serie),
            },
            "serie_mensual": serie,
            "por_canton": [
                {"nombre": nombre, "casos": int(casos)} for nombre, casos in por_canton.items()
            ],
            "por_categoria": [
                {"nombre": nombre, "casos": int(casos)} for nombre, casos in por_categoria.items()
            ],
            "top_combos": [
                {"canton": canton, "categoria": categoria, "casos": int(casos)}
                for (canton, categoria), casos in top_combos.items()
            ],
            "mapa": {
                "cantones": CANTONES,
                "categorias": CATEGORIAS,
                "valores": [
                    {"canton": canton, "categoria": categoria, "casos": int(mapa.loc[canton, categoria])}
                    for canton in (mapa.index if not mapa.empty else [])
                    for categoria in (mapa.columns if not mapa.empty else [])
                ],
            },
        }
    )


@app.get("/api/exportar.csv")
def api_exportar() -> Response:
    filtro = filtrar()
    columnas = ["fecha", "canton", "categoria", "casos"]
    contenido = filtro[columnas].to_csv(index=False, date_format="%Y-%m") if not filtro.empty else ""
    return Response(
        contenido,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=seguridad_pichincha_filtrado.csv"},
    )


@app.get("/api/health")
def api_health() -> Response:
    return jsonify({"estado": "ok", "filas": int(len(df))})


if __name__ == "__main__":
    print(f"Dashboard en http://localhost:{PUERTO}  (CSV: {CSV_PATH.name})")
    app.run(host="0.0.0.0", port=PUERTO, debug=True)
