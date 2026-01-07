from pydantic import BaseModel, Field


class AlimentoBase(BaseModel):
    ean: str | None = None
    nombre: str
    marca: str | None = None
    kcal_100g: float
    proteina_100g: float
    hidratos_100g: float
    grasas_100g: float
    rol_principal: str
    grupo_mediterraneo: str
    frecuencia_mediterranea: str
    permitido_comidas: str
    categorias: str


class AlimentoCreate(AlimentoBase):
    pass


class DiaCreate(BaseModel):
    fecha: str = Field(pattern="^\\d{2}/\\d{2}/\\d{4}$")
    tipo: str = Field(pattern="^(Entreno|Descanso)$")


class ComidaCreate(BaseModel):
    dia_id: str
    nombre: str
    postre_obligatorio: bool = False


class ComidaItemCreate(BaseModel):
    comida_id: int
    ean: str | None = None
    nombre: str
    gramos: float
    kcal: float
    proteina: float
    hidratos: float
    grasas: float
    rol_principal: str
    es_golosina: bool = False
    gramos_iniciales: float


class GeneracionRequest(BaseModel):
    dia_id: str


class GolosinaRequest(BaseModel):
    comida_id: int
    nombre: str
    gramos: float
    kcal: float
    proteina: float
    hidratos: float
    grasas: float
    rol_principal: str


class SustitucionRequest(BaseModel):
    comida_item_id: int


class ConsumoUpdate(BaseModel):
    comida_item_id: int
    estado: str = Field(pattern="^(aceptado|rechazado|modificado)$")
    gramos: float


class PantryUpdate(BaseModel):
    ean: str | None = None
    nombre: str
    estado: str = Field(pattern="^(disponible|agotado)$")


class ShoppingUpdate(BaseModel):
    item_id: int
    comprado: bool


class ObjetivoDia(BaseModel):
    tipo: str
    kcal: float
    proteina: float
    hidratos: float
    grasas: float


class PerfilUpdate(BaseModel):
    default_tipo: str | None = None
    objetivos: list[ObjetivoDia]
