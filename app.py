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
#for m in client.models.list():
 #   st.write(m.name)




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
mensaje = st.text_area("Pega aquí lod datos:")

if st.button("Procesar mensaje"):
    if mensaje.strip() == "":
        st.warning("Primero debes pegar el texto con los datos correctos...")
    else:
        try:
            # USAR GEMINI PARA PROCESAR EL MENSAJE
            # CAMBIO: SE USA client.models.generate_content EN VEZ DE model.generate_content
            response = client.models.generate_content(
            model="models/gemini-2.5-flash",   # usa uno de los que viste en la lista
            contents=f"""
                        Extrae producto, cantidad y unidad de este inventario:
                        {mensaje}
                        Devuélvelo en formato JSON como una lista de objetos, cada uno con claves:
                        producto, cantidad, unidad.
                        """)  

            # MOSTRAR RESPUESTA DE GEMINI
            st.write("Respuesta de Gemini:")
            st.write(response.text)

            # EJEMPLO DE ACTUALIZACIÓN EN GOOGLE SHEETS
            # (Aquí deberías parsear la respuesta y actualizar filas/columnas según tu lógica)
           # sheet.update_cell(1, 1, "Inventario actualizado correctamente")  # DEMO
            # MOSTRAR RESPUESTA DE GEMINI
            st.write("Respuesta de Gemini:")
            st.write(response.text)
            try:
                datos = json.loads(response.text)
                for item in datos:
                    producto = item["producto"]
                    cantidad = item["cantidad"]
                    unidad = item["unidad"]
            
            # ACTUALIZACIÓN EN GOOGLE SHEETS
         #=================AQUI ESTA LA CLAVE DEL PROGRAMA ==================================
         #===================================================================================
            # Procesar cada línea del mensaje ingresado

            
                    # Buscar fila por producto en la hoja
                    try:
                        cell = sheet.find(producto)
                        fila = cell.row
                        sheet.update_cell(fila, 3, cantidad)             # Columna Cantidad
                        sheet.update_cell(fila, 4, unidad)               # Columna Unidad
                        sheet.update_cell(fila, 5, "Sin observación")    # Columna Observación
                    except:
                        st.write(f"⚠️ Producto {producto} no encontrado en la hoja.")

         

            st.success("Inventario actualizado correctamente ✅")
  #=============================================================================================
        except Exception as e:
            st.error(f"Ocurrió un error: {e}")
