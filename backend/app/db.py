import sqlite3
from contextlib import contextmanager
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "befitlab.db"

ALIMENTOS_COLUMNS = {
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
}

LEGACY_ALIMENTOS_COLUMNS = {
    "grupo_mediterraneo",
    "frecuencia_mediterranea",
    "permitido_comidas",
    "categorias",
}


def _create_alimentos_table(cursor: sqlite3.Cursor) -> None:
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
            subgrupo_funcional TEXT NOT NULL
        )
        """
    )


def _ensure_alimentos_schema(cursor: sqlite3.Cursor) -> None:
    table_info = cursor.execute("PRAGMA table_info(alimentos)").fetchall()
    if not table_info:
        _create_alimentos_table(cursor)
        return
    columns = {row[1] for row in table_info}
    if columns & LEGACY_ALIMENTOS_COLUMNS:
        cursor.execute("ALTER TABLE alimentos RENAME TO alimentos_legacy")
        _create_alimentos_table(cursor)
        cursor.execute(
            """
            INSERT INTO alimentos (
                ean, nombre, marca, kcal_100g, proteina_100g, hidratos_100g, grasas_100g,
                rol_principal, grupo_funcional, subgrupo_funcional
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
                COALESCE(grupo_mediterraneo, ''),
                COALESCE(categorias, '')
            FROM alimentos_legacy
            """
        )
        cursor.execute("DROP TABLE alimentos_legacy")
        return
    missing = {"grupo_funcional", "subgrupo_funcional"} - columns
    for column in sorted(missing):
        cursor.execute(f"ALTER TABLE alimentos ADD COLUMN {column} TEXT NOT NULL DEFAULT ''")


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.cursor()
        _ensure_alimentos_schema(cursor)
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
