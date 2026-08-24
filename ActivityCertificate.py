import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, date

# ── CONFIGURACION SUPABASE ──
# Reemplaza estos valores con los de tu proyecto Supabase
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://TU-PROYECTO.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "TU-ANON-KEY-AQUI")

@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

# ── CONFIGURACION DE LA PAGINA ──
st.set_page_config(
    page_title="Activity Certificates DB - Supabase",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS
st.markdown('''
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #0d47a1; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.1rem; color: #666; margin-bottom: 2rem; }
    .metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 12px; color: white; text-align: center; }
    .metric-value { font-size: 2rem; font-weight: 700; }
    .metric-label { font-size: 0.9rem; opacity: 0.9; }
    .stAlert { border-radius: 8px; }
</style>
''', unsafe_allow_html=True)

# ── FUNCIONES CRUD CON SUPABASE ──

def add_certificate(data):
    try:
        response = supabase.table("certificates").insert(data).execute()
        return True, response
    except Exception as e:
        return False, str(e)

def update_certificate(cert_id, data):
    try:
        response = supabase.table("certificates").update(data).eq("id", cert_id).execute()
        return True, response
    except Exception as e:
        return False, str(e)

def delete_certificate(cert_id):
    try:
        response = supabase.table("certificates").delete().eq("id", cert_id).execute()
        return True, response
    except Exception as e:
        return False, str(e)

def get_all_certificates():
    try:
        response = supabase.table("certificates").select("*").order("activity_date", desc=True).execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            df["signed"] = df["signed"].apply(lambda x: "YES" if x else "NO")
            df["cargado"] = df["cargado"].apply(lambda x: "YES" if x else "NO")
        return df
    except Exception as e:
        st.error(f"Error al obtener datos: {e}")
        return pd.DataFrame()

def get_certificate_by_id(cert_id):
    try:
        response = supabase.table("certificates").select("*").eq("id", cert_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None

def get_monthly_summary():
    try:
        # Usamos RPC (funcion SQL) o hacemos el groupby en Python
        response = supabase.table("certificates").select("*").execute()
        df = pd.DataFrame(response.data)
        if df.empty:
            return pd.DataFrame()
        df["month"] = pd.to_datetime(df["activity_date"]).dt.strftime("%Y-%m")
        summary = df.groupby("month").agg(
            total_tickets=("id", "count"),
            total_amount=("total_amount", "sum"),
            signed_count=("signed", lambda x: (x == True).sum()),
            cargado_count=("cargado", lambda x: (x == True).sum())
        ).reset_index()
        return summary.sort_values("month", ascending=False)
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

def get_provider_summary():
    try:
        response = supabase.table("certificates").select("*").execute()
        df = pd.DataFrame(response.data)
        if df.empty:
            return pd.DataFrame()
        df = df[df["provider"].notna() & (df["provider"] != "")]
        summary = df.groupby("provider").agg(
            total_tickets=("id", "count"),
            total_amount=("total_amount", "sum")
        ).reset_index().sort_values("total_amount", ascending=False)
        return summary
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

# ── SIDEBAR: NAVEGACION ──
st.sidebar.markdown("## 📋 Menu")
page = st.sidebar.radio("", [
    "🏠 Dashboard",
    "➕ Nuevo Certificate",
    "📋 Ver / Editar / Eliminar",
    "📊 Reportes por Mes",
    "📤 Importar / Exportar",
    "⚙️ Configuracion"
])

# PAGINA: DASHBOARD
if page == "🏠 Dashboard":
    st.markdown("<div class='main-header'>Activity Certificates Dashboard</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Resumen general - Datos en la nube con Supabase</div>", unsafe_allow_html=True)
    df = get_all_certificates()
    if df.empty:
        st.info("📭 No hay certificados registrados aun. Ve a 'Nuevo Certificate' para agregar uno.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        total_tickets = len(df)
        total_amount = df["total_amount"].sum()
        signed_count = len(df[df["signed"] == "YES"])
        cargado_count = len(df[df["cargado"] == "YES"])
        with col1:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{total_tickets}</div><div class='metric-label'>Total Tickets</div></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='metric-card' style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);'><div class='metric-value'>${total_amount:,.2f}</div><div class='metric-label'>Monto Total</div></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='metric-card' style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);'><div class='metric-value'>{signed_count}</div><div class='metric-label'>Firmados</div></div>", unsafe_allow_html=True)
        with col4:
            st.markdown(f"<div class='metric-card' style='background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);'><div class='metric-value'>{cargado_count}</div><div class='metric-label'>Cargados</div></div>", unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("📊 Resumen por Mes")
        monthly = get_monthly_summary()
        if not monthly.empty:
            monthly["total_amount"] = monthly["total_amount"].apply(lambda x: f"${x:,.2f}")
            monthly.columns = ["Mes", "Tickets", "Monto Total", "Firmados", "Cargados"]
            st.dataframe(monthly, use_container_width=True, hide_index=True)
        st.subheader("📝 Ultimos 10 Registros")
        st.dataframe(df.head(10), use_container_width=True, hide_index=True)

# PAGINA: NUEVO CERTIFICATE
elif page == "➕ Nuevo Certificate":
    st.markdown("<div class='main-header'>Nuevo Activity Certificate</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Completa el formulario para registrar un nuevo certificate en Supabase</div>", unsafe_allow_html=True)
    with st.form("new_certificate_form"):
        col1, col2 = st.columns(2)
        with col1:
            guest_name = st.text_input("👤 Guest Name *", placeholder="Ej: TIFFANY LUI")
            ticket_number = st.text_input("🎫 Ticket Number *", placeholder="Ej: VT260801")
            total_amount = st.number_input("💰 Total Amount *", min_value=0.0, step=0.01, format="%.2f")
            activity_date = st.date_input("📅 Activity Date *", value=date.today())
            provider = st.text_input("🏢 Provider", placeholder="Ej: LA CERNIA")
        with col2:
            concierge = st.text_input("🤵 Concierge", placeholder="Ej: MIGUEL")
            guest_arrival_date = st.date_input("🏨 Guest Arrival Date", value=None)
            signed = st.checkbox("✍️ Signed (Yes)")
            cargado = st.checkbox("📥 Cargado (Yes)")
            notes = st.text_area("📝 Notas adicionales", placeholder="Cualquier informacion extra...")
        submitted = st.form_submit_button("💾 Guardar en Supabase", use_container_width=True)
        if submitted:
            if not guest_name or not ticket_number or total_amount <= 0:
                st.error("❌ Por favor completa los campos obligatorios: Guest Name, Ticket Number y Total Amount.")
            else:
                data = {
                    "guest_name": guest_name.upper().strip(),
                    "ticket_number": ticket_number.upper().strip(),
                    "total_amount": total_amount,
                    "activity_date": activity_date.strftime("%Y-%m-%d"),
                    "provider": provider.strip(),
                    "concierge": concierge.strip(),
                    "guest_arrival_date": guest_arrival_date.strftime("%Y-%m-%d") if guest_arrival_date else None,
                    "signed": signed,
                    "cargado": cargado,
                    "notes": notes.strip()
                }
                success, response = add_certificate(data)
                if success:
                    st.success(f"✅ Certificate {ticket_number} guardado en Supabase!")
                    st.balloons()
                else:
                    st.error(f"❌ Error: {response}")

# PAGINA: VER / EDITAR / ELIMINAR
elif page == "📋 Ver / Editar / Eliminar":
    st.markdown("<div class='main-header'>Gestionar Certificates</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Busca, filtra, edita o elimina registros en Supabase</div>", unsafe_allow_html=True)
    df = get_all_certificates()
    if df.empty:
        st.info("📭 No hay certificados registrados.")
    else:
        st.subheader("🔍 Filtros")
        fcol1, fcol2, fcol3, fcol4 = st.columns(4)
        with fcol1:
            search_name = st.text_input("Buscar por Guest Name")
        with fcol2:
            search_ticket = st.text_input("Buscar por Ticket")
        with fcol3:
            months_list = ["Todos"] + sorted(df["activity_date"].str[:7].unique().tolist(), reverse=True)
            filter_month = st.selectbox("Filtrar por Mes", months_list)
        with fcol4:
            providers_list = ["Todos"] + sorted(df["provider"].dropna().unique().tolist())
            filter_provider = st.selectbox("Filtrar por Provider", providers_list)
        filtered = df.copy()
        if search_name:
            filtered = filtered[filtered["guest_name"].str.contains(search_name, case=False, na=False)]
        if search_ticket:
            filtered = filtered[filtered["ticket_number"].str.contains(search_ticket, case=False, na=False)]
        if filter_month != "Todos":
            filtered = filtered[filtered["activity_date"].str.startswith(filter_month)]
        if filter_provider != "Todos":
            filtered = filtered[filtered["provider"] == filter_provider]
        st.markdown(f"**Mostrando {len(filtered)} de {len(df)} registros**")
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        st.markdown("---")
        st.subheader("✏️ Editar o 🗑️ Eliminar Certificate")
        edit_col1, edit_col2 = st.columns([1, 3])
        with edit_col1:
            edit_id = st.number_input("ID del Certificate", min_value=1, step=1)
        cert = get_certificate_by_id(edit_id)
        if cert is None:
            st.warning("No se encontro un certificate con ese ID.")
        else:
            with st.expander(f"Editando: {cert['ticket_number']} - {cert['guest_name']}", expanded=True):
                with st.form("edit_form"):
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        e_guest = st.text_input("Guest Name", value=cert["guest_name"])
                        e_ticket = st.text_input("Ticket Number", value=cert["ticket_number"])
                        e_amount = st.number_input("Total Amount", min_value=0.0, step=0.01, format="%.2f", value=float(cert["total_amount"]))
                        e_activity = st.date_input("Activity Date", value=datetime.strptime(cert["activity_date"], "%Y-%m-%d").date())
                        e_provider = st.text_input("Provider", value=cert["provider"] if cert["provider"] else "")
                    with ec2:
                        e_concierge = st.text_input("Concierge", value=cert["concierge"] if cert["concierge"] else "")
                        e_arrival = st.date_input("Guest Arrival Date", value=datetime.strptime(cert["guest_arrival_date"], "%Y-%m-%d").date() if cert["guest_arrival_date"] else None)
                        e_signed = st.checkbox("Signed", value=cert["signed"])
                        e_cargado = st.checkbox("Cargado", value=cert["cargado"])
                        e_notes = st.text_area("Notas", value=cert["notes"] if cert["notes"] else "")
                    ecol1, ecol2 = st.columns(2)
                    with ecol1:
                        update_btn = st.form_submit_button("💾 Actualizar en Supabase", use_container_width=True)
                    with ecol2:
                        delete_btn = st.form_submit_button("🗑️ Eliminar de Supabase", use_container_width=True)
                    if update_btn:
                        data = {
                            "guest_name": e_guest.upper().strip(),
                            "ticket_number": e_ticket.upper().strip(),
                            "total_amount": e_amount,
                            "activity_date": e_activity.strftime("%Y-%m-%d"),
                            "provider": e_provider.strip(),
                            "concierge": e_concierge.strip(),
                            "guest_arrival_date": e_arrival.strftime("%Y-%m-%d") if e_arrival else None,
                            "signed": e_signed,
                            "cargado": e_cargado,
                            "notes": e_notes.strip()
                        }
                        success, response = update_certificate(edit_id, data)
                        if success:
                            st.success("✅ Certificate actualizado en Supabase!")
                            st.rerun()
                        else:
                            st.error(f"❌ Error: {response}")
                    if delete_btn:
                        success, response = delete_certificate(edit_id)
                        if success:
                            st.success("🗑️ Certificate eliminado de Supabase!")
                            st.rerun()
                        else:
                            st.error(f"❌ Error: {response}")

# PAGINA: REPORTES POR MES
elif page == "📊 Reportes por Mes":
    st.markdown("<div class='main-header'>Reportes por Mes</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Analisis detallado mensual desde Supabase</div>", unsafe_allow_html=True)
    monthly = get_monthly_summary()
    if monthly.empty:
        st.info("📭 No hay datos suficientes para generar reportes.")
    else:
        st.subheader("📈 Monto Total por Mes")
        chart_data = monthly.copy()
        chart_data["month"] = pd.to_datetime(chart_data["month"])
        chart_data = chart_data.sort_values("month")
        st.bar_chart(chart_data.set_index("month")["total_amount"])
        st.subheader("📋 Detalle Mensual")
        monthly_display = monthly.copy()
        monthly_display["total_amount"] = monthly_display["total_amount"].apply(lambda x: f"${x:,.2f}")
        monthly_display.columns = ["Mes", "Tickets", "Monto Total", "Firmados", "Cargados"]
        st.dataframe(monthly_display, use_container_width=True, hide_index=True)
        st.subheader("🏢 Top Providers")
        providers = get_provider_summary()
        if not providers.empty:
            providers["total_amount"] = providers["total_amount"].apply(lambda x: f"${x:,.2f}")
            providers.columns = ["Provider", "Tickets", "Monto Total"]
            st.dataframe(providers, use_container_width=True, hide_index=True)
            st.subheader("📊 Distribucion por Provider")
            provider_chart = get_provider_summary()
            st.bar_chart(provider_chart.set_index("provider")["total_amount"])

# PAGINA: IMPORTAR / EXPORTAR
elif page == "📤 Importar / Exportar":
    st.markdown("<div class='main-header'>Importar / Exportar Datos</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Migra tus archivos Excel a Supabase o exporta la base de datos</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📥 Importar a Supabase desde CSV")
        st.info("Formato esperado: guest_name, ticket_number, total_amount, activity_date, provider, concierge, guest_arrival_date, signed, cargado")
        uploaded_file = st.file_uploader("Selecciona tu archivo CSV", type=["csv"])
        if uploaded_file is not None:
            try:
                import_df = pd.read_csv(uploaded_file)
                st.write("Vista previa:")
                st.dataframe(import_df.head(), use_container_width=True)
                if st.button("📥 Importar a Supabase", use_container_width=True):
                    imported = 0
                    skipped = 0
                    for _, row in import_df.iterrows():
                        try:
                            data = {
                                "guest_name": str(row.get("guest_name", "")).upper().strip(),
                                "ticket_number": str(row.get("ticket_number", "")).upper().strip(),
                                "total_amount": float(row.get("total_amount", 0)),
                                "activity_date": str(row.get("activity_date", "")),
                                "provider": str(row.get("provider", "")).strip(),
                                "concierge": str(row.get("concierge", "")).strip(),
                                "guest_arrival_date": str(row.get("guest_arrival_date", "")) if pd.notna(row.get("guest_arrival_date")) else None,
                                "signed": bool(int(row.get("signed", 0))),
                                "cargado": bool(int(row.get("cargado", 0)))
                            }
                            success, _ = add_certificate(data)
                            if success:
                                imported += 1
                            else:
                                skipped += 1
                        except Exception as e:
                            skipped += 1
                    st.success(f"✅ {imported} registros importados a Supabase. {skipped} omitidos.")
                    st.balloons()
            except Exception as e:
                st.error(f"❌ Error al leer el archivo: {e}")
    with col2:
        st.subheader("📤 Exportar desde Supabase a CSV")
        df_export = get_all_certificates()
        if df_export.empty:
            st.info("No hay datos para exportar.")
        else:
            csv = df_export.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Descargar Todos los Certificates (CSV)",
                data=csv,
                file_name=f"activity_certificates_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            st.markdown("---")
            st.subheader("📅 Exportar por Mes")
            months = sorted(df_export["activity_date"].str[:7].unique().tolist(), reverse=True)
            selected_month = st.selectbox("Selecciona un mes", months)
            if selected_month:
                month_df = df_export[df_export["activity_date"].str.startswith(selected_month)]
                month_csv = month_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label=f"⬇️ Descargar {selected_month} (CSV)",
                    data=month_csv,
                    file_name=f"certificates_{selected_month}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

# PAGINA: CONFIGURACION
elif page == "⚙️ Configuracion":
    st.markdown("<div class='main-header'>Configuracion de Supabase</div>", unsafe_allow_html=True)
    st.markdown("""
    ### 🔑 Como configurar tu proyecto Supabase
    
    **1. Crea tu proyecto en [supabase.com](https://supabase.com)**
    - Registrate gratis
    - Crea un nuevo proyecto
    - Espera a que se provisione
    
    **2. Crea la tabla `certificates`**
    - Ve a SQL Editor > New query
    - Pega el script SQL que te proporcione
    - Ejecuta
    
    **3. Obtén tus credenciales**
    - Ve a Project Settings > API
    - Copia `URL` y `anon public` key
    
    **4. Configura en Streamlit**
    Crea un archivo `.streamlit/secrets.toml` con:
    ```toml
    SUPABASE_URL = "https://tu-proyecto.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIs..."
    ```
    
    **5. Ejecuta la app**
    ```bash
    streamlit run app_supabase.py
    ```
    """)
    st.info("💡 La conexion actual usa valores por defecto. Reemplazalos en el codigo o usa secrets.toml")

# ── SIDEBAR FOOTER / CREDITOS ──
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="text-align: center; padding: 10px 0;">
    <p style="margin: 0; font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 1px;">Desarrollado por</p>
    <p style="margin: 4px 0 12px 0; font-size: 1rem; font-weight: 700; color: #fff;">Fred Wayne</p>

    <p style="margin: 0; font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 1px;">Departamento</p>
    <p style="margin: 4px 0 12px 0; font-size: 0.95rem; font-weight: 600; color: #ccc;">Concierge</p>

    <p style="margin: 0; font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 1px;">Hotel</p>
    <p style="margin: 4px 0 0 0; font-size: 0.9rem; font-weight: 600; color: #ccc; line-height: 1.4;">Waldorf Astoria<br>at Punta Cacique<br>Costa Rica 🇨🇷</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Estadisticas")
df_stats = get_all_certificates()
if not df_stats.empty:
    st.sidebar.metric("Total Registros", len(df_stats))
    st.sidebar.metric("Monto Total", f"${df_stats['total_amount'].sum():,.2f}")
else:
    st.sidebar.info("Sin datos aun")

st.sidebar.markdown("---")
st.sidebar.caption("v1.0 | Activity Certificates DB")
