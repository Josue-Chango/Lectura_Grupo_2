# Dashboard de seguridad en Pichincha

Dashboard interactivo construido con **Python + pandas + Flask**, con el entorno virtual en la carpeta `.env`. El servidor corre en el **puerto 5000** y el front-end (`index.html`) también se puede abrir con **Live Server** en VS Code.

## Estructura

| Archivo | Descripción |
| --- | --- |
| `dataset_seguridad_pichincha_2020_2026_hasta_febrero.csv` | Datos mensuales por cantón y categoría (ene 2020 – feb 2026). |
| `app.py` | API Flask + procesamiento con pandas. Escucha en `:5000`. |
| `index.html` | Dashboard (filtros, KPIs, gráficos, mapa de calor y exportación CSV). |
| `.env/` | Entorno virtual con pandas y Flask instalados. |
| `.vscode/settings.json` | Live Server configurado en `:5500` para no chocar con Flask. |

## Puesta en marcha

Desde PowerShell, en esta carpeta:

```powershell
.\.env\Scripts\Activate.ps1
pip install -r requirements.txt   # solo si el entorno aún no tiene las librerías
python app.py
```

Si PowerShell bloquea la activación del entorno:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.env\Scripts\Activate.ps1
```

También se puede ejecutar sin activar el entorno:

```powershell
.\.env\Scripts\python.exe app.py
```

## Cómo verlo

- **Directo:** abre <http://localhost:5000> (Flask sirve el mismo `index.html`).
- **Con Live Server:** en VS Code, clic derecho sobre `index.html` → *Open with Live Server*. Se abrirá en `http://localhost:5500` y consumirá la API de `:5000` (CORS habilitado).

> El servidor de Flask debe seguir corriendo para que el dashboard cargue los datos. Si se abre con Live Server y Flask está apagado, aparecerá un aviso en la página.

## Endpoints

| Ruta | Descripción |
| --- | --- |
| `GET /` | Dashboard HTML. |
| `GET /api/filtros` | Años, cantones, categorías y rango de fechas disponibles. |
| `GET /api/datos?anio=2024&canton=Quito&categoria=Robo%20a%20personas` | KPIs, serie mensual, ranking por cantón/categoría, mapa de calor y top de combinaciones. Todos los parámetros son opcionales. |
| `GET /api/exportar.csv?anio=2024` | Descarga el dataset filtrado en CSV. |
| `GET /api/health` | Comprobación rápida del servicio. |

## Notas

- El dataset tiene 4.736 registros, 8 cantones y 8 categorías; los meses de 2026 son solo enero y febrero, por lo que las comparaciones de ese año son parciales.
- Para cambiar el puerto: `$env:PUERTO=5001; .\.env\Scripts\python.exe app.py` (y ajustar `API` en `index.html` si se usa Live Server).
- Para usar otro CSV: `$env:CSV_NOMBRE="otro_archivo.csv"`.
