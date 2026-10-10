from app.model.nombre_estados import NombreEstados


def cambiar_estado_lead(lead, nuevo_estado: NombreEstados) -> None:
    estado_actual = NombreEstados(lead.estado) if isinstance(lead.estado, str) else lead.estado
    transiciones = {
        NombreEstados.PENDIENTE: [NombreEstados.CALIFICADO],
        NombreEstados.CALIFICADO: [NombreEstados.EN_GESTION, NombreEstados.DESCARTADO],
        NombreEstados.EN_GESTION: [NombreEstados.DERIVADO, NombreEstados.DESCARTADO],
    }

    if nuevo_estado in transiciones.get(estado_actual, []):
        lead.estado = nuevo_estado.value
    else:
        raise ValueError(f"No se puede cambiar el estado de {estado_actual.value} a {nuevo_estado.value}")