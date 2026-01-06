from fastapi import FastAPI, HTTPException

from . import crud
from .schemas import (
    AlimentoCreate,
    ComidaCreate,
    ComidaItemCreate,
    ConsumoUpdate,
    DiaCreate,
    GeneracionRequest,
    GolosinaRequest,
    PerfilUpdate,
    PantryUpdate,
    ShoppingUpdate,
    SustitucionRequest,
)
from .services.generator import (
    generar_comida,
    recalcular_por_golosina,
    registrar_faltantes,
    sustituir_item as sustituir_item_generador,
)
from .services.learning import registrar_evento
from .services.stats import resumen_dia


app = FastAPI(title="BeFitLab API")


@app.post("/alimentos")
def crear_alimento(alimento: AlimentoCreate):
    crud.add_alimento(alimento.model_dump())
    return {"status": "ok"}


@app.get("/alimentos")
def listar_alimentos():
    return crud.list_alimentos()


@app.post("/dias")
def crear_dia(dia: DiaCreate):
    dia_id = crud.add_dia(dia.fecha, dia.tipo)
    for nombre in ["Desayuno", "Media mañana", "Almuerzo", "Merienda", "Cena"]:
        crud.add_comida(dia_id, nombre, nombre in {"Almuerzo", "Cena"})
    return {"id": dia_id}


@app.get("/dias")
def listar_dias():
    return crud.list_dias()


@app.put("/dias/{dia_id}")
def actualizar_dia(dia_id: str, dia: DiaCreate):
    dias = [item for item in crud.list_dias() if item["id"] == dia_id]
    if not dias:
        raise HTTPException(status_code=404, detail="Día no encontrado")
    crud.update_dia_tipo(dia_id, dia.tipo)
    return {"status": "ok"}


@app.post("/comidas")
def crear_comida(comida: ComidaCreate):
    comida_id = crud.add_comida(comida.dia_id, comida.nombre, comida.postre_obligatorio)
    return {"id": comida_id}


@app.get("/dias/{dia_id}/comidas")
def listar_comidas(dia_id: str):
    return crud.list_comidas(dia_id)


@app.post("/comidas/{comida_id}/items")
def crear_comida_item(item: ComidaItemCreate):
    crud.add_comida_items([item.model_dump()])
    return {"status": "ok"}


@app.get("/comidas/{comida_id}/items")
def listar_items(comida_id: int):
    return crud.list_comida_items(comida_id)


@app.post("/generador")
def generar_menu(request: GeneracionRequest):
    comidas = crud.list_comidas(request.dia_id)
    if not comidas:
        raise HTTPException(status_code=404, detail="Día no encontrado")
    generadas = []
    for comida in comidas:
        crud.clear_comida_items(comida["id"])
        items = generar_comida(comida["nombre"], {"kcal": 0, "proteina": 0, "hidratos": 0, "grasas": 0})
        for item in items:
            item["comida_id"] = comida["id"]
            item["gramos_iniciales"] = item["gramos"]
        crud.add_comida_items(items)
        registrar_faltantes(items)
        generadas.append({"comida": comida, "items": items})
    registrar_evento("generar_menu", f"dia_id={request.dia_id}")
    return generadas


@app.post("/golosinas")
def agregar_golosina(request: GolosinaRequest):
    item = request.model_dump()
    item["gramos_iniciales"] = request.gramos
    item_id = crud.add_golosina(item)
    recalcular_por_golosina(request.comida_id, item)
    registrar_evento("agregar_golosina", f"item_id={item_id}")
    return {"id": item_id}


@app.post("/sustituciones")
def sustituir_item(request: SustitucionRequest):
    item = crud.get_comida_item(request.comida_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    nuevo = sustituir_item_generador(item)
    if not nuevo:
        raise HTTPException(status_code=400, detail="No hay sustituciones disponibles")
    registrar_evento("sustituir_alimento", f"item_id={request.comida_item_id}")
    return nuevo


@app.post("/consumo")
def confirmar_consumo(update: ConsumoUpdate):
    crud.record_consumo(update.comida_item_id, update.estado, update.gramos)
    registrar_evento(update.estado, f"item_id={update.comida_item_id}")
    return {"status": "ok"}


@app.get("/estadisticas/{dia_id}")
def estadisticas_dia(dia_id: str):
    dias = [dia for dia in crud.list_dias() if dia["id"] == dia_id]
    if not dias:
        raise HTTPException(status_code=404, detail="Día no encontrado")
    return resumen_dia(dias[0])


@app.get("/despensa")
def listar_despensa(estado: str = "disponible"):
    return crud.list_despensa(estado)


@app.post("/despensa")
def actualizar_despensa(update: PantryUpdate):
    crud.upsert_despensa(update.ean, update.nombre, update.estado)
    return {"status": "ok"}


@app.get("/lista-compra")
def listar_compra():
    return crud.list_lista_compra()


@app.post("/lista-compra")
def actualizar_compra(update: ShoppingUpdate):
    crud.update_lista_compra(update.item_id, update.comprado)
    return {"status": "ok"}


@app.get("/perfil")
def obtener_perfil():
    objetivos = crud.list_objetivos()
    return {"default_tipo": crud.get_default_tipo(), "objetivos": objetivos}


@app.put("/perfil")
def actualizar_perfil(payload: PerfilUpdate):
    crud.set_default_tipo(payload.default_tipo)
    for objetivo in payload.objetivos:
        crud.upsert_objetivo(
            objetivo.tipo,
            objetivo.kcal,
            objetivo.proteina,
            objetivo.hidratos,
            objetivo.grasas,
        )
    return {"status": "ok"}
