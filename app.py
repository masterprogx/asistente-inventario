import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import io
import json

# ------------------- 1. CONFIGURACIÓN INICIAL ----------------------------
#===========================================================================
GEMINI_API_KEY = "AIzaSyCVWNZQnZqSi_jlzmSJjSpUAQ7cQnttWDY" 
# ID del Google Sheet de prueba (luego lo cambias por el de Carolina)
ID_EXCEL = "1XbQDQCIhT4rE3kJypoll61sICjuoH-xmfgOUs2lmq-k"

# Inicializar la Inteligencia Artificial de Google
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ---------------------- 2. FUNCIÓN DEL AGENTE IA --------------------------------
#=================================================================================
def agente_ia(texto_sucio):
    """Envía el texto de WhatsApp a la IA para que lo devuelva como tabla CSV."""
    prompt = f"""
    Actúa como un experto en bodega. Analiza el siguiente inventario: {texto_sucio}
    INSTRUCCIONES:
    1. Extrae: Producto, Cantidad (solo número), Unidad y Observación.
    2. Usa nombres estándar (ej: Acelga, Aguacate, Ají).
    3. Si hay sumas (ej: 10kg + 5kg), pon el total (15).
    4. Responde ÚNICAMENTE con formato CSV usando ';' como separador.
    
    Columnas: Producto;Cantidad;Unidad;Observacion
    """
    response = model.generate_content(prompt)
    return response.text

# ----------- 3. INTERFAZ WEB (Streamlit) --------------------------------
#=========================================================================
st.set_page_config(page_title="Inventario Guada", page_icon="🍎")
st.title("🍎 Actualizador de Inventario Automático")
st.markdown("Copia el mensaje de Pedro y presiona el botón para actualizar el Excel.")

# Área de texto para que Carolina pegue el mensaje
texto_pedro = st.text_area("Mensaje de WhatsApp:", height=250, placeholder="Pega aquí el texto de Pedro...")

if st.button("🚀 Actualizar Google Sheet"):
    if texto_pedro:
        try:
            # --- 4. CONEXIÓN SEGURA A GOOGLE SHEETS ---
            # Leemos las credenciales desde los 'Secrets' de Streamlit para que sea automático
            creds_info = json.loads(st.secrets["gcp_service_account"])
            scope = [ "https://spreadsheets.google.com/feeds",  "https://www.googleapis.com/auth/drive"] #URLS CORTAS
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
            client = gspread.authorize(creds)
            
            # Abrir el documento por su ID
            sheet = client.open_by_key(ID_EXCEL).sheet1
            
            with st.spinner("La IA está procesando los datos..."):
                # Llamar a la IA y limpiar el resultado
                raw_csv = agente_ia(texto_pedro).replace('```csv', '').replace('```', '').strip()
                df_nuevo = pd.read_csv(io.StringIO(raw_csv), sep=';')
                
                # --- 5. ACTUALIZACIÓN DE FILAS ---
                for _, fila in df_nuevo.iterrows():
                    nombre_prod = str(fila['Producto']).strip()
                    try:
                        # Buscamos si el producto ya existe en la Columna A del Excel
                        celda = sheet.find(nombre_prod)
                        
                        # Si lo encuentra, actualiza las celdas de esa fila:
                        # Columna B (2): Cantidad | Columna C (3): Unidad | Columna D (4): Observacion
                        sheet.update_cell(celda.row, 2, str(fila['Cantidad']))
                        sheet.update_cell(celda.row, 3, str(fila['Unidad']))
                        sheet.update_cell(celda.row, 4, str(fila['Observacion']))
                    
                    except gspread.exceptions.CellNotFound:
                        # Si el producto NO está en la lista fija, lo añade al final
                        sheet.append_row([nombre_prod, str(fila['Cantidad']), str(fila['Unidad']), str(fila['Observacion'])])
                
                st.success("¡Inventario actualizado correctamente!")
                st.table(df_nuevo) # Muestra resumen en pantalla
                
        except Exception as e:
            st.error(f"Error técnico: {e}")
    else:
        st.warning("Primero debes pegar el texto de Pedro.")

