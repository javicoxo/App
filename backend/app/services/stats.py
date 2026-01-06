from ..crud import list_comidas, list_comida_items, get_objetivo


def resumen_dia(dia: dict) -> dict:
    comidas = list_comidas(dia["id"])
    totals = {"kcal": 0, "proteina": 0, "hidratos": 0, "grasas": 0}
    for comida in comidas:
        items = list_comida_items(comida["id"])
        for item in items:
            totals["kcal"] += item["kcal"]
            totals["proteina"] += item["proteina"]
            totals["hidratos"] += item["hidratos"]
            totals["grasas"] += item["grasas"]
    objetivo_raw = get_objetivo(dia["tipo"])
    objetivo = {
        "kcal": objetivo_raw["kcal"],
        "proteina": objetivo_raw["proteina"],
        "hidratos": objetivo_raw["hidratos"],
        "grasas": objetivo_raw["grasas"],
    }
    return {
        "objetivo": objetivo,
        "consumo": totals,
        "porcentaje": {
            key: (totals[key] / objetivo[key] * 100 if objetivo[key] else 0)
            for key in objetivo
        },
    }
