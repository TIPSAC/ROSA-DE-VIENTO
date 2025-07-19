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
from datetime import datetime, time
import requests
from io import BytesIO
from PIL import Image

st.set_page_config(page_title="Rosa de Viento", layout="centered")
st.title("🌬️ GENERADOR DE  \n ROSA DE VIENTO")

uploaded_file = st.file_uploader("📤 Suba su archivo Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Detectar columnas de velocidad y dirección
    col_velocidad = next((col for col in df.columns if 'vel' in col.lower() or 'speed' in col.lower()), None)
    col_direccion = next((col for col in df.columns if 'dir' in col.lower() or 'direction' in col.lower()), None)

    if col_velocidad is None or col_direccion is None:
        st.error("❌ No se encontraron columnas de velocidad o dirección.")
        st.stop()

    # Detectar columna de fecha
    palabras_fecha = ['fecha', 'date', 'tiempo', 'time']
    col_fecha = next((col for col in df.columns if any(p in col.lower() for p in palabras_fecha)), None)
    if col_fecha is None:
        st.error("❌ No se encontró una columna de fecha.")
        st.stop()

    # Convertir fechas robustamente y quitar zona horaria
    df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce', dayfirst=True)
    df = df.dropna(subset=[col_fecha])
    df[col_fecha] = df[col_fecha].dt.tz_localize(None)

    df = df.dropna(subset=[col_velocidad, col_direccion])
    df = df.rename(columns={col_velocidad: 'velocidad', col_direccion: 'direccion', col_fecha: 'fecha'})

    # Preguntar si se desea seleccionar rango
    usar_rango = st.radio("¿Deseas ingresar un rango de fechas?", ("No", "Sí"))

    if usar_rango == "Sí":
        fecha_min = df['fecha'].min()
        fecha_max = df['fecha'].max()

        st.markdown("### Selecciona el rango de fechas")
        fecha_inicio_fecha = st.date_input("📅 Fecha de inicio", value=fecha_min.date(), min_value=fecha_min.date(), max_value=fecha_max.date())
        fecha_inicio_hora = st.time_input("⏰ Hora de inicio", value=fecha_min.time())

        fecha_fin_fecha = st.date_input("📅 Fecha de fin", value=fecha_max.date(), min_value=fecha_min.date(), max_value=fecha_max.date())
        fecha_fin_hora = st.time_input("⏰ Hora de fin", value=fecha_max.time())

        fecha_inicio = datetime.combine(fecha_inicio_fecha, fecha_inicio_hora)
        fecha_fin = datetime.combine(fecha_fin_fecha, fecha_fin_hora)

        df = df[(df['fecha'] >= fecha_inicio) & (df['fecha'] <= fecha_fin)]

    st.subheader("📊 Rosa de Viento")

    # Cargar logo desde URL y procesar
    url_logo = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTMzPSKQza2TtRd6xqzQAhY2PMQ0il5P7u7Tg&s"
    response = requests.get(url_logo)
    logo_img = Image.open(BytesIO(response.content)).convert("RGBA")
    logo_img_resized = logo_img.resize((380, 150))  # <-- LOGO MÁS GRANDE
    logo_array = np.asarray(logo_img_resized)

    # Crear figura
    fig = plt.figure(figsize=(10, 8))
    ax = WindroseAxes.from_ax(fig=fig)
    ax.bar(df['direccion'], df['velocidad'], normed=True, opening=0.8, edgecolor='white')

    # Personalización
    ax.set_yticklabels(['', '', '', '', ''])  # Ocultar etiquetas de radio
    ax.set_legend(loc='upper right', bbox_to_anchor=(1.3, 1), title="Velocidad (m/s)", prop={'size': 20}, title_fontsize='large')  # <-- LEYENDA MÁS GRANDE
    fig.figimage(logo_array, xo=10, yo=10, alpha=0.8, zorder=15)

    # Título de la rosa
    plt.title("ROSA DE VIENTO", pad=25, fontsize=16, ha="left")

    # Calcular % por dirección con etiquetas cardinales
    etiquetas = ['0° N', 'NE', '90°E', 'SE', '180°S', 'SW', '270°W', 'NW']
    grados = np.arange(0, 360, 45)
    bins = pd.cut(df['direccion'], bins=np.append(grados, 360), labels=etiquetas, right=False, include_lowest=True)
    conteo = bins.value_counts().reindex(etiquetas).fillna(0)
    porcentaje = (conteo / conteo.sum()) * 100
    porcentaje_formateado = porcentaje.round(1).astype(str) + '%'

    # Crear tabla a la derecha
    tabla = pd.DataFrame({'% Dirección': porcentaje_formateado})
    tabla_plot = plt.table(cellText=tabla.values,
                           rowLabels=tabla.index,
                           colLabels=tabla.columns,
                           cellLoc='center',
                           loc='lower right',
                           bbox=[1.1, 0.05, 0.25, 0.45])
    tabla_plot.auto_set_font_size(False)
    tabla_plot.set_fontsize(10)  # <-- TAMAÑO DE LETRA MAYOR

    plt.tight_layout()
    st.pyplot(fig)

    # Mostrar resumen del rango
    if usar_rango == "Sí":
        st.info(f"Mostrando datos desde **{fecha_inicio.strftime('%d/%m/%Y %H:%M')}** hasta **{fecha_fin.strftime('%d/%m/%Y %H:%M')}**")
    else:
        st.info(f"Mostrando **todos los datos** del archivo.")


