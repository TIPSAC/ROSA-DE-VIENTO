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

st.set_page_config(page_title="Rosa de Viento", layout="centered")
st.title("🌬️ Visualizador de Rosa de Viento")

uploaded_file = st.file_uploader("📤 Sube tu archivo Excel", type=["xlsx"])

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

    fig = plt.figure(figsize=(8, 6))
    ax = WindroseAxes.from_ax(fig=fig)
    ax.bar(df['direccion'], df['velocidad'], normed=True, opening=0.8, edgecolor='white')
    ax.set_legend()
    st.pyplot(fig)

    # Mostrar resumen del rango
    if usar_rango == "Sí":
        st.info(f"Mostrando datos desde **{fecha_inicio.strftime('%d/%m/%Y %H:%M')}** hasta **{fecha_fin.strftime('%d/%m/%Y %H:%M')}**")
    else:
        st.info(f"Mostrando **todos los datos** del archivo.")

