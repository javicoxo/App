from ..crud import record_aprendizaje


def registrar_evento(evento: str, detalle: str) -> None:
    record_aprendizaje(evento, detalle)
