import requests
import streamlit as st


API_URL = "http://localhost:8000"


st.set_page_config(page_title="BeFitLab", layout="wide")
st.title("BeFitLab — nutrición inteligente")


section = st.sidebar.radio(
    "Navegación",
    [
        "Días y comidas",
        "Generador",
        "Despensa",
        "Lista de la compra",
        "Estadísticas",
        "Consumo real",
    ],
)


def get(endpoint: str, params: dict | None = None):
    return requests.get(f"{API_URL}{endpoint}", params=params, timeout=10).json()


def post(endpoint: str, payload: dict):
    return requests.post(f"{API_URL}{endpoint}", json=payload, timeout=10).json()


if section == "Días y comidas":
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
