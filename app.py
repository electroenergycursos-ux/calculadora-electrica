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

# Base de datos de tuberías ampliada hasta 6"
db_tuberias_full = {
    "1/2\"": {"PVC40": 184, "EMT": 196, "ARG": 192}, "3/4\"": {"PVC40": 327, "EMT": 353, "ARG": 346},
    "1\"":   {"PVC40": 568, "EMT": 595, "ARG": 583}, "1 1/4\"": {"PVC40": 986, "EMT": 1026, "ARG": 1005},
    "1 1/2\"": {"PVC40": 1338, "EMT": 1391, "ARG": 1362}, "2\"":   {"PVC40": 2186, "EMT": 2275, "ARG": 2228},
    "2 1/2\"": {"PVC40": 3315, "EMT": 3447, "ARG": 3377}, "3\"":   {"PVC40": 4656, "EMT": 4837, "ARG": 4738},
    "3 1/2\"": {"PVC40": 6397, "EMT": 6625, "ARG": 6492}, "4\"":   {"PVC40": 8392, "EMT": 8708, "ARG": 8530},
    "5\"":   {"PVC40": 12850, "EMT": 13320, "ARG": 13050}, "6\"":   {"PVC40": 17940, "EMT": 18600, "ARG": 18210},
}
lista_tuberias = list(db_tuberias_full.keys())


# Inicialización de variables (solo para scope inicial)
carga_va, voltaje, sistema, calibre_sel, num_conductores, amp_real, i_diseno = 1260.0, 120, "Monofásico (1F)", "12 AWG", 3, 22.0, 13.12
percent_drop = 1.83
v_drop = 2.2
tubo_sel, porcentaje, limite = "3/4\"", 40.0, 40
tubo_recomendado = "1\""
area_kcmil_min = 6.53 
calibre_min_cc = "12 AWG"
K_FINAL = 5.0 
i_cc_max_permitida = 0.0
fc_agrup = 1.0 # Variable inicializada para scope del PDF

# --- INTERFAZ DE ENTRADA (Módulo de Configuración Común) ---
st.header("1. Configuracion del Sistema")
col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
with col_cfg1:
    carga_va = st.number_input("Carga Total (VA)", value=1260.0, step=100.0, key="c_va")
