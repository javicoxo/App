import sqlite3
from contextlib import contextmanager
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "befitlab.db"


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS fuentes_alimentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                tipo TEXT NOT NULL,
                creado_en TEXT NOT NULL
            )
            """
        )
        _ensure_alimentos_schema(connection)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS dias (
                id TEXT PRIMARY KEY,
                fecha TEXT NOT NULL,
                tipo TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS comidas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dia_id TEXT NOT NULL,
                nombre TEXT NOT NULL,
                postre_obligatorio INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(dia_id) REFERENCES dias(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS comida_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comida_id INTEGER NOT NULL,
                ean TEXT,
                nombre TEXT NOT NULL,
                gramos REAL NOT NULL,
                kcal REAL NOT NULL,
                proteina REAL NOT NULL,
                hidratos REAL NOT NULL,
                grasas REAL NOT NULL,
                rol_principal TEXT NOT NULL,
                es_golosina INTEGER NOT NULL DEFAULT 0,
                gramos_iniciales REAL NOT NULL,
                FOREIGN KEY(comida_id) REFERENCES comidas(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS despensa (
                ean TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                estado TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS lista_compra (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ean TEXT,
                nombre TEXT NOT NULL,
                comprado INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS consumo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comida_item_id INTEGER NOT NULL,
                estado TEXT NOT NULL,
                gramos REAL NOT NULL,
                FOREIGN KEY(comida_item_id) REFERENCES comida_items(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS aprendizaje (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evento TEXT NOT NULL,
                detalle TEXT NOT NULL,
                creado_en TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS objetivos_dia (
                tipo TEXT PRIMARY KEY,
                kcal REAL NOT NULL,
                proteina REAL NOT NULL,
                hidratos REAL NOT NULL,
                grasas REAL NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ajustes_app (
                clave TEXT PRIMARY KEY,
                valor TEXT NOT NULL
            )
            """
        )
        connection.commit()


def _ensure_alimentos_schema(connection: sqlite3.Connection) -> None:
    cursor = connection.cursor()
    columnas = cursor.execute("PRAGMA table_info(alimentos)").fetchall()
    if not columnas:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS alimentos (
                ean TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                marca TEXT,
                kcal_100g REAL NOT NULL,
                proteina_100g REAL NOT NULL,
                hidratos_100g REAL NOT NULL,
                grasas_100g REAL NOT NULL,
                rol_principal TEXT NOT NULL,
                grupo_funcional TEXT NOT NULL,
                subgrupo_funcional TEXT NOT NULL,
                fuente_id INTEGER,
                FOREIGN KEY(fuente_id) REFERENCES fuentes_alimentos(id)
            )
            """
        )
        return
    columnas_actuales = {columna[1] for columna in columnas}
    columnas_objetivo = {
        "ean",
        "nombre",
        "marca",
        "kcal_100g",
        "proteina_100g",
        "hidratos_100g",
        "grasas_100g",
        "rol_principal",
        "grupo_funcional",
        "subgrupo_funcional",
        "fuente_id",
    }
    if columnas_actuales == columnas_objetivo:
        return
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS alimentos_nuevo (
            ean TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            marca TEXT,
            kcal_100g REAL NOT NULL,
            proteina_100g REAL NOT NULL,
            hidratos_100g REAL NOT NULL,
            grasas_100g REAL NOT NULL,
            rol_principal TEXT NOT NULL,
            grupo_funcional TEXT NOT NULL,
            subgrupo_funcional TEXT NOT NULL,
            fuente_id INTEGER,
            FOREIGN KEY(fuente_id) REFERENCES fuentes_alimentos(id)
        )
        """
    )
    if columnas_actuales:
        grupo_col = "grupo_funcional" if "grupo_funcional" in columnas_actuales else "grupo_mediterraneo"
        subgrupo_col = "subgrupo_funcional" if "subgrupo_funcional" in columnas_actuales else "categorias"
        fuente_col = "fuente_id" if "fuente_id" in columnas_actuales else "NULL"
        cursor.execute(
            f"""
            INSERT INTO alimentos_nuevo (
                ean,
                nombre,
                marca,
                kcal_100g,
                proteina_100g,
                hidratos_100g,
                grasas_100g,
                rol_principal,
                grupo_funcional,
                subgrupo_funcional,
                fuente_id
            )
            SELECT
                ean,
                nombre,
                marca,
                kcal_100g,
                proteina_100g,
                hidratos_100g,
                grasas_100g,
                rol_principal,
                COALESCE({grupo_col}, ''),
                COALESCE({subgrupo_col}, ''),
                {fuente_col}
            FROM alimentos
            """
        )
    cursor.execute("DROP TABLE alimentos")
    cursor.execute("ALTER TABLE alimentos_nuevo RENAME TO alimentos")


@contextmanager
def get_connection():
    init_db()
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()
