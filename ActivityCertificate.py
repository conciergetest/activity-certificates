import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, date
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, HexColor
import io
from streamlit.components.v1 import html

# ── CONFIGURACION SUPABASE ──
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://TU-PROYECTO.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "TU-ANON-KEY-AQUI")

@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase_client()

# ── CONFIGURACION DE LA PAGINA ──
st.set_page_config(
    page_title="Activity Certificates DB",
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

# ── FUNCION PARA GENERAR PDF EN HORIZONTAL ──
def generate_certificate_pdf(cert_data, logo_path="LogoWaldorf.png"):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(letter))
    width, height = landscape(letter)
    left_m = 0.6 * inch

    # --- HEADER ---
    # C: Logo mas grande
    try:
        c.drawImage(logo_path, width - 2.4*inch, height - 1.15*inch, 
                   width=2.0*inch, height=0.9*inch, preserveAspectRatio=True, mask="auto")
    except Exception:
        pass

    # B: Ref del ticket en AZUL INTENSO
    c.setFillColor(HexColor("#0047AB"))
    c.setFont("Helvetica-Bold", 22)
    c.drawString(width - 2.4*inch, height - 1.55*inch, f"Ref: {cert_data.get('ticket_number', '')}")
    c.setFillColor(black)

    c.setFont("Helvetica-Bold", 28)
    c.drawString(left_m, height - 0.75*inch, "ACTIVITY")
    c.drawString(left_m, height - 1.15*inch, "CERTIFICATE")

    # --- LINEA 1: Concierge ---
    y = height - 1.85*inch
    c.setFont("Helvetica", 11)
    c.drawString(left_m, y, "Concierge")
    c.line(left_m + 1.1*inch, y - 0.05*inch, 6.5*inch, y - 0.05*inch)
    if cert_data.get("concierge"):
        c.setFont("Helvetica-Bold", 11)
        c.drawString(left_m + 1.15*inch, y + 0.02*inch, str(cert_data.get("concierge", "")).upper())

    # --- LINEA 2: Name | Room | Confirmed with | On ---
    y = height - 2.35*inch
    c.setFont("Helvetica", 11)
    c.drawString(left_m, y, "Name")
    c.line(left_m + 0.7*inch, y - 0.05*inch, 4.2*inch, y - 0.05*inch)
    if cert_data.get("guest_name"):
        c.setFont("Helvetica-Bold", 11)
        c.drawString(left_m + 0.75*inch, y + 0.02*inch, str(cert_data.get("guest_name", "")).upper())
    c.setFont("Helvetica", 11)
    c.drawString(4.4*inch, y, "Room")
    c.line(4.85*inch, y - 0.05*inch, 5.8*inch, y - 0.05*inch)
    # A: Mostrar room si existe, dejar vacio si no
    if cert_data.get("room"):
        c.setFont("Helvetica-Bold", 11)
        c.drawString(4.9*inch, y + 0.02*inch, str(cert_data.get("room", "")).upper())
    c.setFont("Helvetica", 11)
    c.drawString(6.0*inch, y, "Confirmed with")
    c.line(7.3*inch, y - 0.05*inch, 8.8*inch, y - 0.05*inch)
    if cert_data.get("provider"):
        c.setFont("Helvetica-Bold", 11)
        c.drawString(7.35*inch, y + 0.02*inch, str(cert_data.get("provider", "")).upper())
    c.setFont("Helvetica", 11)
    c.drawString(9.0*inch, y, "On")
    c.line(9.4*inch, y - 0.05*inch, 10.0*inch, y - 0.05*inch)
    if cert_data.get("guest_arrival_date"):
        c.setFont("Helvetica-Bold", 11)
        c.drawString(9.45*inch, y + 0.02*inch, str(cert_data.get("guest_arrival_date", "")))
    c.setFont("Helvetica", 11)

    # --- LINEA 3: Vendor | Event ---
    y = height - 2.85*inch
    c.drawString(left_m, y, "Vendor")
    c.line(left_m + 0.7*inch, y - 0.05*inch, 4.2*inch, y - 0.05*inch)
    if cert_data.get("provider"):
        c.setFont("Helvetica-Bold", 11)
        c.drawString(left_m + 0.75*inch, y + 0.02*inch, str(cert_data.get("provider", "")).upper())
    c.setFont("Helvetica", 11)
    c.drawString(4.4*inch, y, "Event")
    c.line(4.85*inch, y - 0.05*inch, 10.0*inch, y - 0.05*inch)
    if cert_data.get("notes"):
        c.setFont("Helvetica-Bold", 11)
        c.drawString(4.9*inch, y + 0.02*inch, str(cert_data.get("notes", "")).upper())
    c.setFont("Helvetica", 11)

    # --- LINEA 4: Pickup/Meet | Time | Day | Date ---
    y = height - 3.35*inch
    c.rect(left_m, y - 0.12*inch, 0.15*inch, 0.15*inch)
    c.drawString(left_m + 0.22*inch, y, "Pickup at Porte cochere")
    c.rect(left_m, y - 0.45*inch, 0.15*inch, 0.15*inch)
    c.drawString(left_m + 0.22*inch, y - 0.33*inch, "Meet at")
    c.line(left_m + 0.9*inch, y - 0.38*inch, 4.2*inch, y - 0.38*inch)
    if cert_data.get("meeting_point"):
        c.setFont("Helvetica-Bold", 11)
        c.drawString(left_m + 0.95*inch, y - 0.3*inch, str(cert_data.get("meeting_point", "")).upper())
    c.setFont("Helvetica", 11)
    c.drawString(4.4*inch, y, "Time")
    c.line(4.85*inch, y - 0.05*inch, 5.8*inch, y - 0.05*inch)
    if cert_data.get("activity_time"):
        c.setFont("Helvetica-Bold", 11)
        c.drawString(4.9*inch, y + 0.02*inch, str(cert_data.get("activity_time", "")).upper())
    c.setFont("Helvetica", 11)
    c.drawString(6.0*inch, y, "Day")
    c.line(6.4*inch, y - 0.05*inch, 8.0*inch, y - 0.05*inch)
    activity_date = cert_data.get("activity_date", "")
    if activity_date:
        try:
            day_name = datetime.strptime(str(activity_date), "%Y-%m-%d").strftime("%A").upper()
            c.setFont("Helvetica-Bold", 11)
            c.drawString(6.45*inch, y + 0.02*inch, day_name)
        except Exception:
            pass
    c.setFont("Helvetica", 11)
    c.drawString(8.2*inch, y, "Date")
    c.line(8.6*inch, y - 0.05*inch, 10.0*inch, y - 0.05*inch)
    if activity_date:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(8.65*inch, y + 0.02*inch, str(activity_date))
    c.setFont("Helvetica", 11)

    # --- NOTES ---
    y = height - 4.0*inch
    c.drawString(left_m, y, "Notes")
    c.line(left_m + 0.7*inch, y - 0.05*inch, 10.0*inch, y - 0.05*inch)
    c.line(left_m + 0.7*inch, y - 0.38*inch, 10.0*inch, y - 0.38*inch)
    c.line(left_m + 0.7*inch, y - 0.71*inch, 10.0*inch, y - 0.71*inch)
    c.line(left_m + 0.7*inch, y - 1.04*inch, 10.0*inch, y - 1.04*inch)
    notes = cert_data.get("notes", "")
    if notes:
        text_obj = c.beginText(left_m + 0.75*inch, y - 0.28*inch)
        text_obj.setFont("Helvetica", 10)
        for line in str(notes).split("\n")[:4]:
            text_obj.textLine(line)
        c.drawText(text_obj)

    # --- CANCELLATION FEE (izquierda, parte inferior) ---
    y = height - 5.6*inch
    c.setFont("Helvetica", 10)
    c.drawString(left_m, y, "A 100% cancellation fee is applicable if")
    c.drawString(left_m, y - 0.2*inch, "cancelation within 48 hours of confirmed activity")
    c.line(left_m, y - 0.85*inch, 4.0*inch, y - 0.85*inch)
    c.setFont("Helvetica", 10)
    c.drawCentredString(2.3*inch, y - 1.05*inch, "Guest's signature")
    c.rect(left_m, y - 1.5*inch, 0.15*inch, 0.15*inch)
    if cert_data.get("signed"):
        c.setFont("Helvetica-Bold", 12)
        c.drawString(left_m + 0.03*inch, y - 1.46*inch, "X")
    c.setFont("Helvetica", 10)
    c.drawString(left_m + 0.22*inch, y - 1.38*inch, "Waiver ok")
    c.rect(2.2*inch, y - 1.5*inch, 0.15*inch, 0.15*inch)
    if cert_data.get("cargado"):
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2.23*inch, y - 1.46*inch, "X")
    c.setFont("Helvetica", 10)
    c.drawString(2.42*inch, y - 1.38*inch, "Logged")

    # --- TABLA DERECHA (Adults, Children, Totals) ---
    table_x = 5.0*inch
    table_top = height - 5.3*inch
    row_h = 0.38*inch
    col1_w = 1.8*inch
    col2_w = 1.4*inch
    col3_w = 1.4*inch
    total_w = col1_w + col2_w + col3_w

    adults_val = str(cert_data.get("adults", "")) if cert_data.get("adults") else ""
    kids_val = str(cert_data.get("kids", "")) if cert_data.get("kids") else ""

    rows = [
        ("Adults", adults_val, "Each"),
        ("Children", kids_val, "Each"),
        ("Post to", "Sub Total", ""),
        ("", "", ""),
        ("", "Tax", ""),
        ("", "Total", ""),
        ("", "Total", "")
    ]

    for i, (col1, col2, col3) in enumerate(rows):
        y_pos = table_top - (i + 1) * row_h
        c.line(table_x, y_pos, table_x + total_w, y_pos)
        c.setFont("Helvetica", 10)
        if col1:
            c.drawString(table_x + 0.1*inch, y_pos + 0.12*inch, col1)
        if col2:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(table_x + col1_w + 0.1*inch, y_pos + 0.12*inch, str(col2))
            c.setFont("Helvetica", 10)
        if col3:
            c.drawString(table_x + col1_w + col2_w + 0.1*inch, y_pos + 0.12*inch, col3)
        if col2 == "Total" and cert_data.get("total_amount") is not None:
            total = float(cert_data.get("total_amount", 0))
            c.setFont("Helvetica-Bold", 10)
            c.drawString(table_x + col1_w + col2_w + 0.1*inch, y_pos + 0.12*inch, f"${total:,.2f}")
            c.setFont("Helvetica", 10)

    c.line(table_x, table_top, table_x + total_w, table_top)
    c.line(table_x, table_top, table_x, table_top - len(rows)*row_h)
    c.line(table_x + col1_w, table_top, table_x + col1_w, table_top - len(rows)*row_h)
    c.line(table_x + col1_w + col2_w, table_top, table_x + col1_w + col2_w, table_top - len(rows)*row_h)
    c.line(table_x + total_w, table_top, table_x + total_w, table_top - len(rows)*row_h)

    c.save()
    buffer.seek(0)
    return buffer

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