with col_cfg2:
    voltaje = st.selectbox("Tension de Servicio (V)", [120, 208, 480], index=0, key="v_ser")
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
    st.markdown('<p class="header-style">1. Capacidad y Proteccion (CEN 310.15)</p>', unsafe_allow_html=True)
    
    st.caption("Configuracion del Circuito")
    calibre_sel = st.selectbox("Calibre a Evaluar", list(db_cables.keys()), index=1, key="c_sel")
    
    # N° de Conductores Portadores de Corriente (Corregido)
    st.caption("N° Conductores Portadores de Corriente (FA)")
    num_conductores = st.number_input("N° Conductores Activos", value=3, min_value=2, step=1, key="n_cond")

    st.caption("Factores Ambientales")
    temp_factor_key = st.selectbox(
        "Rango de Temperatura Ambiente (FC Temperatura)",
        list(db_temp_factors.keys()),
        index=3, 
        key="temp_factor_key"
    )
    
    # CÁLCULOS RIGUROSOS
    fc_temp = db_temp_factors[temp_factor_key]
    denom = voltaje if "Monofásico" in sistema else (voltaje * 1.732)
    corriente_carga = carga_va / denom
    
    # CÁLCULO DEL FACTOR DE AGRUPAMIENTO (FA)
    fc_agrup = 1.0
    if 4 <= num_conductores <= 6: fc_agrup = 0.8
    elif 7 <= num_conductores <= 9: fc_agrup = 0.7
    elif 10 <= num_conductores <= 20: fc_agrup = 0.5
    elif num_conductores > 20: fc_agrup = 0.45 
    
    # Ampacidad Base usada para corrección (columna 90°C)
    amp_base_90 = db_cables[calibre_sel]["amp_90"]
    # Ampacidad Máxima Permitida por terminales (columna 75°C)
    amp_max_75 = db_cables[calibre_sel]["amp_75"]
    
    # AMPACIDAD CORREGIDA (Cálculo a partir de 90°C)
    amp_corregida = amp_base_90 * fc_temp * fc_agrup
    
    # AMPACIDAD REAL LIMITADA por la temperatura del terminal (CEN 110.14(C))
    amp_real = min(amp_corregida, amp_max_75)
    
    i_diseno = corriente_carga * 1.25
    
    # SELECCIÓN DEL INTERRUPTOR: Regla de redondeo CEN 240.4(B)
    breaker_ideal = next((b for b in db_breakers if b >= i_diseno), 20)
    
    # Mostrar Resultados Ampacidad
    st.markdown("---")
    res_a1, res_a2 = st.columns(2)
    res_a1.metric("Corriente Diseno (Ireq)", f"{i_diseno:.2f} A")
    res_a2.metric("Ampacidad Limite (75°C)", f"{amp_max_75:.2f} A")
    
    st.metric("Ampacidad Corregida (Final)", f"{amp_real:.2f} A", f"FC Agrupamiento: {fc_agrup:.2f}")

    if amp_real >= i_diseno:
        st.markdown(f'<div class="success-box-final">✅ CUMPLE: Cable es apto. (Proteccion sugerida: {breaker_ideal}A)</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="fail-box-final">❌ FALLA: El calibre es insuficiente.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# MÓDULO 2: CAÍDA DE TENSIÓN (col2)
# =========================================================
with col2:
    st.markdown('<div class="module-box">', unsafe_allow_html=True)
    st.markdown('<p class="header-style">2. Caida de Tension</p>', unsafe_allow_html=True)
    
    col2a, col2b = st.columns(2)
    with col2a:
        distancia = st.number_input("Longitud (metros)", value=20.0, key="dist")
    with col2b:
        corriente_calc = st.number_input("Corriente (A)", value=corriente_carga, key="i_calc") 
    
    st.caption("Factor K de su Metodologia de Calculo")
    k_mode_key = st.selectbox("Sistema de Fases y Factor K", 
                              ["Monofasico (K=5.0)", "Trifasico (K=10.0)"], 
                              index=0 if "Monofásico" in sistema else 1,
                              key="k_mode_final")
    
    K_FINAL = 5.0 if "Monofásico" in k_mode_key else 10.0
    
    fp_v = st.slider("Factor Potencia", 0.8, 1.0, 0.90, key="fp_v")
    calibre_v = st.selectbox("Calibre para calculo", list(db_cables.keys()), index=1, key="v_cal")
    
    # CÁLCULOS
    datos = db_cables[calibre_v]
    R, X = datos["R"], datos["X"]
    theta = np.arccos(fp_v)
    L_km = distancia / 1000.0
    impedancia = (R * fp_v) + (X * np.sin(theta))
    v_drop = K_FINAL * corriente_calc * L_km * impedancia
    percent_drop = (v_drop / voltaje) * 100
    
    st.markdown("---")
    st.subheader("📊 Resultados")
    res_v1, res_v2 = st.columns(2)
    res_v1.metric("Factor K Utilizado", f"{K_FINAL:.1f}")
    res_v2.metric("% Caida de Tension", f"{percent_drop:.2f} %")
    
    if percent_drop <= 3.0:
         st.markdown('<div class="success-box-final">✅ CUMPLE: Caida inferior al 3%.</div>', unsafe_allow_html=True)
    else:
         st.markdown('<div class="fail-box-final">❌ NO CUMPLE: Caida excesiva.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# MÓDULO 3: CANALIZACIONES (col3)
# =========================================================
with col3:
    st.markdown('<div class="module-box">', unsafe_allow_html=True)
    st.markdown('<p class="header-style">3. Canalizaciones (CEN Cap. 9)</p>', unsafe_allow_html=True)
    
    st.subheader("Configuracion")
    material_sel = st.selectbox("Material de Tuberia", ["PVC40", "EMT", "ARG"], key="mat_sel")
    calibre_t = st.selectbox("Calibre Conductores", list(db_cables.keys()), index=1, key="t_cal")
    n_hilos_canal = st.number_input("Total Hilos (Fases+Neutro+Tierra)", 1, 30, 4, key="n_hilos_canal")

    # LÓGICA DE OVERRIDE DE ÁREA
    area_default = db_cables[calibre_t]["area"]
    override_area = st.checkbox("Usar Area Unitaria Personalizada", key="override_area")
    
    if override_area:
        area_uni = st.number_input(
            f"Area Unitaria Custom (mm²) para {calibre_t}", 
            value=area_default, 
            key="custom_area_uni",
            help="Introduzca el valor de mm² que usa en su Memoria de Calculo para igualar el % de ocupacion."
        )
    else:
        area_uni = area_default
    
    st.caption(f"Area Unitaria Usada: **{area_uni:.2f} mm²**")

    # CÁLCULOS
    area_ocup = n_hilos_canal * area_uni
    
    # FIX CONCEPTUAL: Se ajusta el límite de llenado según el número de hilos (CEN Cap. 9 Tabla 1)
    if n_hilos_canal == 1:
        limite = 53
    elif n_hilos_canal == 2:
        limite = 31
    else:
        limite = 40 # Para más de dos conductores
        
    area_necesaria_100 = area_ocup * 100 / limite
    tubo_recomendado = "No disponible"
    
    for size, areas in db_tuberias_full.items():
        area_disponible = areas[material_sel]
        if area_disponible >= area_necesaria_100:
            tubo_recomendado = size
            break
            
    # Módulo de Verificación
    st.markdown("---")
    st.markdown(f'<div class="recommendation-box">✅ Diametro Minimo Requerido ({material_sel}): <b>{tubo_recomendado}</b></div>', unsafe_allow_html=True)
    
    tubo_a_verificar = st.selectbox("Verificar Diametro", lista_tuberias, index=1, key="tubo_verif")
    
    area_tubo_verif = db_tuberias_full[tubo_a_verificar][material_sel]
    porc_verif = (area_ocup / area_tubo_verif) * 100
    
    if porc_verif <= limite:
        st.markdown(f'<div class="success-box-final">✅ Ocupacion {porc_verif:.2f}% (Max {limite}%).</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="fail-box-final">❌ SATURADO: Ocupacion {porc_verif:.2f}% (Max {limite}%).</div>', unsafe_allow_html=True)
        
    tubo_sel = tubo_a_verificar
    porcentaje = porc_verif
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# MÓDULO 4: CORTOCIRCUITO (col4)
# =========================================================
with col4:
    st.markdown('<div class="module-box">', unsafe_allow_html=True)
    st.markdown('<p class="header-style">4. Cortocircuito (Calculo Automatico Termico IEEE 242)</p>', unsafe_allow_html=True)
    
    st.subheader("Verificacion Termica (Conductor)")
    calibre_cc = st.selectbox("Calibre a Verificar", list(db_cables.keys()), index=1, key="cc_cal_final")
    
    st.caption("Parametros de Falla")
    i_cap_interrupcion = st.number_input("Capacidad de Interrupcion del Tablero (kA)", value=10.0, step=0.5, key="i_cap_int") * 1000 # Convertir a Amps
    tiempo_despeje = st.number_input("Tiempo de Despeje (t, segundos)", value=0.5, key="t_despeje")

    
    K_CONST = 105.0 
    area_real_kcmil = db_cables[calibre_cc]['kcmil']
    
    # CÁLCULO AUTOMÁTICO DE Icc MÁXIMA PERMITIDA
    if area_real_kcmil > 0 and tiempo_despeje > 0:
        i_cc_max_permitida = (K_CONST * area_real_kcmil) / np.sqrt(tiempo_despeje)
    else:
        i_cc_max_permitida = 0.0

    st.markdown("---")
    st.subheader("📊 Resultados de la Capacidad")
    m_cc1, m_cc2 = st.columns(2)
    m_cc1.metric("Icc Max. Permisible (Conductor)", f"{i_cc_max_permitida/1000:.2f} kA")
    m_cc2.metric("Icc del Tablero (Ref.)", f"{i_cap_interrupcion/1000:.1f} kA")

    if i_cc_max_permitida >= i_cap_interrupcion:
        st.markdown('<div class="success-box-final">✅ CUMPLE: Cable soporta el nivel de cortocircuito del tablero.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="fail-box-final">❌ FALLA TERMICA: El cable podria fundirse ante la falla maxima del tablero.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# 5. GENERADOR PDF (Reporte Simplificado)
# =========================================================
def create_pdf(carga, vol, sist, cal_amp, temp_key, area_uni_mm2, amp, i_dis, v_dp, v_pct, tub, porc_tub, tubo_rec, i_cc_max_cond, i_cc_tablero, k_factor_utilizado, cal_v, R_v, X_v, fp_v, I_carga, amp_base_val_90, i_breaker_val, num_cond_portadores, calibre_t, distancia_metros, tiempo_despeje_seg, material_seleccionado, fc_agrup_val, amp_max_75_val, limite_ocupacion):
    
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 14)
            self.cell(0, 10, 'PROTOCOLO DE DIMENSIONAMIENTO ELECTRICO (CEN-2004)', 0, 1, 'C') 
            self.ln(5)
            self.set_font('Arial', 'I', 10)
            if 'current_date' in st.session_state:
                self.cell(0, 5, f"Fecha de Generacion: {st.session_state.current_date}", 0, 1, 'R')
            self.ln(2)

    if 'current_date' not in st.session_state:
         st.session_state.current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    pdf = FPDF(unit='mm')
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    
    # ----------------------------------------------------
    # SECCION DE PARAMETROS DE ENTRADA
    # ----------------------------------------------------
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 7, "1. PARAMETROS DE ENTRADA", 1, 1, 'L', 1)
    pdf.set_font("Arial", size=10)
    
    pdf.cell(0, 5, f"Carga (VA): {carga:.2f} | Voltaje (V): {vol:.1f} | Sistema: {sist}", ln=True)
    pdf.cell(0, 5, f"Calibre Analizado: {cal_amp} | Longitud (m): {distancia_metros:.1f} | Factor K: {k_factor_utilizado:.1f}", ln=True)
    pdf.cell(0, 5, f"Temp. Ambiente: {temp_key} | Cond. Activos: {num_cond_portadores:.0f}", ln=True)
    pdf.cell(0, 5, f"Cap. Interrupcion Tablero (kA): {i_cc_tablero/1000:.1f} | T. Despeje (s): {tiempo_despeje_seg:.2f}", ln=True)
    pdf.ln(5)

    # ----------------------------------------------------
    # RESUMEN DE RESULTADOS (PRINCIPAL)
    # ----------------------------------------------------
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 7, "2. RESUMEN DE RESULTADOS Y VERIFICACIONES", 1, 1, 'L', 1)
    pdf.set_font("Arial", size=10)
    
    res_amp = "CUMPLE" if amp >= i_dis else "FALLA"
    res_v = "CUMPLE (<3%)" if v_pct <= 3 else "FALLA (>3%)"
    res_t = "CUMPLE (<40%)" if porc_tub <= limite_ocupacion else "FALLA (>40%)"
    res_cc = "CUMPLE" if i_cc_max_cond >= i_cc_tablero else "FALLA"

    # Resultados Ampacidad
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, "2.1. AMPACIDAD Y PROTECCION (CEN 310.15)", 0, 1, 'L')
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 5, f"I_Diseno (125%): {i_dis:.2f} A | Ampacidad Base (90C): {amp_base_val_90:.2f} A", ln=True)
    pdf.cell(0, 5, f"FC Temp: {db_temp_factors[temp_key]:.2f} | FC Agrupamiento: {fc_agrup_val:.2f}", ln=True)
    pdf.cell(0, 5, f"I_Max_Terminal (75C): {amp_max_75_val:.2f} A | I_Corregida (Final): {amp:.2f} A", ln=True)
    pdf.cell(0, 5, f"Proteccion Sugerida: {i_breaker_val:.1f} A | Estado: {res_amp}", ln=True)
    pdf.ln(2)

    # Resultados Caída de Tensión
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, "2.2. CAIDA DE TENSION (CEN 210.19)", 0, 1, 'L')
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 5, f"Caida de Tension: {v_dp:.2f} V ({v_pct:.2f}%)", ln=True)
    pdf.cell(0, 5, f"Estado: {res_v}", ln=True)
    pdf.ln(2)

    # Resultados Canalizaciones
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, "2.3. CANALIZACIONES (CEN Cap. 9)", 0, 1, 'L')
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 5, f"Tuberia Verificada: {tub} ({material_seleccionado}) | Ocupacion: {porc_tub:.2f}% (Max {limite_ocupacion}%)", ln=True)
    pdf.cell(0, 5, f"Diametro Minimo Requerido: {tubo_rec}", ln=True)
    pdf.cell(0, 5, f"Estado: {res_t}", ln=True)
    pdf.ln(2)
    
    # Resultados Cortocircuito
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, "2.4. CORTOCIRCUITO (IEEE 242)", 0, 1, 'L')
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 5, f"Icc Max. Soportada por {cal_amp}: {i_cc_max_cond/1000:.2f} kA", ln=True)
    pdf.cell(0, 5, f"Icc del Tablero (Ref.): {i_cc_tablero/1000:.1f} kA", ln=True)
    pdf.cell(0, 5, f"Estado: {res_cc}", ln=True)

    return pdf.output(dest='S')

