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
    res_a2.metric("Ampacidad Corregida", f"{amp_real:.2f} A")
    
    if amp_real >= i_diseno:
        st.markdown(f'<div class="success-box-final">✅ CUMPLE: Cable es apto. (Protección sugerida: {breaker_ideal}A)</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="fail-box-final">❌ FALLA: El calibre es insuficiente.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# MÓDULO 2: CAÍDA DE TENSIÓN (col2)
# =========================================================
with col2:
    st.markdown('<div class="module-box">', unsafe_allow_html=True)
    st.markdown('<p class="header-style">2. Caída de Tensión</p>', unsafe_allow_html=True)
    
    col2a, col2b = st.columns(2)
    with col2a:
        distancia = st.number_input("Longitud (metros)", value=20.0, key="dist")
    with col2b:
        corriente_calc = st.number_input("Corriente (A)", value=corriente_carga, key="i_calc") 
    
    st.caption("Factor K de su Metodología de Cálculo")
    k_mode_key = st.selectbox("Sistema de Fases y Factor K", 
                              ["Monofásico (K=5.0)", "Trifásico (K=10.0)"], 
                              index=0 if "Monofásico" in sistema else 1,
                              key="k_mode_final")
    
    K_FINAL = 5.0 if "Monofásico" in k_mode_key else 10.0
    
    fp_v = st.slider("Factor Potencia", 0.8, 1.0, 0.90, key="fp_v")
    calibre_v = st.selectbox("Calibre para cálculo", list(db_cables.keys()), index=1, key="v_cal")
    
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
    res_v2.metric("% Caída de Tensión", f"{percent_drop:.2f} %")
    
    if percent_drop <= 3.0:
         st.markdown('<div class="success-box-final">✅ CUMPLE: Caída inferior al 3%.</div>', unsafe_allow_html=True)
    else:
         st.markdown('<div class="fail-box-final">❌ NO CUMPLE: Caída excesiva.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# MÓDULO 3: CANALIZACIONES (col3)
# =========================================================
with col3:
    st.markdown('<div class="module-box">', unsafe_allow_html=True)
    st.markdown('<p class="header-style">3. Canalizaciones</p>', unsafe_allow_html=True)
    
    st.subheader("Configuración")
    material_sel = st.selectbox("Material de Tubería", ["PVC40", "EMT", "ARG"], key="mat_sel")
    calibre_t = st.selectbox("Calibre Conductores", list(db_cables.keys()), index=1, key="t_cal")
    n_hilos = st.number_input("Total Hilos (Fases+Neutro+Tierra)", 1, 30, 4, key="n_hilos")

    # LÓGICA DE OVERRIDE DE ÁREA
    area_default = db_cables[calibre_t]["area"]
    override_area = st.checkbox("Usar Área Unitaria Personalizada", key="override_area")
    
    if override_area:
        area_uni = st.number_input(
            f"Área Unitaria Custom (mm²) para {calibre_t}", 
            value=area_default, 
            key="custom_area_uni",
            help="Introduzca el valor de mm² que usa en su Memoria de Cálculo para igualar el % de ocupación."
        )
    else:
        area_uni = area_default
    
    st.caption(f"Área Unitaria Usada: **{area_uni:.2f} mm²**")

    # CÁLCULOS
    area_ocup = n_hilos * area_uni
    limite = 53 if n_hilos == 1 else (31 if n_hilos == 2 else 40)
    area_necesaria_100 = area_ocup * 100 / limite
    tubo_recomendado = "No disponible"
    
    for size, areas in db_tuberias.items():
        area_disponible = areas[material_sel]
        if area_disponible >= area_necesaria_100:
            tubo_recomendado = size
            break
            
    # Módulo de Verificación
    st.markdown("---")
    st.markdown(f'<div class="recommendation-box">✅ Diámetro Mínimo Requerido ({material_sel}): <b>{tubo_recomendado}</b></div>', unsafe_allow_html=True)
    
    tubo_a_verificar = st.selectbox("Verificar Diámetro", list(db_tuberias.keys()), index=1, key="tubo_verif")
    area_tubo_verif = db_tuberias[tubo_a_verificar][material_sel]
    porc_verif = (area_ocup / area_tubo_verif) * 100
    
    if porc_verif <= limite:
        st.markdown(f'<div class="success-box-final">✅ Ocupación {porc_verif:.2f}% (Máx {limite}%).</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="fail-box-final">❌ SATURADO: Ocupación {porc_verif:.2f}% (Máx {limite}%).</div>', unsafe_allow_html=True)
        
    tubo_sel = tubo_a_verificar
    porcentaje = porc_verif
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# MÓDULO 4: CORTOCIRCUITO (col4)
# =========================================================
with col4:
    st.markdown('<div class="module-box">', unsafe_allow_html=True)
    st.markdown('<p class="header-style">4. Cortocircuito (Cálculo Automático Térmico)</p>', unsafe_allow_html=True)
    
    st.subheader("Verificación Térmica (Conductor)")
    calibre_cc = st.selectbox("Calibre a Verificar", list(db_cables.keys()), index=1, key="cc_cal_final")
    
    st.caption("Parámetros de Falla")
    i_cap_interrupcion = st.number_input("Capacidad de Interrupción del Tablero (kA)", value=10.0, step=0.5, key="i_cap_int") * 1000 # Convertir a Amps
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
    m_cc1.metric("Icc Máx. Permisible (Conductor)", f"{i_cc_max_permitida/1000:.2f} kA")
    m_cc2.metric("Icc del Tablero (Ref.)", f"{i_cap_interrupcion/1000:.1f} kA")

    if i_cc_max_permitida >= i_cap_interrupcion:
        st.markdown('<div class="success-box-final">✅ CUMPLE: Cable soporta el nivel de cortocircuito del tablero.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="fail-box-final">❌ FALLA TÉRMICA: El cable podría fundirse ante la falla máxima del tablero.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# 5. GENERADOR PDF (Botón de Imprimir)
# =========================================================
def create_pdf(carga, vol, sist, cal_amp, temp_key, area_uni_mm2, amp, i_dis, v_dp, v_pct, tub, porc_tub, tubo_rec, i_cc_max_cond, i_cc_tablero, k_factor_utilizado, cal_v, R_v, X_v, fp_v, I_carga, amp_base_val, i_breaker_val, num_cond_val, calibre_t, distancia_metros, tiempo_despeje_seg, material_seleccionado):
    
    # Obtener valores detallados
    fc_temp_val = db_temp_factors[temp_key]
    
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 14)
            self.cell(0, 10, 'PROTOCOLO DE DIMENSIONAMIENTO ELÉCTRICO (CEN-2004)', 0, 1, 'C') 
            self.ln(5)
            self.set_font('Arial', 'I', 10)
            if 'current_date' in st.session_state:
                self.cell(0, 5, f"Fecha de Generación: {st.session_state.current_date}", 0, 1, 'R')
            self.ln(2)

    if 'current_date' not in st.session_state:
         st.session_state.current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    
    # ----------------------------------------------------
    # RESUMEN DE RESULTADOS (INICIO DEL PDF)
    # ----------------------------------------------------
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 7, "RESUMEN DE RESULTADOS", 1, 1, 'L', 1)
    pdf.set_font("Arial", size=10)
    
    res_amp = "CUMPLE" if amp >= i_dis else "FALLA"
    res_v = "CUMPLE" if v_pct <= 3 else "FALLA"
    res_t = "CUMPLE" if porc_tub <= 40 else "FALLA"
    res_cc = "CUMPLE" if i_cc_max_cond >= i_cc_tablero else "FALLA"

    pdf.cell(0, 5, f"1. Ampacidad ({cal_amp}): {amp:.2f} A (Req: {i_dis:.2f} A) -> {res_amp}", ln=True)
    pdf.cell(0, 5, f"2. Caída Tensión ({cal_v}): {v_dp:.2f} V ({v_pct:.2f}%) -> {res_v}", ln=True)
    pdf.cell(0, 5, f"3. Tubería ({tub}): Ocupación {porc_tub:.2f}% (Mín. {tubo_rec}) -> {res_t}", ln=True)
    pdf.cell(0, 5, f"4. Cortocircuito: Cap. Térmica {i_cc_max_cond/1000:.2f} kA (Cap. Tablero {i_cc_tablero/1000:.1f} kA) -> {res_cc}", ln=True)
    pdf.ln(5)
    
    # ----------------------------------------------------
    # SECCIÓN 6: CÁLCULO DEL CONDUCTOR (METODOLOGÍA)
    # ----------------------------------------------------
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "6. CÁLCULO DEL CONDUCTOR", 0, 1, 'L')
    pdf.ln(1)
    
    # 6.1 Selección del Conductor por Capacidad de Corriente
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, "6.1 Selección del Conductor por Capacidad de Corriente.", 0, 1, 'L')
    pdf.set_font("Arial", size=10)
    
    texto_61 = f"Empleando la tabla 310-16 del Código Eléctrico Nacional (CEN-2004), se obtiene la ampacidad base de {amp_base_val:.2f} A para el calibre {cal_amp}. Adicionalmente, se aplica un factor de corrección por temperatura y un factor por agrupamiento (si aplica), resultando una Ampacidad Corregida de {amp:.2f} A. La corriente de diseño requerida es Ireq = I_Carga x 1.25 = {I_carga:.2f} A x 1.25 = {i_dis:.2f} A."
    pdf.multi_cell(0, 5, texto_61)
    
    pdf.ln(1)
    
    # 6.5 Cálculo del Factor de Corrección por Temperatura de Alimentadores en Baja Tensión
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, "6.5 Cálculo del Factor de Corrección por Temperatura de Alimentadores en Baja Tensión.", 0, 1, 'L')
    pdf.set_font("Arial", size=10)
    
    pdf.multi_cell(0, 5, "Este ajuste se realiza de acuerdo a los factores contemplados en la Tabla 310.16 del CEN. El factor de corrección depende del tipo de conductor y de la temperatura ambiente.")
    
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 5, u'FC_{Temp} = (TC - TA_2) / (TC - TA_1)', 0, 1, 'L')
    pdf.set_font("Arial", size=10)
    
    texto_65_res = f"Para el caso de conductores tipo THW-75°C y una temperatura ambiente de 40°C, el factor de corrección de la metodología es típicamente {fc_temp_val:.2f} (correspondiente al rango {temp_key})."
    pdf.multi_cell(0, 5, texto_65_res)
    pdf.ln(1)
    
    # 6.2 Selección del Conductor por Caída de Tensión
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, "6.2 Selección del Conductor por Caída de Tensión.", 0, 1, 'L')
    pdf.set_font("Arial", size=10)
    
    texto_62_intro = "La selección por caída de tensión tiene por objeto dimensionar el conductor a fin de que la caída de tensión que ocurre en él con la corriente nominal de carga no pase los límites admisibles (3% recomendado CEN)."
    pdf.multi_cell(0, 5, texto_62_intro)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, "a. El cálculo de la caída de tensión se realiza basado en las siguientes ecuaciones (Fórmula del Centro de Carga):", 0, 1, 'L')
    pdf.set_font("Arial", 'I', 10)
    
    if "Monofásico" in sist:
        pdf.cell(0, 5, u"Sistemas Monofásicos: \u0394V % = KVA \u22c5 L \u22c5 (r\u22c5cos\u03a6 + x\u22c5sen\u03a6) / (K \u22c5 kV\u00b2)", 0, 1, 'L') 
    else:
        pdf.cell(0, 5, u"Sistemas Trifásicos: \u0394V % = KVA \u22c5 L \u22c5 (r\u22c5cos\u03a6 + x\u22c5sen\u03a6) / (K \u22c5 kV\u00b2)", 0, 1, 'L')
        
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 5, f"La metodología adoptada utiliza un factor K personalizado de {k_factor_utilizado:.1f} para sistemas {sist}. Para el calibre {cal_v} (R={R_v:.2f} \u03a9/Km, X={X_v:.3f} \u03a9/Km) y una longitud de {distancia_metros:.1f} m, la caída calculada es: {v_pct:.2f}%.")
    pdf.ln(1)
    
    # 6.6 Cálculo del Factor de Corrección por Temperatura de Alimentadores en Media Tensión (Solo estructura, sin PDVSA)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, "6.6 Cálculo del Factor de Corrección por Temperatura de Alimentadores en Media Tensión.", 0, 1, 'L')
    pdf.set_font("Arial", size=10)
    
    pdf.multi_cell(0, 5, f"Para alimentadores en Media Tensión (2001 V – 35000 V), el factor de corrección de la ampacidad nominal por temperatura se calcula de acuerdo a la fórmula indicada en la sección 310.60 del CEN. Nota: Este cálculo no aplica para el presente dimensionamiento de Baja Tensión (<=600V).")
    pdf.ln(1)
    
    # 6.7 Selección del Conductor por Capacidad de Cortocircuito
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, "6.7 Selección del Conductor por Capacidad de Cortocircuito.", 0, 1, 'L')
    pdf.set_font("Arial", size=10)
    
    texto_67_intro = f"Según el Estándar IEEE 242 – 2001 capítulo 9, la capacidad térmica del conductor es verificada. La corriente de cortocircuito máxima soportable se calcula con la constante térmica K=105 (Cobre), considerando un tiempo de despeje de falla de {tiempo_despeje_seg:.2f} seg. (usando 5 ciclos=0.083s como referencia IEEE 242, Tabla 9.3a)."
    pdf.multi_cell(0, 5, texto_67_intro)

    pdf.set_font("Arial", 'I', 10) 
    pdf.cell(0, 5, u'  I_{cc} = (K \u22c5 A_{kcmil}) / \u221A(t)', 0, 1, 'L')
    pdf.set_font("Arial", size=10)
    
    texto_67_res = f"El calibre {calibre_cc} tiene una Capacidad Térmica de {i_cc_max_cond/1000:.2f} kA. Este valor es comparado con la Capacidad de Interrupción del Tablero ({i_cc_tablero/1000:.1f} kA). Resultado: {res_cc}."
    pdf.multi_cell(0, 5, texto_67_res)
    pdf.ln(3)

    # ----------------------------------------------------
    # SECCIÓN 7: DIMENSIONAMIENTO
    # ----------------------------------------------------
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "7. DIMENSIONAMIENTO DE CANALIZACIONES Y PROTECCIÓN", 0, 1, 'L')
    pdf.ln(1)

    # 7.0 Tubería
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, "7.0 Dimensionamiento de Tubería (Canalizaciones).", 0, 1, 'L')
    pdf.set_font("Arial", size=10)
    
    pdf.multi_cell(0, 5, "El dimensionamiento de tubos eléctricos se realiza de manera que los cables en su interior no excedan los porcentajes establecidos en la Tabla N° 1, Capítulo 9, CEN-2004.")
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, "Tabla Nº 1. Porcentaje de Área de Tubería que puede ser llenada (CEN-2004)", 0, 1, 'L')
    pdf.set_font("Arial", size=10)
    
    # Simulación de tabla de ocupación (Texto fijo del CEN)
    pdf.cell(30, 5, "Nº Cables", 1, 0, 'C')
    pdf.cell(30, 5, "1", 1, 0, 'C')
    pdf.cell(30, 5, "2", 1, 0, 'C')
    pdf.cell(30, 5, ">2", 1, 1, 'C')
    pdf.cell(30, 5, "Ocupación Máx.", 1, 0, 'L')
    pdf.cell(30, 5, "53%", 1, 0, 'C')
    pdf.cell(30, 5, "31%", 1, 0, 'C')
    pdf.cell(30, 5, "40%", 1, 1, 'C')
    pdf.ln(1)
    
    pdf.multi_cell(0, 5, f"Los cálculos están basados en la siguiente expresión (Área Total/Área Tubo): El Área Unitaria del Conductor utilizado es de {area_uni_mm2:.2f} mm². Tubería Requerida: {tubo_rec} ({material_seleccionado}). Ocupación Verificada: {porc_tub:.2f}% (Resultado: {res_t}).")
    pdf.ln(1)
    
    # 7.1 Dimensionamiento de la Protección
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, "7.1 Dimensionamiento de la Protección.", 0, 1, 'L')
    pdf.set_font("Arial", size=10)

    pdf.multi_cell(0, 5, "Para la selección de protecciones de equipos y alimentadores, en baja tensión, éstas serán del tipo interruptor termomagnético. Se utiliza la siguiente fórmula (Ver CEN, Art. 210-2):")
    
    pdf.set_font("Arial", 'I', 10) 
    pdf.cell(0, 5, u'  I_{Protección} \u2265 I_{Carga} \u22c5 1.25', 0, 1, 'L')
    pdf.set_font("Arial", size=10)

    texto_71 = f"La corriente de diseño calculada es Ireq = {i_dis:.2f} A. El valor comercial superior inmediato se verifica según el CEN, Capítulo 2, Art. 240-6. El Interruptor termomagnético seleccionado es de {i_breaker_val:.1f} A."
    pdf.multi_cell(0, 5, texto_71)

    return pdf.output(dest='S').encode('latin-1')

