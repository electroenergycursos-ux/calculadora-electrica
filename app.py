# ... (Todo tu código anterior de las Tabs y Cálculos sigue igual arriba) ...

# =========================================================
# MÓDULO 4: GENERACIÓN DE REPORTE PDF
# =========================================================
from fpdf import FPDF
import base64

def create_pdf(carga, voltaje, calibre, amp_real, i_diseno, v_drop, v_percent, tubo, ocupacion_percent, limite_ocupacion):
    class PDF(FPDF):
        def header(self):
            # Encabezado estilo Ingeniería
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

    # 1. Resumen de Entradas
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="1. Parametros de Diseno", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 7, txt=f"- Carga Instalada: {carga} VA", ln=True)
    pdf.cell(200, 7, txt=f"- Tension de Servicio: {voltaje} V", ln=True)
    pdf.cell(200, 7, txt=f"- Conductor Seleccionado: {calibre} (THW/THHN)", ln=True)
    pdf.ln(5)

    # 2. Resultados de Ampacidad
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="2. Capacidad de Corriente (CEN 310.16)", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 7, txt=f"- Ampacidad Corregida del Cable: {amp_real:.2f} A", ln=True)
    pdf.cell(200, 7, txt=f"- Corriente de Diseno (125%): {i_diseno:.2f} A", ln=True)
    
    estado_amp = "CUMPLE" if amp_real >= i_diseno else "NO CUMPLE (RIESGO)"
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(200, 7, txt=f"Resultado: {estado_amp}", ln=True)
    pdf.ln(5)

    # 3. Caída de Tensión
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="3. Regulacion de Tension", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 7, txt=f"- Caida Calculada: {v_drop:.2f} V", ln=True)
    pdf.cell(200, 7, txt=f"- Porcentaje: {v_percent:.2f} %", ln=True)
    
    estado_v = "CUMPLE (<3%)" if v_percent <= 3.0 else "NO CUMPLE (>3%)"
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(200, 7, txt=f"Resultado: {estado_v}", ln=True)
    pdf.ln(5)

    # 4. Canalizaciones
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="4. Ocupacion de Tuberia (Fill)", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 7, txt=f"- Diametro Tuberia: {tubo}", ln=True)
    pdf.cell(200, 7, txt=f"- Ocupacion Real: {ocupacion_percent:.2f} %", ln=True)
    pdf.cell(200, 7, txt=f"- Limite NEC/CEN: {limite_ocupacion} %", ln=True)
    
    estado_tubo = "CUMPLE" if ocupacion_percent <= limite_ocupacion else "SATURADO"
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(200, 7, txt=f"Resultado: {estado_tubo}", ln=True)

    # Retornar el PDF como string binario
    return pdf.output(dest='S').encode('latin-1')

# --- BOTÓN DE DESCARGA EN LA BARRA LATERAL ---
st.sidebar.markdown("---")
st.sidebar.header("📄 Reportes")

# Verificamos que las variables existan (por si el usuario acaba de abrir la app)
if 'amp_real' in locals() and 'v_percent' in locals() and 'porcentaje' in locals():
    pdf_bytes = create_pdf(
        carga_va, voltaje, calibre_sel, 
        amp_real, i_diseno, 
        v_drop, percent_drop, 
        tubo_sel, porcentaje, limite
    )
    
    st.sidebar.download_button(
        label="📥 Descargar Memoria de Cálculo (PDF)",
        data=pdf_bytes,
        file_name="memoria_calculo_electrico.pdf",
        mime="application/pdf"
    )
else:
    st.sidebar.info("Realiza un cálculo primero para generar el PDF.")
