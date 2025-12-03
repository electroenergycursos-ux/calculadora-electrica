import streamlit as st
import numpy as np
import pandas as pd
from fpdf import FPDF
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cálculo Eléctrico - Caseta Vigilancia", layout="wide", page_icon="⚡")

st.markdown("""
<style>
    .header-style { font-size:20px; font-weight:bold; color: #004E8C; }
    .success-box { padding: 15px; border-radius: 8px; background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
    .warning-box { padding: 15px; border-radius: 8px; background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; }
    .fail-box { padding: 15px; border-radius: 8px; background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Suite de Ingeniería Eléctrica (Norma PDVSA/CEN)")
st.caption("Basado en Memoria de Cálculo: Caseta de Control de Acceso - Planta Furrial")

# --- BASE DE DATOS (Diccionario Python) ---
db_cables = {
    "14 AWG":      {"area": 2.08,  "diam": 2.80, "R": 10.17, "X": 0.190, "amp": 20},
    "12 AWG":      {"area": 3.31,  "diam": 3.86, "R": 6.56,  "X": 0.177, "amp": 25},
    "10 AWG":      {"area": 5.26,  "diam": 4.50, "R": 3.94,  "X": 0.164, "amp": 35},
    "8 AWG":       {"area": 8.37,  "diam": 5.80, "R": 2.56,  "X": 0.171, "amp": 50},
    "6 AWG":       {"area": 13.3,  "diam": 6.80, "R": 1.61,  "X": 0.167, "amp": 65},
    "4 AWG":       {"area": 21.2,  "diam": 8.40, "R": 1.02,  "X": 0.157, "amp": 85},
    "2 AWG":       {"area": 33.6,  "diam": 10.5, "R": 0.62,  "X": 0.148, "amp": 115},
    "1/0 AWG":     {"area": 53.5,  "diam": 13.0, "R": 0.39,  "X": 0.144, "amp": 150},
    "2/0 AWG":     {"area": 67.4,  "diam": 14.4, "R": 0.31,  "X": 0.141, "amp": 175},
    "4/0 AWG":     {"area": 107.2, "diam": 17.8, "R": 0.219, "X": 0.135, "amp": 230},
}

db_breakers = [15, 20, 25, 30, 40, 50, 60, 70, 100, 125, 150, 175, 200, 225, 250]

db_tuberias = {
    "1/2\"": 196, "3/4\"": 327, "1\"": 568, 
    "1 1/4\"": 986, "1 1/2\"": 1338, "2\"": 2186, "3\"": 4814
}

# --- PESTAÑAS ---
tab1, tab2, tab3 = st.tabs(["🛡️ 1. Ampacidad y Protección", "📉 2. Caída de Tensión", "pipe 3. Canalizaciones"])

# MÓDULO 1
with tab1:
    st.markdown('<p class="header-style">Selección por Capacidad de Corriente (CEN 310.16)</p>', unsafe_allow_html=True)
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        carga_va = st.number_input("Carga Total (VA)", value=1260.0, step=100.0)
        voltaje = st.selectbox("Tensión de Servicio", [120, 208, 480], index=0)
        sistema = st.selectbox("Sistema", ["Monofásico (1F)", "Trifásico (3F)"])
        tipo_carga = st.radio("Tipo de Carga", ["Iluminación (FP 0.95)", "Tomacorrientes (FP 0.90)"], index=1)
        
    with col_in2:
        st.info("Condiciones Ambientales (Memoria de Cálculo):")
        temp_amb = st.number_input("Temp. Ambiente (°C)", value=40, disabled=True)
        fc_temp = 0.88 
        st.write(f"🔹 Factor Corrección Temp: **{fc_temp}**")
        calibre_sel = st.selectbox("Calibre a Evaluar", list(db_cables.keys()), index=1)
        num_conductores = st.number_input("N° Conductores Activos en ducto", value=3)

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

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("Corriente Carga (Ib)", f"{corriente_carga:.2f} A")
    c2.metric("Corriente Diseño (125%)", f"{i_diseno:.2f} A")
    c3.metric(f"Capacidad Cable {calibre_sel}", f"{amp_real:.2f} A", delta=f"Derating: {fc_temp*fc_agrup:.2f}")

    if amp_real >= i_diseno:
        st.markdown(f'<div class="success-box">✅ <b>APROBADO:</b> El conductor <b>{calibre_sel}</b> soporta la carga (Capacidad {amp_real:.1f}A vs Requerido {i_diseno:.1f}A).</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="fail-box">❌ <b>INSUFICIENTE:</b> El conductor {calibre_sel} se sobrecalentará. Aumenta el calibre.</div>', unsafe_allow_html=True)

    st.write("---")
    st.write(f"**Protección Recomendada:** Breaker de **{breaker_ideal} A**")
    if breaker_ideal > amp_real:
        st.markdown(f'<div class="warning-box">⚠️ <b>ATENCIÓN:</b> El breaker ({breaker_ideal}A) es mayor que la capacidad del cable corregida ({amp_real:.1f}A). Verifica coordinación.</div>', unsafe_allow_html=True)

# MÓDULO 2
with tab2:
    st.markdown('<p class="header-style">Cálculo de Regulación (Fórmula Exacta)</p>', unsafe_allow_html=True)
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        distancia = st.number_input("Longitud (metros)", value=20.0)
        corriente_calc = st.number_input("Corriente (A)", value=corriente_carga) 
        calibre_v = st.selectbox("Calibre", list(db_cables.keys()), index=1, key="v_cal")
    
    with col_v2:
        fp_v = st.slider("Factor Potencia", 0.8, 1.0, fp)
        voltaje_base = st.number_input("Voltaje Base", value=voltaje)
        fases_v = st.radio("Fases", ["1F (K=2)", "3F (K=1.732)"], index=0 if "Monofásico" in sistema else 1)

    datos = db_cables[calibre_v]
    R = datos["R"]
    X = datos["X"]
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
         st.markdown(f'<div class="success-box">✅ <b>CUMPLE:</b> Caída inferior al 3% permitido.</div>', unsafe_allow_html=True)
    else:
         st.markdown(f'<div class="fail-box">❌ <b>NO CUMPLE:</b> Excede el 3%. Aumenta calibre o reduce distancia.</div>', unsafe_allow_html=True)

# MÓDULO 3
with tab3:
    st.markdown('<p class="header-style">Ocupación de Tubería (Fill %)</p>', unsafe_allow_html=True)
    c_t1, c_t2 = st.columns(2)
    with c_t1:
        tubo_sel = st.selectbox("Diámetro Tubería (PVC/EMT)", list(db_tuberias.keys()), index=1)
        area_tubo = db_tuberias[tubo_sel]
        st.write(f"Área Disponible (100%): **{area_tubo} mm²**")
        
    with c_t2:
        calibre_t = st.selectbox("Calibre Conductores", list(db_cables.keys()), index=1, key="t_cal")
        n_fases = st.number_input("N° Fases", 1, 10, 2)
        n_neutro = st.number_input("N° Neutros", 0, 5, 1)
        n_tierra = st.number_input("N° Tierras", 0, 5, 1)

    total_hilos = n_fases + n_neutro + n_tierra
    area_unitaria = db_cables[calibre_t]["area"]
    area_ocupada = total_hilos * area_unitaria
    porcentaje = (area_ocupada / area_tubo) * 100
    limite = 53 if total_hilos == 1 else (31 if total_hilos == 2 else 40)
    
    st.markdown("---")
    st.progress(min(porcentaje/100, 1.0))
    st.write(f"**Ocupación: {porcentaje:.2f}%** (Límite permitido: {limite}%)")
    
    if porcentaje <= limite:
        st.success("✅ INSTALACIÓN PERMITIDA")
    else:
        st.error("❌ TUBERÍA SATURADA. Elige un diámetro mayor.")

# GENERADOR PDF
def create_pdf(carga, voltaje, calibre, amp_real, i_diseno, v_drop, v_percent, tubo, ocupacion_percent, limite_ocupacion):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'MEMORIA DE CALCULO ELECTRICO', 0, 1, 'C')
            self.set_font('Arial', '', 10)
            self.cell(0, 10, 'Proyecto: Caseta de Vigilancia / Planta Furrial', 0, 1, 'C')
            self.line(10, 30, 200, 30)
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="1. Parametros de Diseno", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 7, txt=f"- Carga Instalada: {carga} VA", ln=True)
    pdf.cell(200, 7, txt=f"- Tension de Servicio: {voltaje} V", ln=True)
    pdf.cell(200, 7, txt=f"- Conductor Seleccionado: {calibre}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="2. Capacidad de Corriente (CEN 310.16)", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 7, txt=f"- Ampacidad Corregida: {amp_real:.2f} A", ln=True)
    pdf.cell(200, 7, txt=f"- Corriente de Diseno: {i_diseno:.2f} A", ln=True)
    estado_amp = "CUMPLE" if amp_real >= i_diseno else "NO CUMPLE"
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(200, 7, txt=f"Resultado: {estado_amp}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="3. Regulacion de Tension", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 7, txt=f"- Caida Calculada: {v_drop:.2f} V ({v_percent:.2f} %)", ln=True)
    estado_v = "CUMPLE" if v_percent <= 3.0 else "NO CUMPLE"
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(200, 7, txt=f"Resultado: {estado_v}", ln=True)
    pdf.ln(5)

    return pdf.output(dest='S').encode('latin-1')

st.sidebar.markdown("---")
st.sidebar.header("📄 Reportes")

if 'amp_real' in locals():
    pdf_bytes = create_pdf(carga_va, voltaje, calibre_sel, amp_real, i_diseno, v_drop, percent_drop, tubo_sel, porcentaje, limite)
    st.sidebar.download_button(
        label="📥 Descargar Memoria PDF",
        data=pdf_bytes,
        file_name="memoria_calculo.pdf",
        mime="application/pdf"
    )
