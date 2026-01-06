import random

from ..crud import (
    add_lista_compra,
    list_alimentos,
    list_despensa,
    list_comida_items,
    update_comida_item,
    update_comida_item_detalle,
)


MEAL_ORDER = [
    "Desayuno",
    "Media mañana",
    "Almuerzo",
    "Merienda",
    "Cena",
]


POSTRE_VALIDO = {"lácteos", "fruta", "cereales", "frutos secos"}


def objetivos_por_tipo(tipo: str) -> dict:
    if tipo == "Entreno":
        return {"kcal": 2400, "proteina": 150, "hidratos": 260, "grasas": 70}
    return {"kcal": 2000, "proteina": 140, "hidratos": 180, "grasas": 90}


def _alimentos_por_rol(rol: str) -> list[dict]:
    return [alimento for alimento in list_alimentos() if rol in alimento["rol_principal"]]


def _despensa_disponible() -> set[str]:
    disponibles = list_despensa("disponible")
    return {item["ean"] for item in disponibles if item["ean"]}


def _seleccionar_alimento(rol: str, comida: str) -> dict | None:
    candidatos = [
        alimento
        for alimento in _alimentos_por_rol(rol)
        if comida in alimento["permitido_comidas"]
    ]
    return random.choice(candidatos) if candidatos else None


def _calcular_gramos(alimento: dict, macros_objetivo: dict) -> dict:
    gramos = 120
    factor = gramos / 100
    return {
        "gramos": gramos,
        "kcal": alimento["kcal_100g"] * factor,
        "proteina": alimento["proteina_100g"] * factor,
        "hidratos": alimento["hidratos_100g"] * factor,
        "grasas": alimento["grasas_100g"] * factor,
        "macros_objetivo": macros_objetivo,
    }


def generar_comida(comida: str, macros_objetivo: dict) -> list[dict]:
    items = []
    for rol in ("proteina", "hidrato", "grasa"):
        alimento = _seleccionar_alimento(rol, comida)
        if alimento:
            gramos_data = _calcular_gramos(alimento, macros_objetivo)
            items.append(
                {
                    "ean": alimento["ean"],
                    "nombre": alimento["nombre"],
                    "rol_principal": rol,
                    **{k: gramos_data[k] for k in ("gramos", "kcal", "proteina", "hidratos", "grasas")},
                }
            )
    if comida in {"Almuerzo", "Cena"}:
        postre = _seleccionar_postre(comida)
        if postre:
            gramos_data = _calcular_gramos(postre, macros_objetivo)
            items.append(
                {
                    "ean": postre["ean"],
                    "nombre": postre["nombre"],
                    "rol_principal": postre["rol_principal"],
                    **{k: gramos_data[k] for k in ("gramos", "kcal", "proteina", "hidratos", "grasas")},
                }
            )
    return items


def _seleccionar_postre(comida: str) -> dict | None:
    candidatos = [
        alimento
        for alimento in list_alimentos()
        if alimento["grupo_mediterraneo"].lower() in POSTRE_VALIDO
        and comida in alimento["permitido_comidas"]
    ]
    return random.choice(candidatos) if candidatos else None


def registrar_faltantes(items: list[dict]) -> None:
    disponibles = _despensa_disponible()
    for item in items:
        if item.get("ean") and item["ean"] not in disponibles:
            add_lista_compra(item["ean"], item["nombre"])


def sustituir_item(item: dict) -> dict | None:
    candidatos = [
        alimento
        for alimento in _alimentos_por_rol(item["rol_principal"])
        if alimento["ean"] != item.get("ean")
    ]
    if not candidatos:
        return None
    nuevo = random.choice(candidatos)
    gramos = item["gramos"]
    factor = gramos / 100
    detalle = {
        "ean": nuevo["ean"],
        "nombre": nuevo["nombre"],
        "gramos": gramos,
        "kcal": nuevo["kcal_100g"] * factor,
        "proteina": nuevo["proteina_100g"] * factor,
        "hidratos": nuevo["hidratos_100g"] * factor,
        "grasas": nuevo["grasas_100g"] * factor,
        "rol_principal": item["rol_principal"],
        "gramos_iniciales": item["gramos_iniciales"],
    }
    update_comida_item_detalle(item["id"], detalle)
    return detalle


def recalcular_por_golosina(comida_id: int, golosina_macros: dict) -> None:
    items = list_comida_items(comida_id)
    normales = [item for item in items if not item["es_golosina"]]
    if not normales:
        return
    for item in normales:
        gramos_nuevo = max(item["gramos_iniciales"] - golosina_macros["gramos"], 1)
        ratio = gramos_nuevo / item["gramos"] if item["gramos"] else 1
        macros = {
            "kcal": item["kcal"] * ratio,
            "proteina": item["proteina"] * ratio,
            "hidratos": item["hidratos"] * ratio,
            "grasas": item["grasas"] * ratio,
        }
        update_comida_item(item["id"], gramos_nuevo, macros)
