# ===================== 1. IMPORTACIONES NECESARIAS ============================
import streamlit as st              # Librería para crear la interfaz web
#import google.generativeai as genai # Cliente para usar Gemini (Google Generative AI)
import google.genai as genai   #inetntando 
import gspread                      # Cliente para manipular Google Sheets
from oauth2client.service_account import ServiceAccountCredentials # Manejo de credenciales
import pandas as pd                 # Manejo de datos en formato tabla
import io                           # Para manejar strings como archivos
import json                         # Para leer credenciales en formato JSON

# ===================== 2. CONFIGURACIÓN INICIAL ===============================
# La API Key ya no se pone en el código, se guarda en st.secrets["gemini_api_key"]
# Leer la API Key desde secrets
GEMINI_API_KEY = st.secrets["gemini_api_key"]
# Configurar Gemini

# ID del Google Sheet (este lo cambias por el de Carolina)
ID_EXCEL = "1XbQDQCIhT4rE3kJypoll61sICjuoH-xmfgOUs2lmq-k"

# Inicializar la IA de Google con la API Key
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")  # rápido y eficiente

#model = genai.GenerativeModel("gemini-1.5-pro")    # más potente
st.write("Gemini listo para trabajar")

# ===================== 3. FUNCIÓN DEL AGENTE IA ===============================
def agente_ia(texto_sucio):
    """
    Envía el texto de WhatsApp a la IA para que lo devuelva como tabla CSV.
    """
    prompt = f"""
    Actúa como un experto en bodega. Analiza el siguiente inventario: {texto_sucio}
    INSTRUCCIONES:
    1. Extrae: Producto, Cantidad (solo número), Unidad y Observación.
    2. Usa nombres estándar (ej: Acelga, Aguacate, Ají).
    3. Si hay sumas (ej: 10kg + 5kg), pon el total (15).
    4. Responde ÚNICAMENTE con formato CSV usando ';' como separador.
    
    Columnas: Producto;Cantidad;Unidad;Observacion
    """
    # Generamos la respuesta con Gemini
    response = model.generate_content(prompt)
    return response.text

# ===================== 4. INTERFAZ WEB (Streamlit) ============================
st.set_page_config(page_title="Inventario Guada", page_icon="🍎") # Configuración de la página
st.title("🍎 Actualizador de Inventario Automático")              # Título principal
st.markdown("Copia el mensaje de Pedro y presiona el botón para actualizar el Excel.")

# Área de texto para pegar el mensaje de WhatsApp
texto_pedro = st.text_area("Mensaje de WhatsApp:", height=250, placeholder="Pega aquí el texto de Pedro...")

# ===================== 5. BOTÓN DE EJECUCIÓN =================================
if st.button("🚀 Actualizar Google Sheet"):
    if texto_pedro:  # Verifica que haya texto
        try:
            # --- 5.1 CONEXIÓN SEGURA A GOOGLE SHEETS ---
            # Leemos credenciales desde st.secrets
            creds_info = json.loads(st.secrets["gcp_service_account"])
            
            # Scopes correctos para acceder a Google Sheets y Drive
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Autorizamos el cliente con las credenciales
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
            client = gspread.authorize(creds)
            
            # Abrimos el documento por su ID
            sheet = client.open_by_key(ID_EXCEL).sheet1
            
            with st.spinner("La IA está procesando los datos..."):
                # --- 5.2 PROCESAMIENTO DE TEXTO CON IA ---
                raw_csv = agente_ia(texto_pedro).replace('```csv', '').replace('```', '').strip()
                
                # Validamos que el CSV tenga las columnas esperadas
                try:
                    df_nuevo = pd.read_csv(io.StringIO(raw_csv), sep=';')
                    columnas_esperadas = {"Producto", "Cantidad", "Unidad", "Observacion"}
                    if not columnas_esperadas.issubset(df_nuevo.columns):
                        raise ValueError("El CSV no tiene las columnas correctas.")
                except Exception as e:
                    st.error(f"Error al procesar el CSV: {e}")
                    st.stop()
                
                # --- 5.3 ACTUALIZACIÓN DE FILAS EN GOOGLE SHEET ---
                for _, fila in df_nuevo.iterrows():
                    nombre_prod = str(fila['Producto']).strip()
                    try:
                        # Buscamos si el producto ya existe en la Columna A
                        celda = sheet.find(nombre_prod)
                        
                        # Si lo encuentra, actualiza la fila
                        sheet.update_cell(celda.row, 2, str(fila['Cantidad']))
                        sheet.update_cell(celda.row, 3, str(fila['Unidad']))
                        sheet.update_cell(celda.row, 4, str(fila['Observacion']))
                    
                    except gspread.exceptions.CellNotFound:
                        # Si no existe, lo añade al final
                        sheet.append_row([nombre_prod, str(fila['Cantidad']), str(fila['Unidad']), str(fila['Observacion'])])
                
                # --- 5.4 FEEDBACK AL USUARIO ---
                st.success("¡Inventario actualizado correctamente!")
                st.table(df_nuevo)  # Muestra resumen en pantalla
                
        except Exception as e:
            st.error(f"Error técnico: {e}")
    else:
        st.warning("Primero debes pegar el texto de Pedro.")


