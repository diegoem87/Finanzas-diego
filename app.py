import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Control Financiero Personal", page_icon="💰", layout="wide")

# --- FUNCION PARA OBTENER EL DÓLAR BLUE ---
@st.cache_data(ttl=3600)  # Guarda en caché por 1 hora para no saturar la API
def obtener_dolar_blue():
    try:
        response = requests.get("https://dolarapi.com/v1/dolares/blue")
        if response.status_code == 200:
            data = response.json()
            return data.get("venta", 1000) # Devuelve el valor de venta, o 1000 por defecto si falla
    except:
        pass
    return 1000.0 # Valor estimativo de respaldo si hay error de red

VALOR_DOLAR_BLUE = obtener_dolar_blue()

# --- AUTENTICACIÓN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

def login():
    st.title("🔐 Iniciar Sesión")
    usuario = st.text_input("Usuario")
    contrasena = st.text_input("Contraseña", type="password")
    
    if st.button("Ingresar"):
        if usuario == "diego" and contrasena == "diegoem87":
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")

if not st.session_state.autenticado:
    login()
else:
    # --- INICIALIZAR ESTADOS DE DATOS ---
    # Ingresos
    if "ingresos" not in st.session_state:
        st.session_state.ingresos = pd.DataFrame(columns=["Item", "Valor (ARS)"])
    
    # Costos
    if "costos" not in st.session_state:
        st.session_state.costos = pd.DataFrame(columns=["Item", "Valor (ARS)"])
        
    # Inversiones
    categorias_inversiones = ["Dólares", "Criptoactivos", "Plazo Fijo", "Billeteras Virtuales", "Bonos y Acciones", "Inmuebles"]
    if "inversiones" not in st.session_state:
        st.session_state.inversiones = pd.DataFrame(columns=["Categoría", "Detalle / Activo", "Valor Actual (ARS)"])

    # --- BARRA LATERAL (NAVEGACIÓN Y TIPO DE CAMBIO) ---
    st.sidebar.title(f"👋 Hola, Diego")
    st.sidebar.markdown(f"💵 **Dólar Blue Actual:** \\${VALOR_DOLAR_BLUE:,.2f}")
    
    menu = st.sidebar.radio("Navegación", ["📊 Ingresos y Costos", "📈 Cartera de Inversiones"])
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

    # ==========================================
    # SECCIÓN 1: INGRESOS Y COSTOS
    # ==========================================
    if menu == "📊 Ingresos y Costos":
        st.title("📊 Control de Ingresos y Costos de Vida")
        st.write(f"Los valores en dólares se calculan automáticamente a una cotización de \\${VALOR_DOLAR_BLUE:,.2f} por dólar blue.")
        
        col1, col2 = st.columns(2)
        
        # --- CARGA DE INGRESOS ---
        with col1:
            st.subheader("➕ Cargar Ingresos")
            with st.form("form_ingreso", clear_on_submit=True):
                item_ingreso = st.text_input("Nombre del Ingreso (Ej: Sueldo, Freelance)")
                valor_ingreso = st.number_input("Valor en Pesos (ARS)", min_value=0.0, format="%.2f")
                submit_ingreso = st.form_submit_button("Agregar Ingreso")
                
                if submit_ingreso and item_ingreso:
                    nuevo_df = pd.DataFrame({"Item": [item_ingreso], "Valor (ARS)": [valor_ingreso]})
                    st.session_state.ingresos = pd.concat([st.session_state.ingresos, nuevo_df], ignore_index=True)
                    st.success(f"Ingreso '{item_ingreso}' agregado.")
                    st.rerun()

            st.write("**Lista de Ingresos:**")
            if not st.session_state.ingresos.empty:
                df_ing_display = st.session_state.ingresos.copy()
                df_ing_display["Valor (USD)"] = df_ing_display["Valor (ARS)"] / VALOR_DOLAR_BLUE
                st.dataframe(df_ing_display, use_container_width=True)
                if st.button("Borrar último ingreso"):
                    st.session_state.ingresos = st.session_state.ingresos.iloc[:-1]
                    st.rerun()
            else:
                st.info("No hay ingresos cargados.")

        # --- CARGA DE COSTOS ---
        with col2:
            st.subheader("➖ Cargar Costos de Vida")
            with st.form("form_costo", clear_on_submit=True):
                item_costo = st.text_input("Nombre del Costo (Ej: Alquiler, Comida)")
                valor_costo = st.number_input("Valor en Pesos (ARS)", min_value=0.0, format="%.2f", key="val_costo")
                submit_costo = st.form_submit_button("Agregar Costo")
                
                if submit_costo and item_costo:
                    nuevo_df = pd.DataFrame({"Item": [item_costo], "Valor (ARS)": [valor_costo]})
                    st.session_state.costos = pd.concat([st.session_state.costos, nuevo_df], ignore_index=True)
                    st.success(f"Costo '{item_costo}' agregado.")
                    st.rerun()

            st.write("**Lista de Costos:**")
            if not st.session_state.costos.empty:
                df_cos_display = st.session_state.costos.copy()
                df_cos_display["Valor (USD)"] = df_cos_display["Valor (ARS)"] / VALOR_DOLAR_BLUE
                st.dataframe(df_cos_display, use_container_width=True)
                if st.button("Borrar último costo"):
                    st.session_state.costos = st.session_state.costos.iloc[:-1]
                    st.rerun()
            else:
                st.info("No hay costos cargados.")

        st.markdown("---")
        
        # --- BALANCE, AHORRO Y GRÁFICAS ---
        st.subheader("💡 Balance y Análisis Mensual")
        
        total_ingresos = st.session_state.ingresos["Valor (ARS)"].sum() if not st.session_state.ingresos.empty else 0.0
        total_costos = st.session_state.costos["Valor (ARS)"].sum() if not st.session_state.costos.empty else 0.0
        balance = total_ingresos - total_costos
        
        # Métricas principales
        mcol1, mcol2, mcol3 = st.columns(3)
        mcol1.metric("Total Ingresos", f"ARS \\${total_ingresos:,.2f}", f"USD \\${total_ingresos/VALOR_DOLAR_BLUE:,.2f}")
        mcol2.metric("Total Costos", f"ARS \\${total_costos:,.2f}", f"USD \\${total_costos/VALOR_DOLAR_BLUE:,.2f}")
        
        if balance >= 0:
            mcol3.metric("Ahorro / Ganancia Mensual", f"ARS \\${balance:,.2f}", f"USD \\${balance/VALOR_DOLAR_BLUE:,.2f}", delta="¡Excelente!")
        else:
            mcol3.metric("Déficit Mensual", f"ARS \\${balance:,.2f}", f"USD \\${balance/VALOR_DOLAR_BLUE:,.2f}", delta="Atención", delta_color="inverse")

        # Gráficos porcentuales
        gcol1, gcol2 = st.columns(2)
        
        with gcol1:
            st.markdown("### Porcentaje de Ingresos")
            if not st.session_state.ingresos.empty:
                fig_ing = px.pie(st.session_state.ingresos, names="Item", values="Valor (ARS)", hole=0.4)
                st.plotly_chart(fig_ing, use_container_width=True)
            else:
                st.write("Agrega ingresos para ver el gráfico.")
                
        with gcol2:
            st.markdown("### Porcentaje de Costos de Vida")
            if not st.session_state.costos.empty:
                fig_cos = px.pie(st.session_state.costos, names="Item", values="Valor (ARS)", hole=0.4)
                st.plotly_chart(fig_cos, use_container_width=True)
            else:
                st.write("Agrega costos para ver el gráfico.")

    # ==========================================
    # SECCIÓN 2: CARTERA DE INVERSIONES
    # ==========================================
    elif menu == "📈 Cartera de Inversiones":
        st.title("📈 Cartera de Inversiones")
        st.write("Gestiona y carga información detallada de tus activos divididos por categorías.")
        
        with st.form("form_inversion", clear_on_submit=True):
            col_inv1, col_inv2, col_inv3 = st.columns(3)
            with col_inv1:
                cat_elegida = st.selectbox("Categoría", categorias_inversiones)
            with col_inv2:
                detalle_activo = st.text_input("Detalle / Activo (Ej: USD Billete, BTC, Galicia, Depto)")
            with col_inv3:
                valor_activo = st.number_input("Valor Actual (en Pesos ARS)", min_value=0.0, format="%.2f")
                
            submit_inv = st.form_submit_button("Agregar Inversión")
            
            if submit_inv and detalle_activo:
                nueva_inv = pd.DataFrame({
                    "Categoría": [cat_elegida], 
                    "Detalle / Activo": [detalle_activo], 
                    "Valor Actual (ARS)": [valor_activo]
                })
                st.session_state.inversiones = pd.concat([st.session_state.inversiones, nueva_inv], ignore_index=True)
                st.success(f"Inversión en '{cat_elegida}' guardada.")
                st.rerun()

        st.markdown("---")
        st.subheader("📋 Resumen de tu Cartera")
        
        if not st.session_state.inversiones.empty:
            df_inv = st.session_state.inversiones.copy()
            df_inv["Valor Actual (USD)"] = df_inv["Valor Actual (ARS)"] / VALOR_DOLAR_BLUE
            
            # Mostrar tabla completa
            st.dataframe(df_inv, use_container_width=True)
            
            # Totales globales de inversiones
            total_inv_ars = df_inv["Valor Actual (ARS)"].sum()
            total_inv_usd = df_inv["Valor Actual (USD)"].sum()
            
            col_t1, col_t2 = st.columns(2)
            col_t1.metric("Patrimonio Total en Inversiones (ARS)", f"\\${total_inv_ars:,.2f}")
            col_t2.metric("Patrimonio Total en Inversiones (USD)", f"US\\${total_inv_usd:,.2f}")
            
            st.markdown("### 📊 Distribución de Inversiones por Categoría")
            df_agrupado = df_inv.groupby("Categoría")["Valor Actual (ARS)"].sum().reset_index()
            fig_inv = px.bar(df_agrupado, x="Categoría", y="Valor Actual (ARS)", text_auto='.2s', color="Categoría")
            st.plotly_chart(fig_inv, use_container_width=True)
            
            if st.button("Borrar último registro de inversión"):
                st.session_state.inversiones = st.session_state.inversiones.iloc[:-1]
                st.rerun()
        else:
            st.info("Aún no has cargado inversiones en tu cartera.")
