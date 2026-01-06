from datetime import datetime
from typing import Iterable

from .db import get_connection


def add_alimento(alimento: dict) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO alimentos
            (ean, nombre, marca, kcal_100g, proteina_100g, hidratos_100g, grasas_100g,
             rol_principal, grupo_mediterraneo, frecuencia_mediterranea,
             permitido_comidas, categorias)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alimento.get("ean"),
                alimento["nombre"],
                alimento.get("marca"),
                alimento["kcal_100g"],
                alimento["proteina_100g"],
                alimento["hidratos_100g"],
                alimento["grasas_100g"],
                alimento["rol_principal"],
                alimento["grupo_mediterraneo"],
                alimento["frecuencia_mediterranea"],
                alimento["permitido_comidas"],
                alimento["categorias"],
            ),
        )


def list_alimentos() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM alimentos").fetchall()
    return [dict(row) for row in rows]


def add_dia(fecha: str, tipo: str) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO dias (fecha, tipo) VALUES (?, ?)",
            (fecha, tipo),
        )
        return cursor.lastrowid


def list_dias() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM dias ORDER BY fecha").fetchall()
    return [dict(row) for row in rows]


def add_comida(dia_id: int, nombre: str, postre_obligatorio: bool) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO comidas (dia_id, nombre, postre_obligatorio) VALUES (?, ?, ?)",
            (dia_id, nombre, int(postre_obligatorio)),
        )
        return cursor.lastrowid


def list_comidas(dia_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM comidas WHERE dia_id = ? ORDER BY id",
            (dia_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def clear_comida_items(comida_id: int) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM comida_items WHERE comida_id = ?", (comida_id,))


def add_comida_items(items: Iterable[dict]) -> None:
    with get_connection() as connection:
        connection.executemany(
            """
            INSERT INTO comida_items
            (comida_id, ean, nombre, gramos, kcal, proteina, hidratos, grasas, rol_principal,
             es_golosina, gramos_iniciales)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    item["comida_id"],
                    item.get("ean"),
                    item["nombre"],
                    item["gramos"],
                    item["kcal"],
                    item["proteina"],
                    item["hidratos"],
                    item["grasas"],
                    item["rol_principal"],
                    int(item.get("es_golosina", False)),
                    item["gramos_iniciales"],
                )
                for item in items
            ],
        )


def list_comida_items(comida_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM comida_items WHERE comida_id = ? ORDER BY id",
            (comida_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_comida_item(item_id: int) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM comida_items WHERE id = ?",
            (item_id,),
        ).fetchone()
    return dict(row) if row else None


def update_comida_item_detalle(item_id: int, detalle: dict) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE comida_items
            SET ean = ?, nombre = ?, gramos = ?, kcal = ?, proteina = ?, hidratos = ?, grasas = ?,
                rol_principal = ?, gramos_iniciales = ?
            WHERE id = ?
            """,
            (
                detalle.get("ean"),
                detalle["nombre"],
                detalle["gramos"],
                detalle["kcal"],
                detalle["proteina"],
                detalle["hidratos"],
                detalle["grasas"],
                detalle["rol_principal"],
                detalle["gramos_iniciales"],
                item_id,
            ),
        )


def add_golosina(item: dict) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO comida_items
            (comida_id, ean, nombre, gramos, kcal, proteina, hidratos, grasas, rol_principal,
             es_golosina, gramos_iniciales)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (
                item["comida_id"],
                item.get("ean"),
                item["nombre"],
                item["gramos"],
                item["kcal"],
                item["proteina"],
                item["hidratos"],
                item["grasas"],
                item["rol_principal"],
                item["gramos_iniciales"],
            ),
        )
        return cursor.lastrowid


def update_comida_item(item_id: int, gramos: float, macros: dict) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE comida_items
            SET gramos = ?, kcal = ?, proteina = ?, hidratos = ?, grasas = ?
            WHERE id = ?
            """,
            (
                gramos,
                macros["kcal"],
                macros["proteina"],
                macros["hidratos"],
                macros["grasas"],
                item_id,
            ),
        )


def list_despensa(estado: str) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM despensa WHERE estado = ? ORDER BY nombre",
            (estado,),
        ).fetchall()
    return [dict(row) for row in rows]


def upsert_despensa(ean: str, nombre: str, estado: str) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO despensa (ean, nombre, estado)
            VALUES (?, ?, ?)
            ON CONFLICT(ean) DO UPDATE SET nombre = excluded.nombre, estado = excluded.estado
            """,
            (ean, nombre, estado),
        )


def add_lista_compra(ean: str | None, nombre: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO lista_compra (ean, nombre, comprado) VALUES (?, ?, 0)",
            (ean, nombre),
        )


def list_lista_compra() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM lista_compra ORDER BY comprado, nombre",
        ).fetchall()
    return [dict(row) for row in rows]


def update_lista_compra(item_id: int, comprado: bool) -> None:
    with get_connection() as connection:
        connection.execute(
            "UPDATE lista_compra SET comprado = ? WHERE id = ?",
            (int(comprado), item_id),
        )


def record_consumo(item_id: int, estado: str, gramos: float) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO consumo (comida_item_id, estado, gramos)
            VALUES (?, ?, ?)
            """,
            (item_id, estado, gramos),
        )


def list_consumo_por_dia(dia_id: int) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT consumo.*, comida_items.comida_id
            FROM consumo
            JOIN comida_items ON comida_items.id = consumo.comida_item_id
            JOIN comidas ON comidas.id = comida_items.comida_id
            WHERE comidas.dia_id = ?
            """,
            (dia_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def record_aprendizaje(evento: str, detalle: str) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO aprendizaje (evento, detalle, creado_en)
            VALUES (?, ?, ?)
            """,
            (evento, detalle, datetime.utcnow().isoformat()),
        )
