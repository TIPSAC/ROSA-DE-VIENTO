# -*- coding: utf-8 -*-
"""
Created on Fri Jul 18 15:49:30 2025

@author: TIPSAC
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from windrose import WindroseAxes
import numpy as np
from datetime import datetime
import unicodedata
import requests
from io import BytesIO
from PIL import Image
import matplotlib

matplotlib.use('Agg')  # Necesario para que funcione en Streamlit Cloud

def normalizar(texto):
    texto = unicodedata.normalize('NFKD', texto)
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    return texto.lower().strip()

st.set_page_config(layout="centered")
st.title("🌬️ Generador de Rosa de Viento")

archivo = st.file_uploader("📁 Sube tu archivo Excel", type=["xlsx", "xls"])

if archivo:
    df = pd.read_excel(archivo)

    # Buscar columna de fecha
    palabras_fecha = ['fecha', 'date', 'tiempo', 'time']
    col_fecha = next((col for col in df.columns if any(p in col.lower() for p in palabras_fecha)), None)

    if not col_fecha:
        st.error("❌ No se encontró una columna de fecha.")
        st.stop()

    df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce')
    df[col_fecha] = df[col_fecha].dt.tz_localize(None)  # Quitar zona horaria
    if df[col_fecha].dropna().empty:
        st.error("❌ Ninguna fecha se pudo convertir correctamente.")
        st.stop()

    # Buscar columnas de velocidad y dirección
    col_speed = next((col for col in df.columns if "speed" in col.lower()), None)
    col_direction = next((col for col in df.columns if "direction" in col.lower()), None)

    if not col_speed or not col_direction:
        st.error("❌ No se encontraron columnas con 'Speed' y/o 'Direction'.")
        st.stop()

    usar_rango = st.radio("¿Deseas ingresar un rango de fechas?", ["No", "Sí"])

    if usar_rango == "Sí":
        fechas_disponibles = df[col_fecha].dropna().sort_values()
        fecha_min = fechas_disponibles.min()
        fecha_max = fechas_disponibles.max()

        rango_fechas = st.slider(
            "Selecciona el rango de fechas:",
            min_value=fecha_min,
            max_value=fecha_max,
            value=(fecha_min, fecha_max),
            format="DD/MM/YYYY HH:mm"
        )

        fecha_inicio, fecha_fin = rango_fechas
        df_filtrado = df[(df[col_fecha] >= fecha_inicio) & (df[col_fecha] <= fecha_fin)]
        mostrar_rango = True
    else:
        df_filtrado = df
        mostrar_rango = False

    velocidad = df_filtrado[col_speed]
    direccion = df_filtrado[col_direction]

    etiquetas = ['0° N', 'NE', '90°E', 'SE', '180°S', 'SW', '270°W', 'NW']
    grados = np.arange(0, 360, 45)
    bins = pd.cut(direccion, bins=np.append(grados, 360), labels=etiquetas, right=False, include_lowest=True)
    conteo = bins.value_counts().reindex(etiquetas).fillna(0)
    porcentaje = (conteo / conteo.sum()) * 100
    porcentaje = porcentaje.round(1).astype(str) + '%'

    fig = plt.figure(figsize=(10, 8))
    ax = WindroseAxes.from_ax(fig=fig)
    ax.bar(direccion, velocidad, normed=True, opening=0.8, edgecolor='white')
    ax.set_title("ROSA DE VIENTO", pad=25, fontsize=16, ha="left")

    if mostrar_rango:
        rango_texto = f"{fecha_inicio.strftime('%d/%m/%Y %H:%M')} \n al  {fecha_fin.strftime('%d/%m/%Y %H:%M')}"
        fig.text(0.95, 0.08, f"Del: {rango_texto}", ha='center', fontsize=11)

    # Logo desde URL
    url_logo = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTMzPSKQza2TtRd6xqzQAhY2PMQ0il5P7u7Tg&s"
    response = requests.get(url_logo)
    logo_img = Image.open(BytesIO(response.content)).convert("RGBA")
    logo_img_resized = logo_img.resize((170, 80))
    logo_array = np.asarray(logo_img_resized)
    fig.figimage(logo_array, xo=10, yo=10, alpha=0.6, zorder=15)

    ax.set_yticklabels(['', '', '', '', ''])
    ax.set_legend(loc='upper right', bbox_to_anchor=(1.3, 1), title="Velocidad (m/s)")

    tabla = pd.DataFrame({'% Dirección': porcentaje})
    tabla_plot = plt.table(cellText=tabla.values,
                           rowLabels=tabla.index,
                           colLabels=tabla.columns,
                           cellLoc='center',
                           loc='lower right',
                           bbox=[1.1, 0.05, 0.25, 0.45])
    tabla_plot.auto_set_font_size(False)
    tabla_plot.set_fontsize(8)

    st.pyplot(fig)

