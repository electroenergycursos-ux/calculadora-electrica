import streamlit as st
import numpy as np
from fpdf import FPDF
import base64

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS ---
st.set_page_config(page_title="CEN-2004: Protocolo de Dimensionamiento Eléctrico", layout="wide", page_icon="⚡")

st.markdown("""
<style>
    .header-style { font-size:18px; font-weight:bold; color: #1e40af; border-bottom: 2px solid #1e40af; padding-bottom: 5px; margin-bottom: 15px;}
    
    /* Cajas de Módulos (Estilo de la imagen) */
    .module-box { border: 1px solid #e0e0e0; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 2px 2px 8px rgba(0,0,0,0.05);}
    
    /* Indicadores de APROBADO/FALLA */
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
    fp = 0.90 # Se asume FP 0.90 de Tomacorriente
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
        st.markdown(f'<div class="fail-box-final">❌ FALLA: El calibre es insuficiente.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# MÓDULO 2: CAÍDA DE TENSIÓN (col2)
# =========================================================
with col2:
    st.markdown('<div class="module-box">', unsafe_allow_html=True)
    st.markdown('<p class="header-style">2. Caída de Tensión (CEN 210.19)</p>', unsafe_allow_html=True)
    
    col2a, col2b = st.columns(2)
    with col2a:
        distancia = st.number_input("Longitud (metros)", value=20.0, key="dist")
    with col2b:
        corriente_calc = st.number_input("Corriente (A)", value=corriente_carga, key="i_calc") 
    
    # Selector K (USANDO LOS VALORES CONFIRMADOS K=5 y K=10)
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
         st.markdown(f'<div class="success-box-final">✅ CUMPLE: Caída inferior al 3%.</div>', unsafe_allow_html=True)
    else:
         st.markdown(f'<div class="fail-box-final">❌ NO CUMPLE: Caída excesiva.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# MÓDULO 3: CANALIZACIONES (col3)
# =========================================================
with col3:
    st.markdown('<div class="module-box">', unsafe_allow_html=True)
    st.markdown('<p class="header-style">3. Canalizaciones (Ocupación CEN Cap. 9)</p>', unsafe_allow_html=True)
    
    st.subheader("Configuración")
    material_sel = st.selectbox("Material de Tubería", ["PVC40", "EMT", "ARG"], key="mat_sel")
    calibre_t = st.selectbox("Calibre Conductores", list(db_cables.keys()), index=1, key="t_cal")
    n_hilos = st.number_input("Total Hilos (Fases+Neutro+Tierra)", 1, 30, 4, key="n_hilos")

    # 🟢 LÓGICA DE OVERRIDE DE ÁREA
    area_default = db_cables[calibre_t]["area"]
    override_area = st.checkbox("Usar Área Unitaria Personalizada", key="override_area")
    
    if override_area:
        area_uni = st.number_input(
            f"Área Unitaria Custom (mm²) para {calibre_t}", 
            value=area_default, 
            key="custom_area_uni",
            help="Introduzca el valor de mm² que usa en su Memoria de Cálculo."
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
    st.markdown('<p class="header-style">4. Cortocircuito (IEEE 242)</p>', unsafe_allow_html=True)
    
    st.subheader("Parámetros de Falla")
    i_falla = st.number_input("Corriente de Falla (Icc, Amps)", value=10000.0, step=500.0, key="i_falla")
    tiempo_despeje = st.number_input("Tiempo de Despeje (t, segundos)", value=0.5, step=0.01, key="t_despeje")

    st.subheader("Verificación Térmica")
    calibre_cc = st.selectbox("Calibre a Verificar", list(db_cables.keys()), index=1, key="cc_cal")
    
    K_CONST = 105.0 
    area_real_kcmil = db_cables[calibre_cc]['kcmil']
    st.caption(f"Área Real ({calibre_cc}): {area_real_kcmil:.2f} kcmil (K=105.0)")


    # Cálculo de Cortocircuito
    if i_falla > 0 and tiempo_despeje > 0:
        area_kcmil_min = i_falla * np.sqrt(tiempo_despeje) / K_CONST
        
        calibre_min_cc = "N/A"
        for cal, data in db_cables.items():
            if data['kcmil'] >= area_kcmil_min:
                calibre_min_cc = cal
                break
    else:
        area_kcmil_min = 0
        calibre_min_cc = "N/A"


    st.markdown("---")
    m_cc1, m_cc2 = st.columns(2)
    m_cc1.metric("Área Mínima Requerida", f"{area_kcmil_min:.2f} kcmil")
    m_cc2.metric("Calibre Mínimo", calibre_min_cc)

    if area_real_kcmil >= area_kcmil_min:
        st.markdown(f'<div class="success-box-final">✅ CUMPLE: Cable es seguro ante falla térmica.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="fail-box-final">❌ FALLA TÉRMICA: Calibre insuficiente.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================
# 5. GENERADOR PDF (En la Barra Lateral - Botón de Imprimir)
# =========================================================
def create_pdf(carga, vol, cal, amp, i_dis, v_dp, v_pct, tub, porc_tub, tubo_rec, cc_req, cc_cal_min, k_factor_utilizado):
    # Lógica PDF
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'PROTOCOLO DE DIMENSIONAMIENTO CEN-2004', 0, 1, 'C') 
            self.ln(5)
    
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    pdf.cell(0, 10, f"Referencia: CEN-2004 (Codigo Electrico Nacional)", ln=True)
    pdf.cell(0, 10, f"Carga: {carga} VA | Tension: {vol} V | Cable: {cal}", ln=True)
    pdf.cell(0, 7, f"Factor K utilizado en Caida de Tension: {k_factor_utilizado:.3f}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10, "RESUMEN DE RESULTADOS:", ln=True)
    pdf.set_font("Arial", size=10)
    
    res_amp = "CUMPLE" if amp >= i_dis else "FALLA"
    pdf.cell(0, 7, f"1. Ampacidad: {amp:.2f} A (Req: {i_dis:.2f} A) -> {res_amp}", ln=True)
    
    res_v = "CUMPLE" if v_pct <= 3 else "FALLA"
    pdf.cell(0, 7, f"2. Caida Tension: {v_drop:.2f} V ({v_pct:.2f}%) -> {res_v}", ln=True)
    
    res_t = "CUMPLE" if porc_tub <= 40 else "FALLA"
    pdf.cell(0, 7, f"3. Tuberia ({tub}): Ocupacion {porc_tub:.2f}% (MINIMO REQ: {tubo_rec}) -> {res_t}", ln=True)
    
    res_cc = "CUMPLE" if db_cables[cal].get('kcmil', 0) >= cc_req else "FALLA"
    pdf.cell(0, 7, f"4. Cortocircuito: Area Req {cc_req:.2f} kcmil (MINIMO {cc_cal_min}) -> {res_cc}", ln=True)

    return pdf.output(dest='S').encode('latin-1')

# --- BARRA LATERAL (DESCARGA) ---
st.sidebar.markdown("---")
st.sidebar.header("📄 Reportes")

if 'amp_real' in locals():
    K_FINAL_REPORT = locals().get('K_FINAL', 2.0) 
    
    pdf_bytes = create_pdf(
        carga_va, voltaje, calibre_sel, amp_real, i_diseno, 
        v_drop, percent_drop, tubo_sel, porcentaje, tubo_recomendado, 
        area_kcmil_min, calibre_min_cc, K_FINAL_REPORT
    )
    st.sidebar.download_button("📥 Descargar Memoria PDF", pdf_bytes, "protocolo_dimensionamiento_cen.pdf", "application/pdf")
