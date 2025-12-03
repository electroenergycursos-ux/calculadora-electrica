import streamlit as st
import numpy as np
from fpdf import FPDF
import base64

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CEN-2004: Protocolo de Dimensionamiento Eléctrico", layout="wide", page_icon="⚡")

st.markdown("""
<style>
    .header-style { font-size:20px; font-weight:bold; color: #004E8C; }
    .success-box { padding: 15px; border-radius: 8px; background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .fail-box { padding: 15px; border-radius: 8px; background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    .recommendation-box { padding: 15px; border-radius: 8px; background-color: #f0f8ff; color: #004E8C; border: 1px solid #b3d9ff; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ CEN-2004: Protocolo de Dimensionamiento Eléctrico")
st.caption("Herramienta de Dimensionamiento Conforme al Código Eléctrico Nacional (CEN-2004)")

# --- 2. BASE DE DATOS DE INGENIERÍA ---
db_cables = {
    # area: mm2 | diam: mm | R, X: Ohm/km | amp: A (75C) | kcmil: kcmil (para Cortocircuito)
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

db_tuberias = {
    "1/2\"": {"PVC40": 184, "EMT": 196, "ARG": 192},
    "3/4\"": {"PVC40": 327, "EMT": 353, "ARG": 346},
    "1\"":   {"PVC40": 568, "EMT": 595, "ARG": 583},
    "1 1/4\"": {"PVC40": 986, "EMT": 1026, "ARG": 1005},
    "1 1/2\"": {"PVC40": 1338, "EMT": 1391, "ARG": 1362},
    "2\"":   {"PVC40": 2186, "EMT": 2275, "ARG": 2228},
}

# Inicialización de variables para el PDF (Usando valores del caso C1)
carga_va, voltaje, sistema, calibre_sel, num_conductores, amp_real, i_diseno = 1260.0, 120, "Monofásico (1F)", "12 AWG", 3, 22.0, 13.12
percent_drop = 1.83
v_drop = 2.2
tubo_sel, porcentaje, limite = "3/4\"", 40.0, 40
tubo_recomendado = "1\""
area_kcmil_min = 6.53 
calibre_min_cc = "12 AWG"

# --- PESTAÑAS (Añadida TAB 4) ---
tab1, tab2, tab3, tab4 = st.tabs(["🛡️ 1. Ampacidad", "📉 2. Caída de Tensión", "pipe 3. Canalizaciones", "💥 4. Cortocircuito"])

# --- MÓDULO 1: AMPACIDAD ---
with tab1:
    st.markdown('<p class="header-style">Selección por Capacidad de Corriente (CEN 310.16)</p>', unsafe_allow_html=True)
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        carga_va = st.number_input("Carga Total (VA)", value=1260.0, step=100.0, key="c_va")
        voltaje = st.selectbox("Tensión de Servicio", [120, 208, 480], index=0, key="v_ser")
        sistema = st.selectbox("Sistema", ["Monofásico (1F)", "Trifásico (3F)"], key="sist")
        tipo_carga = st.radio("Tipo de Carga", ["Iluminación (FP 0.95)", "Tomacorrientes (FP 0.90)"], index=1, key="t_carga")
        
    with col_in2:
        st.info("Condiciones de Diseño (T=40°C):")
        fc_temp = 0.88 
        st.write(f"🔹 Factor Corrección Temp (CEN 310.15): **{fc_temp}**")
        calibre_sel = st.selectbox("Calibre a Evaluar", list(db_cables.keys()), index=1, key="c_sel")
        num_conductores = st.number_input("N° Conductores Activos", value=3, key="n_cond")

    fp = 0.95 if "Iluminación" in tipo_carga else 0.90
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
    c1, c2, c3 = st.columns(3)
    c1.metric("Corriente Carga", f"{corriente_carga:.2f} A")
    c2.metric("Corriente Diseño (125%)", f"{i_diseno:.2f} A")
    c3.metric(f"Capacidad {calibre_sel}", f"{amp_real:.2f} A")

    if amp_real >= i_diseno:
        st.markdown(f'<div class="success-box">✅ <b>APROBADO:</b> El conductor soporta la carga.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="fail-box">❌ <b>INSUFICIENTE:</b> El conductor se sobrecalentará.</div>', unsafe_allow_html=True)

# --- MÓDULO 2: CAÍDA DE TENSIÓN ---
with tab2:
    st.markdown('<p class="header-style">Cálculo de Regulación (CEN 210.19)</p>', unsafe_allow_html=True)
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        distancia = st.number_input("Longitud (metros)", value=20.0, key="dist")
        corriente_calc = st.number_input("Corriente (A)", value=corriente_carga, key="i_calc") 
        calibre_v = st.selectbox("Calibre", list(db_cables.keys()), index=1, key="v_cal")
    
    with col_v2:
        fp_v = st.slider("Factor Potencia", 0.8, 1.0, fp, key="fp_v")
        voltaje_base = st.number_input("Voltaje Base", value=voltaje, key="v_base")
        fases_v = st.radio("Fases", ["1F (K=2)", "3F (K=1.732)"], index=0 if "Monofásico" in sistema else 1, key="fases_v")

    datos = db_cables[calibre_v]
    R, X = datos["R"], datos["X"]
    theta = np.arccos(fp_v)
    K = 2 if "1F" in fases_v else 1.732
    L_km = distancia / 1000.0
    impedancia = (R * fp_v) + (X * np.sin(theta))
    v_drop = K * corriente_calc * L_km * impedancia
    percent_drop = (v_drop / voltaje_base) * 100
    
    st.markdown("---")
    m1, m2 = st.columns(2)
    m1.metric("Caída de Voltaje", f"{v_drop:.2f} V")
    m2.metric("% Regulación", f"{percent_drop:.2f} %")
    
    if percent_drop <= 3.0:
         st.markdown(f'<div class="success-box">✅ <b>CUMPLE:</b> Caída inferior al 3% (Recomendación CEN).</div>', unsafe_allow_html=True)
    elif percent_drop <= 5.0:
         st.markdown(f'<div class="warning-box">⚠️ <b>ATENCIÓN:</b> Caída superior a 3%. Cumple para sistemas complejos (<5%), pero verificar.</div>', unsafe_allow_html=True)
    else:
         st.markdown(f'<div class="fail-box">❌ <b>NO CUMPLE:</b> Excede el 5%. Aumenta calibre.</div>', unsafe_allow_html=True)

# --- MÓDULO 3: CANALIZACIONES ---
with tab3:
    st.markdown('<p class="header-style">Dimensionamiento por Material y Recomendación (CEN Cap. 9)</p>', unsafe_allow_html=True)
    c_t1, c_t2 = st.columns(2)
    with c_t1:
        material_sel = st.selectbox("Material de Tubería", ["PVC40", "EMT", "ARG"], key="mat_sel")
        st.caption("Límite de Ocupación: 40% (CEN, Cap. 9, Tabla 1)")
        
    with c_t2:
        calibre_t = st.selectbox("Calibre Conductores", list(db_cables.keys()), index=1, key="t_cal")
        n_hilos = st.number_input("Total Hilos (Fases+Neutro+Tierra)", 1, 30, 4, key="n_hilos")

    # Cálculos de Ocupación
    area_uni = db_cables[calibre_t]["area"]
    area_ocup = n_hilos * area_uni
    limite = 53 if n_hilos == 1 else (31 if n_hilos == 2 else 40)
    
    # BÚSQUEDA DEL TUBO MÍNIMO
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
    
    st.subheader("Verificar Diámetro Seleccionado")
    tubo_a_verificar = st.selectbox("Selecciona Diámetro para verificar", list(db_tuberias.keys()), index=1, key="tubo_verif")
    
    area_tubo_verif = db_tuberias[tubo_a_verificar][material_sel]
    porc_verif = (area_ocup / area_tubo_verif) * 100
    
    st.write(f"Área Interna del {tubo_a_verificar}: **{area_tubo_verif:.2f} mm²**")

    if porc_verif <= limite:
        st.markdown(f'<div class="success-box">✅ <b>APROBADO:</b> Ocupación {porc_verif:.2f}% (Máx {limite}%).</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="fail-box">❌ <b>SATURADO:</b> Ocupación {porc_verif:.2f}% (Máx {limite}%).</div>', unsafe_allow_html=True)
        
    tubo_sel = tubo_a_verificar
    porcentaje = porc_verif

# --- MÓDULO 4: CORTOCIRCUITO (NUEVO) ---
with tab4:
    st.markdown('<p class="header-style">Dimensionamiento por Cortocircuito (IEEE 242)</p>', unsafe_allow_html=True)
    
    # Constante térmica K (TC) para Cobre THW (75C a 150C)
    K_CONST = 105.0 
    
    c_cc1, c_cc2 = st.columns(2)
    with c_cc1:
        i_falla = st.number_input("Corriente de Falla (Icc, Amps)", value=10000.0, step=500.0, key="i_falla", help="Valor de cortocircuito simétrico.")
        tiempo_despeje = st.number_input("Tiempo de Despeje del Breaker (t, segundos)", value=0.5, step=0.01, key="t_despeje", help="Tiempo de operación del interruptor de protección.")
    
    with c_cc2:
        calibre_cc = st.selectbox("Calibre a Verificar", list(db_cables.keys()), index=1, key="cc_cal")
        
        st.info("Parámetros del Conductor (Cobre 75°C):")
        st.write(f"🔹 Constante Térmica (K): **{K_CONST}**")
        area_real_kcmil = db_cables[calibre_cc]['kcmil']
        st.write(f"🔹 Área Real ({calibre_cc}): **{area_real_kcmil:.2f} kcmil**")


    # Cálculo de Cortocircuito
    if i_falla > 0 and tiempo_despeje > 0:
        area_kcmil_min = i_falla * np.sqrt(tiempo_despeje) / K_CONST
        
        # Búsqueda del calibre mínimo que satisface A_min
        calibre_min_cc = "N/A"
        for cal, data in db_cables.items():
            if data['kcmil'] >= area_kcmil_min:
                calibre_min_cc = cal
                break
    else:
        area_kcmil_min = 0

    st.markdown("---")
    m_cc1, m_cc2 = st.columns(2)
    m_cc1.metric("Área Mínima Requerida (kcmil)", f"{area_kcmil_min:.2f} kcmil")
    m_cc2.metric("Calibre Mínimo Requerido", calibre_min_cc)


    st.subheader("Evaluación del Calibre Seleccionado:")
    if area_real_kcmil >= area_kcmil_min:
        st.markdown(f'<div class="success-box">✅ <b>APROBADO:</b> El calibre {calibre_cc} ({area_real_kcmil:.2f} kcmil) es seguro ante la falla térmica.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="fail-box">❌ <b>FALLA TÉRMICA:</b> El calibre {calibre_cc} es menor al área mínima requerida. Selecciona {calibre_min_cc} o mayor.</div>', unsafe_allow_html=True)


# --- 5. GENERADOR PDF (Actualizado para incluir Cortocircuito) ---
def create_pdf(carga, vol, cal, amp, i_dis, v_dp, v_pct, tub, porc_tub, tubo_rec, cc_req, cc_cal_min):
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
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10, "RESUMEN DE RESULTADOS:", ln=True)
    pdf.set_font("Arial", size=10)
    
    res_amp = "CUMPLE" if amp >= i_dis else "FALLA"
    pdf.cell(0, 7, f"1. Ampacidad: {amp:.2f} A (Req: {i_dis:.2f} A) -> {res_amp}", ln=True)
    
    res_v = "CUMPLE" if v_pct <= 3 else "FALLA"
    pdf.cell(0, 7, f"2. Caida Tension: {v_dp:.2f} V ({v_pct:.2f}%) -> {res_v}", ln=True)
    
    res_t = "CUMPLE" if porc_tub <= 40 else "FALLA"
    pdf.cell(0, 7, f"3. Tuberia ({tub}): Ocupacion {porc_tub:.2f}% (MINIMO REQ: {tubo_rec}) -> {res_t}", ln=True)
    
    res_cc = "CUMPLE" if db_cables[cal].get('kcmil', 0) >= cc_req else "FALLA"
    pdf.cell(0, 7, f"4. Cortocircuito: Area Req {cc_req:.2f} kcmil (MINIMO {cc_cal_min}) -> {res_cc}", ln=True)

    return pdf.output(dest='S').encode('latin-1')

# --- BARRA LATERAL (DESCARGA) ---
st.sidebar.markdown("---")
st.sidebar.header("📄 Reportes")

if 'amp_real' in locals():
    pdf_bytes = create_pdf(
        carga_va, voltaje, calibre_sel, amp_real, i_diseno, 
        v_drop, percent_drop, tubo_sel, porcentaje, tubo_recomendado, 
        area_kcmil_min, calibre_min_cc
    )
    st.sidebar.download_button("📥 Descargar Memoria PDF", pdf_bytes, "protocolo_dimensionamiento_cen.pdf", "application/pdf")
