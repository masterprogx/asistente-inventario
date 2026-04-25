import streamlit as st
import google.genai as genai   # CAMBIO: ANTES ERA google.generativeai, AHORA ES google.genai

import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# LEER LA API KEY DESDE SECRETS
# CAMBIO: YA NO SE USA genai.configure(), AHORA SE CREA UN CLIENTE DIRECTO
api_key = st.secrets["gemini_api_key"]
client = genai.Client(api_key=api_key)   # CAMBIO: SE CREA EL CLIENTE CON LA API KEY

#OBSERVACIONES

# DEBUG: listar modelos disponibles
for m in client.models.list():
    st.write(m.name)




# LEER EL SERVICE ACCOUNT DESDE SECRETS
# IMPORTANTE: EN SECRETS DE STREAMLIT DEBE ESTAR gcp_service_account CON EL JSON ENTRE """ """
creds_info = json.loads(st.secrets["gcp_service_account"])

# CONFIGURAR AUTORIZACIÓN PARA GOOGLE SHEETS
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
client_gsheets = gspread.authorize(creds)

# ABRIR TU HOJA DE INVENTARIO (REEMPLAZA CON TU ID DE SHEET)
sheet = client_gsheets.open_by_key("1XbQDQCIhT4rE3kJypoll61sICjuoH-xmfgOUs2lmq-k").sheet1


# INTERFAZ STREAMLIT
st.title("Asistente de Inventario con Gemini")

# CAMPO DE TEXTO PARA PEGAR EL MENSAJE DE PEDRO
mensaje = st.text_area("Pega aquí el mensaje de Pedro:")

if st.button("Procesar mensaje"):
    if mensaje.strip() == "":
        st.warning("Primero debes pegar el texto de Pedro...")
    else:
        try:
            # USAR GEMINI PARA PROCESAR EL MENSAJE
            # CAMBIO: SE USA client.models.generate_content EN VEZ DE model.generate_content
            response = client.models.generate_content(
                model="gemini-1.5-flash",   # CAMBIO: MODELOS NUEVOS DISPONIBLES
                contents=mensaje
            )

            # MOSTRAR RESPUESTA DE GEMINI
            st.write("Respuesta de Gemini:")
            st.write(response.text)

            # EJEMPLO DE ACTUALIZACIÓN EN GOOGLE SHEETS
            # (Aquí deberías parsear la respuesta y actualizar filas/columnas según tu lógica)
            sheet.update_cell(1, 1, "Inventario actualizado correctamente")  # DEMO

            st.success("Inventario actualizado correctamente")

        except Exception as e:
            st.error(f"Ocurrió un error: {e}")
