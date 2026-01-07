import random

from ..crud import (
    add_lista_compra,
    get_objetivo,
    list_alimentos,
    list_comida_items,
    list_despensa,
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


POSTRE_VALIDO = {"lácteos", "fruta", "otros", "chocolate", "chocolate negro"}

MEAL_WEIGHTS = {
    "Desayuno": 0.22,
    "Media mañana": 0.14,
    "Almuerzo": 0.28,
    "Merienda": 0.10,
    "Cena": 0.26,
}


def objetivos_por_tipo(tipo: str) -> dict:
    objetivo = get_objetivo(tipo)
    return {
        "kcal": objetivo["kcal"],
        "proteina": objetivo["proteina"],
        "hidratos": objetivo["hidratos"],
        "grasas": objetivo["grasas"],
    }


def _alimentos_por_rol(rol: str) -> list[dict]:
    alimentos = list_alimentos()
    rol_lower = rol.lower()
    candidatos = []
    for alimento in alimentos:
        rol_principal = str(alimento.get("rol_principal", "")).lower()
        if rol_lower in rol_principal:
            candidatos.append(alimento)
    return candidatos or alimentos


def _despensa_disponible() -> set[str]:
    disponibles = list_despensa("disponible")
    return {item["ean"] for item in disponibles if item["ean"]}


def _permitido_para_comida(alimento: dict, comida: str) -> bool:
    permitido = str(alimento.get("permitido_comidas", ""))
    if not permitido:
        return True
    permitidos = {item.strip().lower() for item in permitido.replace(";", ",").split(",")}
    return comida.lower() in permitidos


def _es_cereal_o_pan(alimento: dict) -> bool:
    categorias = alimento.get("categorias", "").lower()
    grupo = alimento.get("grupo_mediterraneo", "").lower()
    return "cereal" in categorias or "pan" in categorias or "cereal" in grupo or "pan" in grupo


def _es_lacteo(alimento: dict) -> bool:
    grupo = alimento.get("grupo_mediterraneo", "").lower()
    categorias = alimento.get("categorias", "").lower()
    return "lácte" in grupo or "lacte" in grupo or "lácte" in categorias or "lacte" in categorias


def _es_fruta(alimento: dict) -> bool:
    grupo = alimento.get("grupo_mediterraneo", "").lower()
    categorias = alimento.get("categorias", "").lower()
    return "fruta" in grupo or "fruta" in categorias


def _es_huevo(alimento: dict) -> bool:
    categorias = alimento.get("categorias", "").lower()
    nombre = alimento.get("nombre", "").lower()
    return "huevo" in categorias or "huevo" in nombre


def _es_embutido(alimento: dict) -> bool:
    categorias = alimento.get("categorias", "").lower()
    return "embutido" in categorias


def _candidatos_desayuno_snack(comida: str) -> list[dict]:
    candidatos = []
    for alimento in list_alimentos():
        if not _permitido_para_comida(alimento, comida):
            continue
        if (
            _es_lacteo(alimento)
            or _es_fruta(alimento)
            or _es_cereal_o_pan(alimento)
            or _es_huevo(alimento)
            or _es_embutido(alimento)
            or "proteina" in str(alimento.get("rol_principal", "")).lower()
        ):
            candidatos.append(alimento)
    return candidatos


def _seleccionar_alimento(
    rol: str,
    comida: str,
    requiere_cereal: bool = False,
    evita_cereal: bool = False,
    macro_requerido: str | None = None,
) -> dict | None:
    candidatos = []
    for alimento in _alimentos_por_rol(rol):
        if not _permitido_para_comida(alimento, comida):
            continue
        if requiere_cereal and not _es_cereal_o_pan(alimento):
            continue
        if evita_cereal and _es_cereal_o_pan(alimento):
            continue
        if macro_requerido and alimento.get(f"{macro_requerido}_100g", 0) <= 0:
            continue
        candidatos.append(alimento)
    if not candidatos:
        return None
    disponibles = _despensa_disponible()
    en_despensa = [item for item in candidatos if item.get("ean") in disponibles]
    if en_despensa:
        return random.choice(en_despensa)
    return random.choice(candidatos)


def _calcular_gramos(alimento: dict, gramos: float) -> dict:
    factor = gramos / 100
    return {
        "gramos": gramos,
        "kcal": alimento["kcal_100g"] * factor,
        "proteina": alimento["proteina_100g"] * factor,
        "hidratos": alimento["hidratos_100g"] * factor,
        "grasas": alimento["grasas_100g"] * factor,
    }

def _gramos_para_macro(alimento: dict, macro: str, objetivo: float) -> float:
    valor = alimento.get(f"{macro}_100g", 0)
    if valor <= 0:
        return 0
    return max((objetivo / valor) * 100, 1)


def _gramos_para_kcal(alimento: dict, kcal_objetivo: float) -> float:
    kcal_100g = alimento.get("kcal_100g", 0)
    if kcal_100g <= 0:
        return 0
    return max((kcal_objetivo / kcal_100g) * 100, 1)


def _seleccionar_postre(comida: str) -> dict | None:
    candidatos = [
        alimento
        for alimento in list_alimentos()
        if alimento["grupo_mediterraneo"].lower() in POSTRE_VALIDO
        and _permitido_para_comida(alimento, comida)
    ]
    return random.choice(candidatos) if candidatos else None


def _objetivos_por_comida(objetivo: dict) -> dict[str, dict]:
    proteina_por_comida = min(max(objetivo["proteina"] / 5, 20), 35)
    proteina_total = proteina_por_comida * 5
    kcal_restantes = max(objetivo["kcal"] - proteina_total * 4, 0)
    kcal_carbs = objetivo["hidratos"] * 4
    kcal_grasas = objetivo["grasas"] * 9
    total_reparto = kcal_carbs + kcal_grasas
    if total_reparto <= 0:
        kcal_carbs = kcal_restantes / 2
        kcal_grasas = kcal_restantes / 2
    else:
        kcal_carbs = kcal_restantes * (kcal_carbs / total_reparto)
        kcal_grasas = kcal_restantes * (kcal_grasas / total_reparto)
    hidratos_total = kcal_carbs / 4 if kcal_carbs else 0
    grasas_total = kcal_grasas / 9 if kcal_grasas else 0
    objetivos_comidas = {}
    for comida in MEAL_ORDER:
        peso = MEAL_WEIGHTS[comida]
        objetivos_comidas[comida] = {
            "proteina": proteina_por_comida,
            "hidratos": hidratos_total * peso,
            "grasas": grasas_total * peso,
        }
    return objetivos_comidas


def _generar_items_comida(comida: str, objetivo: dict) -> list[dict]:
    items = []
    if comida in {"Desayuno", "Media mañana", "Merienda"}:
        candidatos = _candidatos_desayuno_snack(comida)
        if not candidatos:
            return items
        proteina = _seleccionar_alimento("proteina", comida, macro_requerido="proteina")
        if proteina and proteina in candidatos:
            grams = _gramos_para_macro(proteina, "proteina", objetivo["proteina"])
            if grams > 0:
                macros = _calcular_gramos(proteina, grams)
                items.append(
                    {
                        "ean": proteina["ean"],
                        "nombre": proteina["nombre"],
                        "rol_principal": "proteina",
                        **{k: macros[k] for k in ("gramos", "kcal", "proteina", "hidratos", "grasas")},
                    }
                )
                candidatos = [item for item in candidatos if item.get("ean") != proteina.get("ean")]
        if candidatos:
            extra = random.choice(candidatos)
            gramos = _gramos_para_macro(extra, "hidratos", objetivo["hidratos"]) or _gramos_para_kcal(extra, 150)
            if gramos > 0:
                macros = _calcular_gramos(extra, gramos)
                items.append(
                    {
                        "ean": extra["ean"],
                        "nombre": extra["nombre"],
                        "rol_principal": extra.get("rol_principal", "extra"),
                        **{k: macros[k] for k in ("gramos", "kcal", "proteina", "hidratos", "grasas")},
                    }
                )
                candidatos = [item for item in candidatos if item.get("ean") != extra.get("ean")]
        if len(items) < 2 and candidatos:
            extra = random.choice(candidatos)
            gramos = _gramos_para_kcal(extra, 120)
            if gramos > 0:
                macros = _calcular_gramos(extra, gramos)
                items.append(
                    {
                        "ean": extra["ean"],
                        "nombre": extra["nombre"],
                        "rol_principal": extra.get("rol_principal", "extra"),
                        **{k: macros[k] for k in ("gramos", "kcal", "proteina", "hidratos", "grasas")},
                    }
                )
        if len(items) < 2:
            fallback = random.choice(list_alimentos()) if list_alimentos() else None
            if fallback:
                gramos = _gramos_para_kcal(fallback, 120)
                if gramos > 0:
                    macros = _calcular_gramos(fallback, gramos)
                    items.append(
                        {
                            "ean": fallback["ean"],
                            "nombre": fallback["nombre"],
                            "rol_principal": fallback.get("rol_principal", "extra"),
                            **{k: macros[k] for k in ("gramos", "kcal", "proteina", "hidratos", "grasas")},
                        }
                    )
        return items

    proteina = _seleccionar_alimento("proteina", comida, macro_requerido="proteina")
    if proteina:
        gramos = _gramos_para_macro(proteina, "proteina", objetivo["proteina"])
        if gramos > 0:
            macros = _calcular_gramos(proteina, gramos)
            items.append(
                {
                    "ean": proteina["ean"],
                    "nombre": proteina["nombre"],
                    "rol_principal": "proteina",
                    **{k: macros[k] for k in ("gramos", "kcal", "proteina", "hidratos", "grasas")},
                }
            )

    hidrato = _seleccionar_alimento("hidrato", comida, evita_cereal=True, macro_requerido="hidratos")
    if hidrato:
        gramos = _gramos_para_macro(hidrato, "hidratos", objetivo["hidratos"])
        if gramos > 0:
            macros = _calcular_gramos(hidrato, gramos)
            items.append(
                {
                    "ean": hidrato["ean"],
                    "nombre": hidrato["nombre"],
                    "rol_principal": "hidrato",
                    **{k: macros[k] for k in ("gramos", "kcal", "proteina", "hidratos", "grasas")},
                }
            )

    relleno = _seleccionar_alimento("grasa", comida, evita_cereal=True, macro_requerido="grasas")
    if not relleno:
        relleno = _seleccionar_alimento("hidrato", comida, evita_cereal=True, macro_requerido="hidratos")
    if not relleno:
        relleno = _seleccionar_alimento("proteina", comida, macro_requerido="proteina")
    if relleno:
        gramos = (
            _gramos_para_macro(relleno, "grasas", objetivo["grasas"])
            or _gramos_para_macro(relleno, "hidratos", objetivo["hidratos"])
            or _gramos_para_macro(relleno, "proteina", objetivo["proteina"])
        )
        if gramos > 0:
            macros = _calcular_gramos(relleno, gramos)
            items.append(
                {
                    "ean": relleno["ean"],
                    "nombre": relleno["nombre"],
                    "rol_principal": relleno.get("rol_principal", "relleno"),
                    **{k: macros[k] for k in ("gramos", "kcal", "proteina", "hidratos", "grasas")},
                }
            )
    if len(items) < 3:
        candidatos = [
            alimento
            for alimento in list_alimentos()
            if _permitido_para_comida(alimento, comida)
        ]
        while len(items) < 3 and candidatos:
            extra = random.choice(candidatos)
            candidatos = [item for item in candidatos if item.get("ean") != extra.get("ean")]
            gramos = _gramos_para_kcal(extra, 120)
            if gramos > 0:
                macros = _calcular_gramos(extra, gramos)
                items.append(
                    {
                        "ean": extra["ean"],
                        "nombre": extra["nombre"],
                        "rol_principal": extra.get("rol_principal", "relleno"),
                        **{k: macros[k] for k in ("gramos", "kcal", "proteina", "hidratos", "grasas")},
                    }
                )
    return items


def _ajustar_tolerancia(items: list[dict], objetivo_kcal: float) -> list[dict]:
    kcal_total = sum(item["kcal"] for item in items)
    if not kcal_total:
        return items
    diferencia = objetivo_kcal - kcal_total
    if abs(diferencia) <= 50:
        return items
    kcal_proteina = sum(item["kcal"] for item in items if item["rol_principal"] == "proteina")
    kcal_resto = kcal_total - kcal_proteina
    if kcal_resto <= 0:
        return items
    ratio = max((objetivo_kcal - kcal_proteina) / kcal_resto, 0)
    ajustados = []
    for item in items:
        if item["rol_principal"] == "proteina":
            ajustados.append(item)
            continue
        gramos_nuevo = max(item["gramos"] * ratio, 1)
        factor = gramos_nuevo / item["gramos"] if item["gramos"] else 1
        ajustados.append(
            {
                **item,
                "gramos": gramos_nuevo,
                "kcal": item["kcal"] * factor,
                "proteina": item["proteina"] * factor,
                "hidratos": item["hidratos"] * factor,
                "grasas": item["grasas"] * factor,
            }
        )
    return ajustados


def generar_menu_dia(comidas: list[dict], tipo: str) -> dict[str, list[dict]]:
    objetivo = objetivos_por_tipo(tipo)
    objetivos_comidas = _objetivos_por_comida(objetivo)
    menu: dict[str, list[dict]] = {}
    for comida in comidas:
        nombre = comida["nombre"]
        if nombre not in objetivos_comidas:
            continue
        menu[nombre] = _generar_items_comida(nombre, objetivos_comidas[nombre])
    items_totales = [item for items in menu.values() for item in items]
    items_ajustados = _ajustar_tolerancia(items_totales, objetivo["kcal"])
    if items_ajustados:
        index = 0
        for nombre in menu:
            cantidad = len(menu[nombre])
            menu[nombre] = items_ajustados[index : index + cantidad]
            index += cantidad
    return menu


def generar_comida(comida: str, macros_objetivo: dict) -> list[dict]:
    objetivo = {
        "proteina": min(max(macros_objetivo.get("proteina", 0), 20), 35),
        "hidratos": macros_objetivo.get("hidratos", 0),
        "grasas": macros_objetivo.get("grasas", 0),
    }
    return _generar_items_comida(comida, objetivo)


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
