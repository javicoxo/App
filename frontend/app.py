import csv
import io
from datetime import date, timedelta
from json import JSONDecodeError

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
        background: var(--accent-2);
        border: none;
        color: #ffffff;
        border-radius: 999px;
        padding: 0.45rem 1rem;
        font-weight: 600;
    }
    div[data-testid="stToggle"] input:checked + div {
        background-color: #22c55e !important;
    }
    div[data-testid="stToggle"] input:checked + div > div {
        background-color: #ffffff !important;
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
    "Programación",
    "Alimentos",
    "Perfil",
    "Generador",
    "Despensa y compra",
    "Consumo real",
]
if "section" not in st.session_state:
    st.session_state.section = "Programación"

st.markdown(
    """
    <div>
        <h1 class="page-title">Programación</h1>
        <p class="page-subtitle">Vista de los próximos 7 días con la dieta propuesta.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


def get(endpoint: str, params: dict | None = None):
    params_tuple = tuple(sorted((params or {}).items()))
    return cached_get(endpoint, params_tuple)


def post(endpoint: str, payload: dict):
    response = requests.post(f"{API_URL}{endpoint}", json=payload, timeout=10)
    st.cache_data.clear()
    return parse_response(response)


@st.cache_data(show_spinner=False, ttl=60)
def cached_get(endpoint: str, params_tuple: tuple[tuple[str, str], ...]):
    params = dict(params_tuple)
    response = requests.get(f"{API_URL}{endpoint}", params=params or None, timeout=10)
    return parse_response(response)


def parse_response(response: requests.Response) -> dict | list:
    if not response.content:
        return {}
    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type:
        return {}
    if not response.text.strip():
        return {}
    try:
        return response.json()
    except (JSONDecodeError, ValueError):
        return {}


def format_fecha(fecha: date) -> str:
    return fecha.strftime("%d/%m/%Y")


if st.session_state.section == "Programación":
    st.markdown("### Próximos 7 días")
    today = date.today()
    consulta_fecha = st.date_input(
        "Consultar día",
        value=today,
        min_value=date(today.year, 1, 1),
        max_value=date(today.year, 12, 31),
    )
    dias = get("/dias")
    perfil = get("/perfil")
    objetivos = {item["tipo"]: item for item in perfil.get("objetivos", [])}
    dias_por_fecha = {dia["fecha"]: dia for dia in dias}
    for offset in range(7):
        fecha = format_fecha(today + timedelta(days=offset))
        dia = dias_por_fecha.get(fecha)
        st.markdown(f"#### {fecha}")
        if not dia:
            st.info("Sin propuesta generada todavía.")
            continue
        comidas = get(f"/dias/{dia['id']}/comidas")
        items_totales: list[dict] = []
        menu_por_comida = []
        for comida in comidas:
            items = get(f"/comidas/{comida['id']}/items")
            items_totales.extend(items)
            menu_por_comida.append({"nombre": comida["nombre"], "items": items})
        if not items_totales:
            st.info("Sin items generados aún para este día.")
            continue
        objetivo = objetivos.get(dia.get("tipo", "Entreno"), {})
        kcal_total = sum(item["kcal"] for item in items_totales)
        proteina_total = sum(item["proteina"] for item in items_totales)
        hidratos_total = sum(item["hidratos"] for item in items_totales)
        grasas_total = sum(item["grasas"] for item in items_totales)
        kcal_obj = float(objetivo.get("kcal", 0) or 0)
        prot_obj = float(objetivo.get("proteina", 0) or 0)
        hidr_obj = float(objetivo.get("hidratos", 0) or 0)
        gras_obj = float(objetivo.get("grasas", 0) or 0)
        kpi_cols = st.columns(4)
        kpi_cols[0].metric("Kcal", f"{int(kcal_total)}")
        kpi_cols[1].metric("Proteínas (g)", f"{int(proteina_total)}")
        kpi_cols[2].metric("Hidratos (g)", f"{int(hidratos_total)}")
        kpi_cols[3].metric("Grasas (g)", f"{int(grasas_total)}")
        diff_cols = st.columns(4)
        diff_cols[0].metric("Δ Kcal", f"{int(kcal_total - kcal_obj)}")
        diff_cols[1].metric("Δ Prot", f"{int(proteina_total - prot_obj)}")
        diff_cols[2].metric("Δ Hidr", f"{int(hidratos_total - hidr_obj)}")
        diff_cols[3].metric("Δ Gras", f"{int(grasas_total - gras_obj)}")
        st.bar_chart(
            {
                "Kcal": kcal_total,
                "Proteínas (g)": proteina_total,
                "Hidratos (g)": hidratos_total,
                "Grasas (g)": grasas_total,
            }
        )
        for menu in menu_por_comida:
            st.markdown(f"**{menu['nombre']}**")
            st.dataframe(menu["items"])
        if st.button("Eliminar día", key=f"delete-dia-{fecha}"):
            requests.delete(f"{API_URL}/dias/{dia['id']}", timeout=10)
            st.cache_data.clear()
            st.rerun()
    st.markdown("### Consultar cualquier día")
    fecha_consulta = format_fecha(consulta_fecha)
    dia = dias_por_fecha.get(fecha_consulta)
    st.markdown(f"#### {fecha_consulta}")
    if not dia:
        st.info("Sin propuesta generada para este día.")
    else:
        comidas = get(f"/dias/{dia['id']}/comidas")
        items_totales: list[dict] = []
        menu_por_comida = []
        for comida in comidas:
            items = get(f"/comidas/{comida['id']}/items")
            items_totales.extend(items)
            menu_por_comida.append({"nombre": comida["nombre"], "items": items})
        if not items_totales:
            st.info("Sin items generados aún para este día.")
        else:
            objetivo = objetivos.get(dia.get("tipo", "Entreno"), {})
            kcal_total = sum(item["kcal"] for item in items_totales)
            proteina_total = sum(item["proteina"] for item in items_totales)
            hidratos_total = sum(item["hidratos"] for item in items_totales)
            grasas_total = sum(item["grasas"] for item in items_totales)
            kcal_obj = float(objetivo.get("kcal", 0) or 0)
            prot_obj = float(objetivo.get("proteina", 0) or 0)
            hidr_obj = float(objetivo.get("hidratos", 0) or 0)
            gras_obj = float(objetivo.get("grasas", 0) or 0)
            kpi_cols = st.columns(4)
            kpi_cols[0].metric("Kcal", f"{int(kcal_total)}")
            kpi_cols[1].metric("Proteínas (g)", f"{int(proteina_total)}")
            kpi_cols[2].metric("Hidratos (g)", f"{int(hidratos_total)}")
            kpi_cols[3].metric("Grasas (g)", f"{int(grasas_total)}")
            diff_cols = st.columns(4)
            diff_cols[0].metric("Δ Kcal", f"{int(kcal_total - kcal_obj)}")
            diff_cols[1].metric("Δ Prot", f"{int(proteina_total - prot_obj)}")
            diff_cols[2].metric("Δ Hidr", f"{int(hidratos_total - hidr_obj)}")
            diff_cols[3].metric("Δ Gras", f"{int(grasas_total - gras_obj)}")
            st.bar_chart(
                {
                    "Kcal": kcal_total,
                    "Proteínas (g)": proteina_total,
                    "Hidratos (g)": hidratos_total,
                    "Grasas (g)": grasas_total,
                }
            )
            for menu in menu_por_comida:
                st.markdown(f"**{menu['nombre']}**")
                st.dataframe(menu["items"])


elif st.session_state.section == "Perfil":
    st.subheader("Perfil de usuario")
    perfil = get("/perfil")
    objetivos_lista = perfil.get("objetivos", [])
    objetivos = {item["tipo"]: item for item in objetivos_lista}
    tipos = sorted(objetivos.keys())
    st.markdown("### Tipos de día disponibles")
    for tipo in tipos:
        row_cols = st.columns([3, 1])
        row_cols[0].markdown(f"**{tipo}**")
        if tipo not in {"Entreno", "Descanso"}:
            if row_cols[1].button("Eliminar", key=f"delete-tipo-{tipo}"):
                requests.delete(f"{API_URL}/perfil/objetivos/{tipo}", timeout=10)
                st.cache_data.clear()
                st.rerun()
    with st.form("perfil-form"):
        st.markdown("### Objetivos por tipo de día")
        tabs = st.tabs(tipos or ["Entreno", "Descanso"])
        objetivos_payload = []
        for tab, tipo in zip(tabs, tipos or ["Entreno", "Descanso"], strict=False):
            with tab:
                valores = objetivos.get(tipo, {})
                kcal_base = float(valores.get("kcal", 0))
                kcal = st.number_input(f"Kcal ({tipo})", value=kcal_base, step=10.0)
                if tipo == "Entreno":
                    pct_proteina, pct_hidratos, pct_grasas = 0.30, 0.50, 0.20
                elif tipo == "Descanso":
                    pct_proteina, pct_hidratos, pct_grasas = 0.35, 0.25, 0.40
                else:
                    base_proteina = float(valores.get("proteina", 0))
                    base_hidratos = float(valores.get("hidratos", 0))
                    base_grasas = float(valores.get("grasas", 0))
                    base_total = base_proteina * 4 + base_hidratos * 4 + base_grasas * 9
                    scale = kcal / base_total if base_total else 0
                    proteina = base_proteina * scale
                    hidratos = base_hidratos * scale
                    grasas = base_grasas * scale
                    pct_proteina = pct_hidratos = pct_grasas = None
                if pct_proteina is not None:
                    proteina = (kcal * pct_proteina) / 4 if kcal else 0
                    hidratos = (kcal * pct_hidratos) / 4 if kcal else 0
                    grasas = (kcal * pct_grasas) / 9 if kcal else 0
                st.caption(
                    f"Proteínas: {proteina:.1f} g · Hidratos: {hidratos:.1f} g · Grasas: {grasas:.1f} g"
                )
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
            json={"objetivos": objetivos_payload},
            timeout=10,
        )
        st.success("Perfil actualizado.")
    with st.form("nuevo-reparto-form"):
        st.markdown("### Nuevo tipo de día")
        nuevo_tipo = st.text_input("Nombre del tipo de día", placeholder="Ej: Competición")
        kcal_nuevo = st.number_input("Kcal objetivo", min_value=0.0, value=2000.0, step=10.0)
        pct_proteina = st.number_input("Proteínas (%)", min_value=0.0, max_value=100.0, value=25.0, step=1.0)
        pct_hidratos = st.number_input("Hidratos (%)", min_value=0.0, max_value=100.0, value=50.0, step=1.0)
        pct_grasas = st.number_input("Grasas (%)", min_value=0.0, max_value=100.0, value=25.0, step=1.0)
        crear_reparto = st.form_submit_button("Guardar")
    if crear_reparto:
        if not nuevo_tipo.strip():
            st.warning("Introduce un nombre para el nuevo tipo de día.")
            st.stop()
        proteina = (kcal_nuevo * (pct_proteina / 100)) / 4 if kcal_nuevo else 0
        hidratos = (kcal_nuevo * (pct_hidratos / 100)) / 4 if kcal_nuevo else 0
        grasas = (kcal_nuevo * (pct_grasas / 100)) / 9 if kcal_nuevo else 0
        requests.post(
            f"{API_URL}/perfil/objetivos",
            json={
                "tipo": nuevo_tipo,
                "kcal": kcal_nuevo,
                "proteina": proteina,
                "hidratos": hidratos,
                "grasas": grasas,
            },
            timeout=10,
        )
        st.cache_data.clear()
        st.success("Tipo de día guardado.")
        st.rerun()


elif st.session_state.section == "Alimentos":
    st.subheader("Gestión de alimentos")
    tabs = st.tabs(["Importar CSV", "Recetas", "Open Food Facts"])
    with tabs[0]:
        st.markdown("### Importar base de datos (CSV)")
        delimitador = st.text_input("Delimitador", value=",", max_chars=1)
        archivo = st.file_uploader("CSV de alimentos", type=["csv"])
        columnas_requeridas = [
            "nombre",
            "kcal_100g",
            "proteina_100g",
            "hidratos_100g",
            "grasas_100g",
            "rol_principal",
            "grupo_mediterraneo",
            "frecuencia_mediterranea",
            "permitido_comidas",
            "categorias",
        ]
        if archivo is not None:
            contenido = archivo.getvalue().decode("utf-8-sig")
            lector = csv.DictReader(io.StringIO(contenido), delimiter=delimitador)
            if not lector.fieldnames:
                st.error("El CSV no contiene cabeceras.")
            else:
                faltantes = [col for col in columnas_requeridas if col not in lector.fieldnames]
                if faltantes:
                    st.error(f"Faltan columnas requeridas: {', '.join(faltantes)}")
                else:
                    filas = list(lector)
                    st.dataframe(filas[:5])
                    if st.button("Importar alimentos"):
                        errores = 0
                        total = len(filas)
                        progreso = st.progress(0)
                        estado = st.empty()
                        batch_size = 25
                        exitos = 0
                        with requests.Session() as session:
                            for fila in filas:
                                try:
                                    payload = {
                                        "ean": fila.get("ean") or None,
                                        "nombre": fila["nombre"],
                                        "marca": fila.get("marca") or None,
                                        "kcal_100g": float(fila["kcal_100g"]),
                                        "proteina_100g": float(fila["proteina_100g"]),
                                        "hidratos_100g": float(fila["hidratos_100g"]),
                                        "grasas_100g": float(fila["grasas_100g"]),
                                        "rol_principal": fila["rol_principal"],
                                        "grupo_mediterraneo": fila["grupo_mediterraneo"],
                                        "frecuencia_mediterranea": fila["frecuencia_mediterranea"],
                                        "permitido_comidas": fila["permitido_comidas"],
                                        "categorias": fila["categorias"],
                                    }
                                    session.post(f"{API_URL}/alimentos", json=payload, timeout=30)
                                    exitos += 1
                                except (ValueError, KeyError, requests.RequestException):
                                    errores += 1
                                progreso.progress(min((exitos + errores) / total, 1.0))
                                if (exitos + errores) % batch_size == 0:
                                    estado.write(f"Procesadas: {exitos + errores}/{total}")
                        estado.write(f"Procesadas: {exitos + errores}/{total}")
                        st.success(f"Importación finalizada. Éxitos: {exitos}. Errores: {errores}.")
                        st.cache_data.clear()
    with tabs[1]:
        st.markdown("### Recetas propias")
        with st.form("recetas-form"):
            nombre = st.text_input("Nombre de la receta")
            ean = st.text_input("EAN (opcional)")
            marca = st.text_input("Marca (opcional)")
            kcal_100g = st.number_input("Kcal / 100g", min_value=0.0, step=1.0)
            proteina_100g = st.number_input("Proteínas / 100g", min_value=0.0, step=0.1)
            hidratos_100g = st.number_input("Hidratos / 100g", min_value=0.0, step=0.1)
            grasas_100g = st.number_input("Grasas / 100g", min_value=0.0, step=0.1)
            rol_principal = st.text_input("Rol nutricional")
            grupo_mediterraneo = st.text_input("Grupo mediterráneo")
            frecuencia_mediterranea = st.text_input("Frecuencia mediterránea")
            permitido_comidas = st.text_input("Comidas permitidas (separadas por coma)")
            categorias = st.text_input("Categorías")
            submit = st.form_submit_button("Guardar receta")
        if submit:
            if not nombre.strip():
                st.warning("El nombre es obligatorio.")
            else:
                post(
                    "/alimentos",
                    {
                        "ean": ean or None,
                        "nombre": nombre,
                        "marca": marca or None,
                        "kcal_100g": kcal_100g,
                        "proteina_100g": proteina_100g,
                        "hidratos_100g": hidratos_100g,
                        "grasas_100g": grasas_100g,
                        "rol_principal": rol_principal,
                        "grupo_mediterraneo": grupo_mediterraneo,
                        "frecuencia_mediterranea": frecuencia_mediterranea,
                        "permitido_comidas": permitido_comidas,
                        "categorias": categorias,
                    },
                )
                st.success("Receta guardada.")
                st.cache_data.clear()
    with tabs[2]:
        st.markdown("### Buscar en Open Food Facts")
        criterio = st.selectbox("Buscar por", ["Nombre", "EAN"])
        consulta = st.text_input("Consulta")
        if st.button("Buscar en Open Food Facts"):
            if not consulta.strip():
                st.warning("Introduce un valor de búsqueda.")
            elif criterio == "EAN":
                response = requests.get(
                    f"https://world.openfoodfacts.org/api/v2/product/{consulta.strip()}.json",
                    timeout=10,
                )
                data = response.json() if response.content else {}
                st.session_state.off_results = [data.get("product")] if data.get("product") else []
            else:
                response = requests.get(
                    "https://world.openfoodfacts.org/cgi/search.pl",
                    params={"search_terms": consulta.strip(), "search_simple": 1, "action": "process", "json": 1},
                    timeout=10,
                )
                data = response.json() if response.content else {}
                st.session_state.off_results = data.get("products", [])[:10]
        productos = st.session_state.get("off_results", [])
        if productos:
            opciones = []
            for producto in productos:
                nombre_prod = (
                    producto.get("product_name")
                    or producto.get("product_name_es")
                    or producto.get("product_name_en")
                    or "Sin nombre"
                )
                opciones.append(f"{nombre_prod} ({producto.get('code', 'sin EAN')})")
            seleccion = st.selectbox("Selecciona un producto", opciones)
            indice = opciones.index(seleccion)
            producto = productos[indice]
            nutriments = producto.get("nutriments", {})
            kcal = nutriments.get("energy-kcal_100g")
            if kcal is None and nutriments.get("energy_100g"):
                kcal = float(nutriments.get("energy_100g")) / 4.184
            kcal = float(kcal or 0)
            with st.form("off-import"):
                st.markdown("### Importar alimento")
                nombre = st.text_input(
                    "Nombre",
                    value=producto.get("product_name") or producto.get("product_name_es") or "",
                )
                ean = st.text_input("EAN", value=str(producto.get("code") or ""))
                marca = st.text_input("Marca", value=producto.get("brands") or "")
                kcal_100g = st.number_input("Kcal / 100g", min_value=0.0, value=float(kcal), step=1.0)
                proteina_100g = st.number_input(
                    "Proteínas / 100g", min_value=0.0, value=float(nutriments.get("proteins_100g") or 0), step=0.1
                )
                hidratos_100g = st.number_input(
                    "Hidratos / 100g",
                    min_value=0.0,
                    value=float(nutriments.get("carbohydrates_100g") or 0),
                    step=0.1,
                )
                grasas_100g = st.number_input(
                    "Grasas / 100g", min_value=0.0, value=float(nutriments.get("fat_100g") or 0), step=0.1
                )
                rol_principal = st.text_input("Rol nutricional")
                grupo_mediterraneo = st.text_input("Grupo mediterráneo")
                frecuencia_mediterranea = st.text_input("Frecuencia mediterránea")
                permitido_comidas = st.text_input("Comidas permitidas (separadas por coma)")
                categorias = st.text_input("Categorías")
                submit = st.form_submit_button("Importar alimento")
            if submit:
                if not nombre.strip():
                    st.warning("El nombre es obligatorio.")
                else:
                    post(
                        "/alimentos",
                        {
                            "ean": ean or None,
                            "nombre": nombre,
                            "marca": marca or None,
                            "kcal_100g": kcal_100g,
                            "proteina_100g": proteina_100g,
                            "hidratos_100g": hidratos_100g,
                            "grasas_100g": grasas_100g,
                            "rol_principal": rol_principal,
                            "grupo_mediterraneo": grupo_mediterraneo,
                            "frecuencia_mediterranea": frecuencia_mediterranea,
                            "permitido_comidas": permitido_comidas,
                            "categorias": categorias,
                        },
                    )
                    st.success("Alimento importado.")
                    st.cache_data.clear()


elif st.session_state.section == "Generador":
    st.subheader("Generar menú")
    with st.form("crear-dia-generador"):
        fecha = st.date_input("Fecha")
        tipo = st.selectbox("Tipo de día", ["Entreno", "Descanso"])
        submit = st.form_submit_button("Crear y generar menú")
    if submit:
        payload = {"fecha": format_fecha(fecha), "tipo": tipo}
        dia = post("/dias", payload)
        dia_id = dia.get("id")
        if dia_id:
            post("/generador", {"dia_id": dia_id})
            st.success("Menú generado.")
            st.cache_data.clear()
            st.session_state.last_generated_day = dia_id
            st.rerun()
        else:
            st.error("No se pudo crear el día.")
    dias = get("/dias")
    if dias:
        dia_id = st.session_state.get("last_generated_day", dias[-1]["id"])
        if st.button("Regenerar menú completo"):
            post("/generador", {"dia_id": dia_id})
            st.success("Menú regenerado.")
            st.cache_data.clear()
            st.rerun()
        comidas = get(f"/dias/{dia_id}/comidas")
        for comida in comidas:
            st.markdown(f"### {comida['nombre']}")
            items = get(f"/comidas/{comida['id']}/items")
            st.dataframe(items)
    else:
        st.info("Crea un día antes de generar.")


elif st.session_state.section == "Despensa y compra":
    st.subheader("Despensa y lista de la compra")
    tabs = st.tabs(["Despensa", "Lista de la compra"])
    with tabs[0]:
        st.markdown("### Añadir alimento manual")
        with st.form("despensa-manual"):
            ean_manual = st.text_input("EAN (opcional)")
            nombre_manual = st.text_input("Nombre del alimento")
            estado_manual = st.selectbox("Estado", ["disponible", "agotado"])
            submit_despensa = st.form_submit_button("Guardar")
        if submit_despensa:
            if not nombre_manual.strip():
                st.warning("El nombre es obligatorio.")
            else:
                requests.post(
                    f"{API_URL}/despensa",
                    json={"ean": ean_manual or None, "nombre": nombre_manual, "estado": estado_manual},
                    timeout=10,
                )
                st.cache_data.clear()
                st.success("Despensa actualizada.")
                st.rerun()
        st.markdown("### Disponibles")
        st.dataframe(get("/despensa", {"estado": "disponible"}))
        st.markdown("### Agotados")
        st.dataframe(get("/despensa", {"estado": "agotado"}))
    with tabs[1]:
        st.markdown("### Lista automática")
        rango = st.selectbox("Cobertura", ["7 días", "Hoy"])
        rango_dias = 7 if rango == "7 días" else 1
        lista = get("/lista-compra/auto", {"rango_dias": rango_dias})
        if not lista:
            st.info("No hay faltantes detectados.")
        else:
            for item in lista:
                cols = st.columns([4, 2, 2])
                nombre = item.get("nombre", "")
                gramos = item.get("gramos", 0)
                cols[0].markdown(f"**{nombre}**")
                cols[1].markdown(f"{gramos:.0f} g")
                if cols[2].button("Marcar comprado", key=f"comprar-{item.get('ean')}-{nombre}"):
                    requests.post(
                        f"{API_URL}/despensa",
                        json={"ean": item.get("ean"), "nombre": nombre, "estado": "disponible"},
                        timeout=10,
                    )
                    st.cache_data.clear()
                    st.rerun()


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
