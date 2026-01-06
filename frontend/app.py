import calendar
from datetime import date

import requests
import streamlit as st


API_URL = "http://localhost:8000"


st.set_page_config(page_title="BeFitLab", layout="wide")
st.markdown(
    """
    <style>
    :root {
        --bg: #f7f8fb;
        --panel: #ffffff;
        --panel-2: #f1f4f9;
        --accent: #2563eb;
        --accent-2: #10b981;
        --text: #0f172a;
        --muted: #64748b;
    }
    html, body, [class*="stApp"] {
        background-color: var(--bg);
        color: var(--text);
        font-family: "Inter", "Segoe UI", sans-serif;
    }
    header, footer {visibility: hidden;}
    section[data-testid="stSidebar"] {
        display: none;
    }
    [data-testid="stAppViewContainer"] {
        margin-left: 0;
    }
    .sidebar-title {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: var(--text);
    }
    .page-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
    }
    .page-subtitle {
        color: var(--muted);
        margin-top: 0.3rem;
    }
    .card {
        background: var(--panel);
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 1.25rem;
        box-shadow: 0 16px 32px rgba(15, 23, 42, 0.08);
    }
    .card h3, .card h4 {
        margin-top: 0;
        color: var(--text);
    }
    .chip {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.3rem 0.6rem;
        border-radius: 999px;
        background: rgba(37, 99, 235, 0.12);
        color: var(--accent);
        font-size: 0.8rem;
    }
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
    }
    .kpi {
        background: var(--panel-2);
        border-radius: 14px;
        padding: 0.9rem 1rem;
        border: 1px solid #e2e8f0;
    }
    .kpi span {
        color: var(--muted);
        font-size: 0.85rem;
    }
    .kpi strong {
        display: block;
        font-size: 1.2rem;
        margin-top: 0.2rem;
    }
    .stButton > button {
        background: linear-gradient(90deg, var(--accent) 0%, var(--accent-2) 100%);
        border: none;
        color: #ffffff;
        border-radius: 999px;
        padding: 0.45rem 1rem;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        background: var(--panel);
        border-radius: 999px;
        color: var(--muted);
        padding: 0.4rem 1rem;
        border: 1px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: var(--text);
        border-color: var(--accent);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


SECTIONS = [
    "Dashboard",
    "Perfil",
    "Días y comidas",
    "Generador",
    "Despensa",
    "Lista de la compra",
    "Estadísticas",
    "Consumo real",
]
if "section" not in st.session_state:
    st.session_state.section = "Dashboard"

st.markdown(
    """
    <div>
        <h1 class="page-title">Dashboard</h1>
        <p class="page-subtitle">Planificación diaria, control de macros y hábitos sostenibles.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


def get(endpoint: str, params: dict | None = None):
    return requests.get(f"{API_URL}{endpoint}", params=params, timeout=10).json()


def post(endpoint: str, payload: dict):
    return requests.post(f"{API_URL}{endpoint}", json=payload, timeout=10).json()


def format_fecha(fecha: date) -> str:
    return fecha.strftime("%d/%m/%Y")


if st.session_state.section == "Dashboard":
    st.markdown("### Calendario mensual")
    today = date.today()
    month_matrix = calendar.monthcalendar(today.year, today.month)
    dias = get("/dias")
    dias_por_fecha = {dia["fecha"]: dia for dia in dias}
    week_headers = ["L", "M", "X", "J", "V", "S", "D"]
    header_cols = st.columns(7)
    for idx, header in enumerate(week_headers):
        header_cols[idx].markdown(f"**{header}**")
    for week in month_matrix:
        day_cols = st.columns(7)
        for idx, day_num in enumerate(week):
            if day_num == 0:
                day_cols[idx].markdown(" ")
                continue
            fecha = format_fecha(date(today.year, today.month, day_num))
            dia = dias_por_fecha.get(fecha)
            tipo_actual = dia["tipo"] if dia else "Descanso"
            is_entreno = tipo_actual == "Entreno"
            with day_cols[idx]:
                st.markdown(f"**{day_num}**")
                toggle_key = f"entreno-{fecha}"
                toggle_label = "🏋️" if is_entreno else "💤"
                entreno = st.toggle(
                    toggle_label,
                    value=is_entreno,
                    key=toggle_key,
                )
                if entreno != is_entreno:
                    if dia:
                        post_payload = {"fecha": fecha, "tipo": "Entreno" if entreno else "Descanso"}
                        requests.put(f"{API_URL}/dias/{dia['id']}", json=post_payload, timeout=10)
                    else:
                        post("/dias", {"fecha": fecha, "tipo": "Entreno" if entreno else "Descanso"})
                    st.rerun()
                if dia:
                    comidas = get(f"/dias/{dia['id']}/comidas")
                    almuerzo = next((c for c in comidas if c["nombre"] == "Almuerzo"), None)
                    cena = next((c for c in comidas if c["nombre"] == "Cena"), None)
                    if almuerzo:
                        items = get(f"/comidas/{almuerzo['id']}/items")
                        kcal = sum(item["kcal"] for item in items)
                        st.caption(f"Almuerzo: {len(items)} items · {int(kcal)} kcal")
                    if cena:
                        items = get(f"/comidas/{cena['id']}/items")
                        kcal = sum(item["kcal"] for item in items)
                        st.caption(f"Cena: {len(items)} items · {int(kcal)} kcal")


elif st.session_state.section == "Perfil":
    st.subheader("Perfil de usuario")
    perfil = get("/perfil")
    default_tipo = perfil.get("default_tipo", "Descanso")
    objetivos = {item["tipo"]: item for item in perfil.get("objetivos", [])}
    with st.form("perfil-form"):
        st.markdown("### Tipo de día por defecto")
        tipo_default = st.selectbox("Nuevo día:", ["Entreno", "Descanso"], index=0 if default_tipo == "Entreno" else 1)
        st.markdown("### Objetivos por tipo de día")
        tabs = st.tabs(["Entreno", "Descanso"])
        objetivos_payload = []
        for tab, tipo in zip(tabs, ["Entreno", "Descanso"], strict=False):
            with tab:
                valores = objetivos.get(tipo, {})
                kcal = st.number_input(f"Kcal ({tipo})", value=float(valores.get("kcal", 0)), step=10.0)
                proteina = st.number_input(f"Proteínas g ({tipo})", value=float(valores.get("proteina", 0)), step=1.0)
                hidratos = st.number_input(f"Hidratos g ({tipo})", value=float(valores.get("hidratos", 0)), step=1.0)
                grasas = st.number_input(f"Grasas g ({tipo})", value=float(valores.get("grasas", 0)), step=1.0)
                objetivos_payload.append(
                    {
                        "tipo": tipo,
                        "kcal": kcal,
                        "proteina": proteina,
                        "hidratos": hidratos,
                        "grasas": grasas,
                    }
                )
        submitted = st.form_submit_button("Guardar perfil")
    if submitted:
        requests.put(
            f"{API_URL}/perfil",
            json={"default_tipo": tipo_default, "objetivos": objetivos_payload},
            timeout=10,
        )
        st.success("Perfil actualizado.")


elif st.session_state.section == "Días y comidas":
    st.subheader("Crear día")
    perfil = get("/perfil")
    default_tipo = perfil.get("default_tipo", "Descanso")
    with st.form("crear-dia"):
        fecha = st.text_input("Fecha (DD/MM/AAAA)")
        tipo = st.selectbox(
            "Tipo de día",
            ["Entreno", "Descanso"],
            index=0 if default_tipo == "Entreno" else 1,
        )
        submitted = st.form_submit_button("Crear día")
    if submitted:
        post("/dias", {"fecha": fecha, "tipo": tipo})
        st.success("Día creado con sus comidas.")
    st.subheader("Días existentes")
    st.dataframe(get("/dias"))


elif st.session_state.section == "Generador":
    st.subheader("Generar menú")
    dias = get("/dias")
    if dias:
        dia_id = st.selectbox("Selecciona día", [dia["id"] for dia in dias])
        if st.button("Generar menú completo"):
            post("/generador", {"dia_id": dia_id})
            st.success("Menú generado.")
        comidas = get(f"/dias/{dia_id}/comidas")
        for comida in comidas:
            st.markdown(f"### {comida['nombre']}")
            items = get(f"/comidas/{comida['id']}/items")
            st.dataframe(items)
    else:
        st.info("Crea un día antes de generar.")


elif st.session_state.section == "Despensa":
    st.subheader("Despensa disponible")
    st.dataframe(get("/despensa", {"estado": "disponible"}))
    st.subheader("Despensa agotada")
    st.dataframe(get("/despensa", {"estado": "agotado"}))


elif st.session_state.section == "Lista de la compra":
    st.subheader("Lista automática")
    st.dataframe(get("/lista-compra"))


elif st.session_state.section == "Estadísticas":
    st.subheader("Resumen diario")
    dias = get("/dias")
    if dias:
        dia_id = st.selectbox("Selecciona día", [dia["id"] for dia in dias])
        stats = get(f"/estadisticas/{dia_id}")
        st.json(stats)
    else:
        st.info("Crea un día para ver estadísticas.")


elif st.session_state.section == "Consumo real":
    st.subheader("Confirmar consumo")
    dias = get("/dias")
    if dias:
        dia_id = st.selectbox("Selecciona día", [dia["id"] for dia in dias])
        comidas = get(f"/dias/{dia_id}/comidas")
        for comida in comidas:
            st.markdown(f"### {comida['nombre']}")
            items = get(f"/comidas/{comida['id']}/items")
            for item in items:
                with st.form(f"consumo-{item['id']}"):
                    estado = st.selectbox(
                        "Estado",
                        ["aceptado", "rechazado", "modificado"],
                        key=f"estado-{item['id']}",
                    )
                    gramos = st.number_input(
                        "Gramos consumidos",
                        value=float(item["gramos"]),
                        key=f"gramos-{item['id']}",
                    )
                    submit = st.form_submit_button("Registrar")
                if submit:
                    post("/consumo", {"comida_item_id": item["id"], "estado": estado, "gramos": gramos})
                    st.success("Registro guardado.")
    else:
        st.info("Crea un día antes de registrar consumo.")


st.markdown("---")
nav_cols = st.columns(len(SECTIONS))
for idx, name in enumerate(SECTIONS):
    if nav_cols[idx].button(name, use_container_width=True):
        st.session_state.section = name
        st.rerun()
