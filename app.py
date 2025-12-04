import streamlit as st
import numpy as np
from fpdf import FPDF
import base64
import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS ---
st.set_page_config(page_title="CEN-2004: Protocolo de Dimensionamiento Eléctrico", layout="wide", page_icon="⚡")

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

st.title("⚡ CEN-2004: Protocolo de Dimensionamiento Eléctrico")
st.caption("Herramienta de Dimensionamiento conforme al Código Eléctrico Nacional (CEN-2004)")

# --- 2. BASES DE DATOS DE INGENIERÍA ---
db_cables = {
    "14 AWG":      {"area": 2.08,  "diam": 2.80, "R": 10.17, "X": 0.190, "amp": 20, "kcmil": 4.107},
    "12 AWG":      {"area": 3.31,  "diam": 3.86, "R": 6.56,  "X": 0.177, "amp": 25, "kcmil": 6.530},
    "10 AWG":      {"area": 5.26,  "diam": 4.10, "R": 3.94,  "X": 0.164, "amp": 35, "kcmil": 10.380},
    "8 AWG":       {"area": 8.37,  "diam": 5.50, "R": 2.56,  "X": 0.171, "amp": 50, "kcmil": 16.510},
    "6 AWG":       {"area": 13.3,  "diam": 6.80, "R": 1.61,  "X": 0.167, "amp": 65, "kcmil": 26.240},
    "4 AWG":       {"area": 21.2,  "diam": 8.40, "R": 1.02,  "X": 0.157, "amp": 85, "kcmil": 41.740},
    "2 AWG":       {"area": 33.6,  "diam": 10.5, "R": 0.62,  "X": 0.148, "amp": 115, "kcmil": 66.360},
    "1/0 AWG":     {"area": 53.5,  "diam": 13.0, "R": 0.39,  "X": 0.144, "amp": 150, "kcmil": 105.5},
    "2/0 AWG":     {"area": 67.4,  "diam": 14.4, "R": 0.31,  "X": 0.141, "amp": 175, "kcmil": 133.1},
    "4/0 AWG":     {"area": 107.2, "diam": 17.8, "R": 0.219, "X": 0.135, "amp": 230, "kcmil": 211.6},
}

db_breakers = [15, 20, 25, 30, 40, 50, 60, 70, 100, 125, 150, 175, 200, 225, 250]

db_temp_factors = {
    "21-25 °C (1.04)": 1.04, "26-30 °C (Base 1.00)": 1.00, "31-35 °C (0.96)": 0.96,
    "36-40 °C (0.91)": 0.91, "41-45 °C (0.87)": 0.87, "46-50 °C (0.82)": 0.82,
}

db_tuberias = {
    "1/2\"": {"PVC40": 184, "EMT": 196, "ARG": 192}, "3/4\"": {"PVC40": 327, "EMT": 353, "ARG": 346},
    "1\"":   {"PVC40": 568, "EMT": 595, "ARG": 583}, "1 1/4\"": {"PVC40": 986, "EMT": 1026, "ARG": 1005},
    "1 1/2\"": {"PVC40": 1338, "EMT": 1391, "ARG": 1362}, "2\"":   {"PVC40": 2186, "EMT": 2275, "ARG": 2228},
}

# Inicialización de variables
carga_va, voltaje, sistema, calibre_sel, num_conductores, amp_real, i_diseno = 1260.0, 120, "Monofásico (1F)", "12 AWG", 3, 22.0, 13.12
percent_drop = 1.83
v_drop = 2.2
tubo_sel, porcentaje, limite = "3/4\"", 40.0, 40
tubo_recomendado = "1\""
area_kcmil_min = 6.53 
calibre_min_cc = "12 AWG"
K_FINAL = 5.0 
i_cc_max_permitida = 0.0

# --- INTERFAZ DE ENTRADA (Módulo de Configuración Común) ---
st.header("1. Configuración del Sistema")
col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
with col_cfg1:
    carga_va = st.number_input("Carga Total (VA)", value=1260.0, step=100.0, key="c_va")
with col_cfg2:
    voltaje = st.selectbox("Tensión de Servicio (V)", [120, 208, 480], index=0, key="v_ser")
with col_cfg3:
    sistema = st.selectbox("Sistema", ["Monofásico (1F)", "Trifásico (3F)"], key="sist")
st.markdown("---")

# --- INTERFAZ DASHBOARD (GRID 2x2) ---
col1, col2 = st.columns(2)
col3, col4 = st.columns(2)


# =========================================================
# MÓDULO 1: AMPACIDAD (col1)
# =========================================================
with col1:
    st.markdown('<div class="module-box">', unsafe_allow_html=True)
    st.markdown('<p class="header-style">1. Capacidad y Protección</p>', unsafe_allow_html=True)
    
    st.caption("Configuración del Circuito")
    calibre_sel = st.selectbox("Calibre a Evaluar", list(db_cables.keys()), index=1, key="c_sel")
    num_conductores = st.number_input("N° Conductores Activos", value=3, key="n_cond")

    st.caption("Factores Ambientales (CEN 310.15)")
    temp_factor_key = st.selectbox(
        "Rango de Temperatura Ambiente",
        list(db_temp_factors.keys()),
        index=3, 
        key="temp_factor_key"
    )
    
    # CÁLCULOS
    fc_temp = db_temp_factors[temp_factor_key]
    fp = 0.90 
    denom = voltaje if "Monofásico" in sistema else (voltaje * 1.732)
    corriente_carga = carga_va / denom
    
    fc_agrup = 1.0
    if 4 <= num_conductores <= 6: fc_agrup = 0.8
    elif num_conductores >= 7: fc_agrup = 0.7
    
    amp_base = db_cables[calibre_sel]["amp"]
    amp_real = amp_base * fc_temp * fc_agrup
    i_diseno = corriente_carga * 1.25
    breaker_ideal = next((b for b in db_breakers if b >= i_diseno), 20)

    # Mostrar Resultados Ampacidad
    st.markdown("---")
    res_a1, res_a2 = st.columns(2)
    res_a1.metric("Corriente Diseño (Ireq)", f"{i_diseno:.2f} A")
    res_a2.metric("Ampacidad Corregida", f