# --- BARRA LATERAL (DESCARGA) ---
st.sidebar.markdown("---")
st.sidebar.header("📄 Reportes")

if 'amp_real' in locals():
    # Variables a pasar al PDF
    I_carga = corriente_carga
    amp_base_val_90 = amp_base_90
    i_breaker_val = breaker_ideal
    R_v = db_cables[calibre_v]["R"]
    X_v = db_cables[calibre_v]["X"]
    fp_v = locals().get('fp_v', 0.90)
    
    # Inicialización de fecha para el PDF
    if 'current_date' not in st.session_state:
         st.session_state.current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Valores de los widgets obtenidos de st.session_state (la forma más segura)
    distancia_val = st.session_state.get('dist', 20.0) 
    tiempo_despeje_val = st.session_state.get('t_despeje', 0.5)
    material_sel_val = st.session_state.get('mat_sel', 'PVC40')
    
    area_uni_final = locals().get('area_uni', db_cables[calibre_sel]["area"])
    K_FINAL_REPORT = locals().get('K_FINAL', 5.0) 
    
    # Nuevos valores de Ampacidad para el PDF
    fc_agrup_val = locals().get('fc_agrup', 1.0)
    amp_max_75_val = locals().get('amp_max_75', 0.0)
    limite_ocupacion = locals().get('limite', 40)
    
    pdf_bytes = create_pdf(
        carga_va, voltaje, sistema, calibre_sel, temp_factor_key, area_uni_final,
        amp_real, i_diseno, 
        v_drop, percent_drop, tubo_sel, porcentaje, tubo_recomendado, 
        i_cc_max_permitida, i_cap_interrupcion, K_FINAL_REPORT,
        calibre_v, R_v, X_v, fp_v, I_carga, amp_base_val_90, i_breaker_val, 
        num_conductores, calibre_sel, 
        # Argumentos finales pasados a la función PDF
        distancia_val, tiempo_despeje_val, material_sel_val,
        fc_agrup_val, amp_max_75_val, limite_ocupacion
    )
    st.sidebar.download_button("📥 Descargar Memoria PDF", pdf_bytes, "protocolo_dimensionamiento_cen.pdf", "application/pdf")