def get_certificates_by_month(month_str):
    """Obtiene todos los certificates de un mes especifico para backup."""
    try:
        response = supabase.table("certificates").select("*").execute()
        df = pd.DataFrame(response.data)
        if df.empty:
            return pd.DataFrame()
        return df[df["activity_date"].str.startswith(month_str)]
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

def delete_certificates_by_month(month_str):
    """Borra todos los certificates de un mes especifico usando rango de fechas."""
    try:
        from datetime import datetime, timedelta
        # Parse year and month
        year, month = int(month_str[:4]), int(month_str[5:7])
        start_date = datetime(year, month, 1).strftime("%Y-%m-%d")
        # Calculate next month
        if month == 12:
            end_year, end_month = year + 1, 1
        else:
            end_year, end_month = year, month + 1
        end_date = datetime(end_year, end_month, 1).strftime("%Y-%m-%d")

        response = supabase.table("certificates").delete().gte("activity_date", start_date).lt("activity_date", end_date).execute()
        return True, response
    except Exception as e:
        return False, str(e)

def get_next_ticket_number():
    try:
        response = supabase.table("certificates").select("ticket_number").execute()
        df = pd.DataFrame(response.data)
        if df.empty:
            return "VT000001"
        df["num"] = df["ticket_number"].str.extract(r"VT(\d+)").astype(int)
        max_num = df["num"].max()
        next_num = max_num + 1
        return f"VT{next_num:06d}"
    except Exception:
        return "VT000001"

