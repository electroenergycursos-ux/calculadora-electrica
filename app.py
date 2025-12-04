import streamlit as st
import numpy as np
from fpdf import FPDF
import base64
import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS ---
st.set_page_config(page_title="CEN-2004: Protocolo de Dimensionamiento Electrico", layout="wide", page_icon="⚡")

st.markdown("""
<style>
    /* Estilos del Dashboard */
    .header-style { font-size:18px; font-weight:bold; color: #1e40af; border-bottom: 2px solid #1e40af; padding-bottom: 5px; margin-bottom: 15px;}
    .module-box { border: 1px solid #e0e0e0; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 2px 2px 8px rgba(0,0,0,0.05);}
    
    /* Estilos de Resultados */
    .success-box-final { padding: 15px; border-radius: 8px; background-color: #d1e7dd; color: #0f5132; border: 1px solid #badbcc; font-weight: bold; text-align: center; margin-top: 15px; }
    .fail-box-final { padding: 15px; border-radius: 8px; background-color: #f8d7da; color: #842029; border: 1px solid #f5c6cb; font-weight: bold; text-align: center; margin-top: 15px; }
    .warning-box-final { padding: 15px; border-radius: 8px; background-color: #fff3cd; color: #664d03; border: 1px solid #ffecb5; font-weight: bold; text-align: center; margin-top: 15px; }
    .recommendation-box { padding: 15px; border-radius: 8px; background-color: #f0f8ff; color: #004E8C; border: 1px solid #b3d9ff; font-weight: bold; }
    h1 { color: #1e40af; } 
    [data-testid="stMetricValue"] { font-size: 20px; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ CEN-2004: Protocolo de Dimensionamiento Electrico")
st.caption("Herramienta de Dimensionamiento conforme al Codigo Electrico Nacional (CEN-2004)")

# --- 2. BASES DE DATOS DE INGENIERÍA ---
# Se usan ampacidades de 75°C (Limite Terminal) y 90°C (Base para Correcion)
db_cables = {
    "14 AWG":      {"area": 2.08,  "diam": 2.80, "R": 10.17, "X": 0.190, "amp_75": 25, "amp_90": 30, "kcmil": 4.107},
    "12 AWG":      {"area": 3.31,  "diam": 3.86, "R": 6.56,  "X": 0.177, "amp_75": 30, "amp_90": 35, "kcmil": 6.530},
    "10 AWG":      {"area": 5.26,  "diam": 4.10, "R": 3.94,  "X": 0.164, "amp_75": 40, "amp_90": 50, "kcmil": 10.380},
    "8 AWG":       {"area": 8.37,  "diam": 5.50, "R": 2.56,  "X": 0.171, "amp_75": 55, "amp_90": 70, "kcmil": 16.510},
    "6 AWG":       {"area": 13.3,  "diam": 6.80, "R": 1.61,  "X": 0.167, "amp_75": 75, "amp_90": 95, "kcmil": 26.240},
    "4 AWG":       {"area": 21.2,  "diam": 8.40, "R": 1.02,  "X": 0.157, "amp_75": 95, "amp_90": 120, "kcmil": 41.740},
    "2 AWG":       {"area": 33.6,  "diam": 10.5, "R": 0.62,  "X": 0.148, "amp_75": 130, "amp_90": 170, "kcmil": 66.360},
    "1/0 AWG":     {"area": 53.5,  "diam": 13.0, "R": 0.39,  "X": 0.144, "amp_75": 150, "amp_90": 210, "kcmil": 105.5},
    "2/0 AWG":     {"area": 67.4,  "diam": 14.4, "R": 0.31,  "X": 0.141, "amp_75": 175, "amp_90": 240, "kcmil": 133.1},
    "4/0 AWG":     {"area": 107.2, "diam": 17.8, "R": 0.219, "X": 0.135, "amp_75": 230, "amp_90": 320, "kcmil": 211.6},
}

db_breakers = [15, 20, 25, 30, 40, 50, 60, 70, 100, 125, 150, 175, 200, 225, 250]

db_temp_factors = {
    "21-25 C (1.04)": 1.04, "26-30 C (Base 1.00)": 1.00, "31-35 C (0.96)": 0.96,
    "36-40 C (0.91)": 0.91, "41-45 C (0.87)": 0.87, "46-50 C (0.82)": 0.82,
}

# Base de