# --- BARRA LATERAL (DESCARGA) ---
st.sidebar.markdown("---")
st.sidebar.header("📄 Reportes")

if 'amp_real' in locals():
    # Variables a pasar al PDF
    I_carga = corriente_carga
    amp_base_val = amp_base
    i_breaker_val = breaker_ideal
    R_v = db_cables[calibre_v]["R"]
    X_v = db_cables[calibre_v]["X"]
    fp_v = locals().get('fp_v', 0.90)
    
    # Inicialización de fecha para el PDF
    if 'current_date' not in st.session_state:
         st.session_state.current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Eliminamos las asignaciones a st.session_state que causaban el error
    # y usamos las variables locales que sí están definidas: distancia, tiempo_despeje, material_sel
    
    area_uni_final = locals().get('area_uni', db_cables[calibre_sel]["area"])
    K_FINAL_REPORT = locals().get('K_FINAL', 5.0) 
    
    pdf_bytes = create_pdf(
        carga_va, voltaje, sistema, calibre_sel, temp_factor_key, area_uni_final,
        amp_real, i_diseno, 
        v_drop, percent_drop, tubo_sel, porcentaje, tubo_recomendado, 
        i_cc_max_permitida, i_cap_interrupcion, K_FINAL_REPORT,
        calibre_v, R_v, X_v, fp_v, I_carga, amp_base_val, i_breaker_val, 
        num_conductores, calibre_sel, 
        # Nuevos argumentos pasados para el PDF (variables locales)
        distancia, tiempo_despeje, material_sel
    )
    st.sidebar.download_button("📥 Descargar Memoria PDF", pdf_bytes, "protocolo_dimensionamiento_cen.pdf", "application/pdf")