# ── SIDEBAR: NAVEGACION ──
st.sidebar.markdown("## 📋 Menu")
page = st.sidebar.radio("", [
    "🏠 Dashboard",
    "➕ Nuevo Certificate",
    "📋 Ver / Editar / Eliminar",
    "📊 Reportes por Mes",
    "📤 Importar / Exportar",
    "🗑️ Limpiar por Mes",
    "⚙️ Configuracion"
])

# PAGINA: DASHBOARD
if page == "🏠 Dashboard":
    dash_col1, dash_col2 = st.columns([3, 1])
    with dash_col1:
        st.markdown("<div class='main-header'>Activity Certificates Dashboard</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Resumen general</div>", unsafe_allow_html=True)
    with dash_col2:
        # Reloj en tiempo real con JavaScript (se actualiza sin recargar la pagina)
        clock_html = """
        <div id="live-clock" style="text-align:right; margin-bottom:8px; font-family:monospace;">
            <div id="clock-time" style="font-size:1.6rem; font-weight:700; color:#00FFFF; text-shadow:0 0 8px #00FFFF;"></div>
            <div id="clock-date" style="font-size:1.1rem; font-weight:700; color:#00FFFF; text-shadow:0 0 6px #00FFFF; margin-top:4px;"></div>
        </div>
        <script>
            function updateClock() {
                const now = new Date();
                const timeOptions = { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true };
                const dateOptions = { weekday: 'long', year: 'numeric', month: 'long', day: '2-digit' };
                document.getElementById('clock-time').textContent = now.toLocaleTimeString('en-US', timeOptions);
                document.getElementById('clock-date').textContent = now.toLocaleDateString('en-US', dateOptions);
            }
            updateClock();
            setInterval(updateClock, 1000);
        </script>
        """
        html(clock_html, height=90)

    df = get_all_certificates()

    if df.empty:
        st.info("📭 No hay certificados registrados aun. Ve a 'Nuevo Certificate' para agregar uno.")
    else:
        if "created_at" in df.columns:
            df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d")

        current_month = datetime.now().strftime("%Y-%m")

        st.subheader("🔍 Filtros")
        fcol1, fcol2, fcol3, fcol4, fcol5 = st.columns(5)
        with fcol1:
            months_list = ["Mes actual (" + current_month + ")"] + sorted(df["activity_date"].str[:7].unique().tolist(), reverse=True)
            filter_month = st.selectbox("Filtrar por Mes", months_list)
        with fcol2:
            providers_list = ["Todos"] + sorted(df["provider"].dropna().unique().tolist())
            filter_provider = st.selectbox("Filtrar por Provider", providers_list)
        with fcol3:
            filter_guest = st.text_input("Buscar por Guest Name")
        with fcol4:
            filter_ticket = st.text_input("Buscar por Ticket (VT)")
        with fcol5:
            concierges_list = ["Todos"] + sorted(df["concierge"].dropna().unique().tolist())
            filter_concierge = st.selectbox("Filtrar por Concierge", concierges_list)

        filtered = df.copy()
        if filter_month != "Mes actual (" + current_month + ")":
            filtered = filtered[filtered["activity_date"].str.startswith(filter_month)]
        else:
            filtered = filtered[filtered["activity_date"].str.startswith(current_month)]
        if filter_provider != "Todos":
            filtered = filtered[filtered["provider"] == filter_provider]
        if filter_guest:
            filtered = filtered[filtered["guest_name"].str.contains(filter_guest, case=False, na=False)]
        if filter_ticket:
            filtered = filtered[filtered["ticket_number"].str.contains(filter_ticket, case=False, na=False)]
        if filter_concierge != "Todos":
            filtered = filtered[filtered["concierge"] == filter_concierge]

        st.markdown(f"**Mostrando {len(filtered)} registros**")

        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Estadisticas del Mes")
        st.sidebar.metric("Total Registros", len(filtered))
        st.sidebar.metric("Monto Total", f"${filtered['total_amount'].sum():,.2f}")
        try:
            st.sidebar.image("FredWayneLOGO.jpeg", width=220)
        except Exception:
            pass

        col1, col2, col3, col4 = st.columns(4)
        total_tickets = len(filtered)
        total_amount = filtered["total_amount"].sum()
        signed_count = len(filtered[filtered["signed"] == "YES"])
        cargado_count = len(filtered[filtered["cargado"] == "YES"])
        with col1:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{total_tickets}</div><div class='metric-label'>Total Tickets</div></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='metric-card' style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);'><div class='metric-value'>${total_amount:,.2f}</div><div class='metric-label'>Monto Total</div></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='metric-card' style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);'><div class='metric-value'>{signed_count}</div><div class='metric-label'>Firmados</div></div>", unsafe_allow_html=True)
        with col4:
            st.markdown(f"<div class='metric-card' style='background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);'><div class='metric-value'>{cargado_count}</div><div class='metric-label'>Cargados</div></div>", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📊 Resumen")
        monthly = get_monthly_summary()
        if not monthly.empty:
            monthly["total_amount"] = monthly["total_amount"].apply(lambda x: f"${x:,.2f}")
            monthly.columns = ["Mes", "Tickets", "Monto Total", "Firmados", "Cargados"]
            st.dataframe(monthly, use_container_width=True, hide_index=True)

        st.subheader("📝 Registros del Mes")
        display_df = filtered.copy()
        display_df["total_amount"] = display_df["total_amount"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

# PAGINA: NUEVO CERTIFICATE
elif page == "➕ Nuevo Certificate":
    st.markdown("<div class='main-header'>Nuevo Activity Certificate</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Completa el formulario para registrar un nuevo certificate</div>", unsafe_allow_html=True)

    if "last_saved_cert" not in st.session_state:
        st.session_state.last_saved_cert = None
    if "save_success" not in st.session_state:
        st.session_state.save_success = False

    with st.form("new_certificate_form"):
        col1, col2 = st.columns(2)
        with col1:
            guest_name = st.text_input("👤 Guest Name *", placeholder="Ej: TIFFANY LUI")
            next_ticket = get_next_ticket_number()
            ticket_number = st.text_input("🎫 Ticket Number", value=next_ticket, disabled=True)
            total_amount = st.number_input("💰 Total Amount *", min_value=0.0, step=0.01, format="%.2f")
            activity_date = st.date_input("📅 Activity Date *", value=date.today())
            provider = st.text_input("🏢 Provider", placeholder="Ej: LA CERNIA")
            activity_time = st.text_input("🕐 Activity Time", placeholder="Ej: 09:30 AM")
            adults = st.number_input("👨 Adults", min_value=0, step=1, value=0)
            room = st.text_input("🚪 Room", placeholder="Ej: 1205")
        with col2:
            concierge = st.text_input("🤵 Concierge", placeholder="Ej: MIGUEL")
            guest_arrival_date = st.date_input("🏨 Guest Arrival Date", value=None)
            signed = st.checkbox("✍️ Signed (Yes)")
            cargado = st.checkbox("📥 Cargado (Yes)")
            meeting_point = st.text_input("📍 Meeting Point", placeholder="Ej: Lobby")
            notes = st.text_area("📝 Notas adicionales", placeholder="Cualquier informacion extra...")
            kids = st.number_input("👶 Kids", min_value=0, step=1, value=0)
        submitted = st.form_submit_button("💾 Guardar", use_container_width=True)

        if submitted:
            if not guest_name or not ticket_number or total_amount <= 0:
                st.error("❌ Por favor completa los campos obligatorios: Guest Name, Ticket Number y Total Amount.")
                st.session_state.save_success = False
                st.session_state.last_saved_cert = None
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
                    "notes": notes.strip(),
                    "activity_time": activity_time.strip() if activity_time else None,
                    "meeting_point": meeting_point.strip() if meeting_point else None,
                    "adults": int(adults) if adults > 0 else None,
                    "kids": int(kids) if kids > 0 else None,
                    "room": room.strip().upper() if room else None
                }
                success, response = add_certificate(data)
                if success:
                    st.session_state.save_success = True
                    st.session_state.last_saved_cert = data
                    st.rerun()
                else:
                    st.session_state.save_success = False
                    st.session_state.last_saved_cert = None
                    st.error(f"❌ Error: {response}")

    if st.session_state.save_success and st.session_state.last_saved_cert:
        st.success(f"✅ Certificate {st.session_state.last_saved_cert['ticket_number']} guardado correctamente!")
        st.balloons()
        st.markdown("---")
        st.subheader("📄 Descargar Certificate en PDF")
        cert_data = st.session_state.last_saved_cert
        pdf_buffer = generate_certificate_pdf(cert_data, logo_path="LogoWaldorf.png")
        st.download_button(
            label="⬇️ Descargar PDF",
            data=pdf_buffer,
            file_name=f"{cert_data['ticket_number']}_certificate.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        st.session_state.save_success = False
        st.session_state.last_saved_cert = None

# PAGINA: VER / EDITAR / ELIMINAR
elif page == "📋 Ver / Editar / Eliminar":
    st.markdown("<div class='main-header'>Gestionar Certificates</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Busca, filtra, edita o elimina registros</div>", unsafe_allow_html=True)
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
        display_df = filtered.copy()
        display_df["total_amount"] = display_df["total_amount"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        st.markdown("---")
        st.subheader("✏️ Editar o 🗑️ Eliminar Certificate")
        edit_col1, edit_col2 = st.columns([1, 3])

        # FIX: Use session_state variable instead of widget key to avoid StreamlitAPIException
        if "edit_id_value" not in st.session_state:
            st.session_state.edit_id_value = 0
        with edit_col1:
            edit_id = st.number_input("ID del Certificate", min_value=0, step=1, value=st.session_state.edit_id_value)
        if edit_id == 0:
            st.info("Ingresa un ID de certificate para editar o eliminar.")
        else:
            cert = get_certificate_by_id(edit_id)
            if cert is None:
                st.warning("No se encontro un certificate con ese ID.")
            else:
                st.markdown("---")
                pdf_col1, pdf_col2 = st.columns(2)
                with pdf_col1:
                    pdf_buffer = generate_certificate_pdf(cert, logo_path="LogoWaldorf.png")
                    st.download_button(
                        label="📄 Descargar PDF de este Certificate",
                        data=pdf_buffer,
                        file_name=f"{cert['ticket_number']}_certificate.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                with pdf_col2:
                    st.info(f"Ticket: **{cert['ticket_number']}** | Guest: **{cert['guest_name']}**")

                with st.expander(f"Editando: {cert['ticket_number']} - {cert['guest_name']}", expanded=True):
                    with st.form("edit_form"):
                        ec1, ec2 = st.columns(2)
                        with ec1:
                            e_guest = st.text_input("Guest Name", value=cert["guest_name"])
                            e_ticket = st.text_input("Ticket Number", value=cert["ticket_number"])
                            e_amount = st.number_input("Total Amount", min_value=0.0, step=0.01, format="%.2f", value=float(cert["total_amount"]))
                            e_activity = st.date_input("Activity Date", value=datetime.strptime(cert["activity_date"], "%Y-%m-%d").date())
                            e_provider = st.text_input("Provider", value=cert["provider"] if cert["provider"] else "")
                            e_time = st.text_input("Activity Time", value=cert["activity_time"] if cert.get("activity_time") else "")
                            e_adults = st.number_input("Adults", min_value=0, step=1, value=int(cert["adults"]) if cert.get("adults") else 0)
                            e_room = st.text_input("Room", value=cert["room"] if cert.get("room") else "")
                        with ec2:
                            e_concierge = st.text_input("Concierge", value=cert["concierge"] if cert["concierge"] else "")
                            e_arrival = st.date_input("Guest Arrival Date", value=datetime.strptime(cert["guest_arrival_date"], "%Y-%m-%d").date() if cert["guest_arrival_date"] else None)
                            e_signed = st.checkbox("Signed", value=cert["signed"])
                            e_cargado = st.checkbox("Cargado", value=cert["cargado"])
                            e_meeting = st.text_input("Meeting Point", value=cert["meeting_point"] if cert.get("meeting_point") else "")
                            e_notes = st.text_area("Notas", value=cert["notes"] if cert["notes"] else "")
                            e_kids = st.number_input("Kids", min_value=0, step=1, value=int(cert["kids"]) if cert.get("kids") else 0)
                        ecol1, ecol2 = st.columns(2)
                        with ecol1:
                            update_btn = st.form_submit_button("💾 Actualizar", use_container_width=True)
                        with ecol2:
                            delete_btn = st.form_submit_button("🗑️ Eliminar", use_container_width=True)
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
                                "notes": e_notes.strip(),
                                "activity_time": e_time.strip() if e_time else None,
                                "meeting_point": e_meeting.strip() if e_meeting else None,
                                "adults": int(e_adults) if e_adults > 0 else None,
                                "kids": int(e_kids) if e_kids > 0 else None,
                                "room": e_room.strip().upper() if e_room else None
                            }
                            success, response = update_certificate(edit_id, data)
                            if success:
                                st.success("✅ Certificate actualizado correctamente!")
                                st.session_state.edit_id_value = 0
                                st.rerun()
                            else:
                                st.error(f"❌ Error: {response}")
                        if delete_btn:
                            success, response = delete_certificate(edit_id)
                            if success:
                                st.success("🗑️ Certificate eliminado correctamente!")
                                st.session_state.edit_id_value = 0
                                st.rerun()
                            else:
                                st.error(f"❌ Error: {response}")

# PAGINA: REPORTES POR MES
elif page == "📊 Reportes por Mes":
    st.markdown("<div class='main-header'>Reportes por Mes</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Analisis detallado mensual</div>", unsafe_allow_html=True)
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
    st.markdown("<div class='sub-header'>Importa o exporta la base de datos</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📥 Importar desde CSV")
        st.info("Formato esperado: guest_name, ticket_number, total_amount, activity_date, provider, concierge, guest_arrival_date, signed, cargado, activity_time, meeting_point, adults, kids, room")
        uploaded_file = st.file_uploader("Selecciona tu archivo CSV", type=["csv"])
        if uploaded_file is not None:
            try:
                import_df = pd.read_csv(uploaded_file)
                st.write("Vista previa:")
                st.dataframe(import_df.head(), use_container_width=True)
                if st.button("📥 Importar", use_container_width=True):
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
                                "cargado": bool(int(row.get("cargado", 0))),
                                "activity_time": str(row.get("activity_time", "")).strip() if pd.notna(row.get("activity_time")) else None,
                                "meeting_point": str(row.get("meeting_point", "")).strip() if pd.notna(row.get("meeting_point")) else None,
                                "adults": int(row.get("adults", 0)) if pd.notna(row.get("adults")) and int(row.get("adults", 0)) > 0 else None,
                                "kids": int(row.get("kids", 0)) if pd.notna(row.get("kids")) and int(row.get("kids", 0)) > 0 else None,
                                "room": str(row.get("room", "")).strip().upper() if pd.notna(row.get("room")) and str(row.get("room", "")).strip() else None
                            }
                            success, _ = add_certificate(data)
                            if success:
                                imported += 1
                            else:
                                skipped += 1
                        except Exception as e:
                            skipped += 1
                    st.success(f"✅ {imported} registros importados. {skipped} omitidos.")
                    st.balloons()
            except Exception as e:
                st.error(f"❌ Error al leer el archivo: {e}")
    with col2:
        st.subheader("📤 Exportar a CSV")
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

# PAGINA: LIMPIAR POR MES
elif page == "🗑️ Limpiar por Mes":
    st.markdown("<div class='main-header'>Limpiar por Mes</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Descarga un backup y elimina registros antiguos por mes</div>", unsafe_allow_html=True)

    df_all = get_all_certificates()
    if df_all.empty:
        st.info("📭 No hay certificados registrados.")
    else:
        months = sorted(df_all["activity_date"].str[:7].unique().tolist(), reverse=True)

        st.subheader("📅 Selecciona el mes a limpiar")
        selected_month = st.selectbox("Mes", months)

        if selected_month:
            month_df = get_certificates_by_month(selected_month)

            if month_df.empty:
                st.warning(f"No hay registros para {selected_month}.")
            else:
                st.info(f"📋 **{len(month_df)} registros** encontrados para **{selected_month}**")

                # Show preview
                with st.expander("👁️ Vista previa de registros a eliminar"):
                    preview_df = month_df.copy()
                    if "total_amount" in preview_df.columns:
                        preview_df["total_amount"] = preview_df["total_amount"].apply(lambda x: f"${x:,.2f}")
                    st.dataframe(preview_df, use_container_width=True, hide_index=True)

                st.markdown("---")
                st.subheader("📥 Paso 1: Descargar Backup")
                month_csv = month_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label=f"⬇️ Descargar Backup {selected_month} (CSV)",
                    data=month_csv,
                    file_name=f"backup_{selected_month}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

                st.markdown("---")
                st.subheader("🗑️ Paso 2: Eliminar Registros")
                st.error("⚠️ **ATENCION**: Esta accion es IRREVERSIBLE. Asegurate de haber descargado el backup antes de continuar.")

                confirm = st.checkbox(f"Confirmo que quiero eliminar PERMANENTEMENTE los {len(month_df)} registros de {selected_month}")
                if confirm:
                    if st.button("🗑️ ELIMINAR MES PERMANENTEMENTE", use_container_width=True, type="primary"):
                        success, response = delete_certificates_by_month(selected_month)
                        if success:
                            st.success(f"✅ {len(month_df)} registros de {selected_month} eliminados correctamente!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"❌ Error al eliminar: {response}")

# PAGINA: CONFIGURACION
elif page == "⚙️ Configuracion":
    st.markdown("<div class='main-header'>Configuracion</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Informacion del sistema</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("### 🏨 Activity Certificates DB")
        st.caption("Sistema de gestion de certificados de actividades para el departamento de Concierge.")
        st.markdown("---")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("<p style='margin:0; font-size:0.75rem; color:#888; text-transform:uppercase;'>Desarrollado por</p>", unsafe_allow_html=True)
            st.markdown("<p style='margin:4px 0 0 0; font-size:1.3rem; font-weight:700; color:#fff;'>Fred Wayne</p>", unsafe_allow_html=True)
        with col2:
            st.markdown("<p style='margin:0; font-size:0.75rem; color:#888; text-transform:uppercase;'>Departamento</p>", unsafe_allow_html=True)
            st.markdown("<p style='margin:4px 0 0 0; font-size:1.3rem; font-weight:600; color:#ccc;'>Concierge</p>", unsafe_allow_html=True)
        with col3:
            st.markdown("<p style='margin:0; font-size:0.75rem; color:#888; text-transform:uppercase;'>Hotel</p>", unsafe_allow_html=True)
            st.markdown("<p style='margin:4px 0 0 0; font-size:1.3rem; font-weight:600; color:#ccc;'>Waldorf Astoria</p>", unsafe_allow_html=True)
        with col4:
            st.markdown("<p style='margin:0; font-size:0.75rem; color:#888; text-transform:uppercase;'>Ubicacion</p>", unsafe_allow_html=True)
            st.markdown("<p style='margin:4px 0 0 0; font-size:1.3rem; font-weight:600; color:#ccc;'>Punta Cacique, Costa Rica 🇨🇷</p>", unsafe_allow_html=True)

    st.markdown("---")
    st.caption("v1.0 | Activity Certificates DB |")

    st.subheader("🔌 Estado de Conexion")
    try:
        test = supabase.table("certificates").select("count", count="exact").limit(1).execute()
        st.success("✅ Conectado a Base de Datos correctamente")
        st.info("Tabla: certificates | Proyecto: Activity Certificates | Waldorf Astoria.")
    except Exception as e:
        st.error(f"❌ Error de conexion: {e}")

st.sidebar.markdown("---")
