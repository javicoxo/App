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
        background: var(--panel);
        border-right: 1px solid #e2e8f0;
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


st.sidebar.markdown('<div class="sidebar-title">BeFitLab</div>', unsafe_allow_html=True)
section = st.sidebar.radio(
    "Main",
    [
        "Dashboard",
        "Días y comidas",
        "Generador",
        "Despensa",
        "Lista de la compra",
        "Estadísticas",
        "Consumo real",
    ],
)

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


if section == "Dashboard":
    left, right = st.columns([2, 1], gap="large")
    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Resumen diario")
        dias = get("/dias")
        if dias:
            dia_id = st.selectbox("Selecciona día", [dia["id"] for dia in dias], key="dashboard-dia")
            stats = get(f"/estadisticas/{dia_id}")
            st.markdown(
                """
                <div class="kpi-grid">
                    <div class="kpi"><span>Kcal objetivo</span><strong>{kcal_obj}</strong></div>
                    <div class="kpi"><span>Proteínas objetivo</span><strong>{prot_obj} g</strong></div>
                    <div class="kpi"><span>Hidratos objetivo</span><strong>{hid_obj} g</strong></div>
                </div>
                """.format(
                    kcal_obj=stats["objetivo"]["kcal"],
                    prot_obj=stats["objetivo"]["proteina"],
                    hid_obj=stats["objetivo"]["hidratos"],
                ),
                unsafe_allow_html=True,
            )
            st.markdown(
                """
                <div class="kpi-grid">
                    <div class="kpi"><span>Consumido</span><strong>{kcal} kcal</strong></div>
                    <div class="kpi"><span>Proteínas</span><strong>{prot} g</strong></div>
                    <div class="kpi"><span>Grasas</span><strong>{gras} g</strong></div>
                </div>
                """.format(
                    kcal=int(stats["consumo"]["kcal"]),
                    prot=int(stats["consumo"]["proteina"]),
                    gras=int(stats["consumo"]["grasas"]),
                ),
                unsafe_allow_html=True,
            )
        else:
            st.info("Crea un día para ver el resumen.")
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Atajos rápidos")
        st.markdown('<span class="chip">Generador inteligente</span>', unsafe_allow_html=True)
        if st.button("Generar menú"):
            dias = get("/dias")
            if dias:
                post("/generador", {"dia_id": dias[-1]["id"]})
                st.success("Menú generado para el último día.")
        st.markdown("---")
        st.markdown("### Lista de la compra")
        st.dataframe(get("/lista-compra"), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


elif section == "Días y comidas":
    st.subheader("Crear día")
    with st.form("crear-dia"):
        fecha = st.text_input("Fecha (YYYY-MM-DD)")
        tipo = st.selectbox("Tipo de día", ["Entreno", "Descanso"])
        submitted = st.form_submit_button("Crear día")
    if submitted:
        post("/dias", {"fecha": fecha, "tipo": tipo})
        st.success("Día creado con sus comidas.")
    st.subheader("Días existentes")
    st.dataframe(get("/dias"))


elif section == "Generador":
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


elif section == "Despensa":
    st.subheader("Despensa disponible")
    st.dataframe(get("/despensa", {"estado": "disponible"}))
    st.subheader("Despensa agotada")
    st.dataframe(get("/despensa", {"estado": "agotado"}))


elif section == "Lista de la compra":
    st.subheader("Lista automática")
    st.dataframe(get("/lista-compra"))


elif section == "Estadísticas":
    st.subheader("Resumen diario")
    dias = get("/dias")
    if dias:
        dia_id = st.selectbox("Selecciona día", [dia["id"] for dia in dias])
        stats = get(f"/estadisticas/{dia_id}")
        st.json(stats)
    else:
        st.info("Crea un día para ver estadísticas.")


elif section == "Consumo real":
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
