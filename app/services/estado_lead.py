from app.model.estado_lead import EstadoLead

def cambiar_estado_lead(lead, nuevo_estado):
    transiciones = {
        EstadoLead.PENDIENTE: [EstadoLead.CALIFICADO],
        EstadoLead.CALIFICADO: [EstadoLead.EN_GESTION, EstadoLead.DESCARTADO],
        EstadoLead.EN_GESTION: [EstadoLead.DERIVADO, EstadoLead.DESCARTADO],
    }

    if nuevo_estado in transiciones[lead.estado]:
        lead.estado = nuevo_estado
    else:
        raise ValueError(f"No se puede cambiar el estado de {lead.estado} a {nuevo_estado}")