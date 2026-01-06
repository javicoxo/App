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
            CREATE TABLE IF NOT EXISTS alimentos (
                ean TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                marca TEXT,
                kcal_100g REAL NOT NULL,
                proteina_100g REAL NOT NULL,
                hidratos_100g REAL NOT NULL,
                grasas_100g REAL NOT NULL,
                rol_principal TEXT NOT NULL,
                grupo_mediterraneo TEXT NOT NULL,
                frecuencia_mediterranea TEXT NOT NULL,
                permitido_comidas TEXT NOT NULL,
                categorias TEXT NOT NULL
            )
            """
        )
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
