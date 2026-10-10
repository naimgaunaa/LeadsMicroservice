from app.model.state.estadoLead import EstadoLead
from app.model.state.derivado import Derivado
from app.model.state.descartado import Descartado
from app.model.nombre_estados import NombreEstados

class EnGestion(EstadoLead):
    def calificar(self):
        pass

    def tomar(self):
        pass

    def derivar(self):
        return Derivado()

    def descartar(self):
        return Descartado()

    def getEstado(self):
        return NombreEstados.EN_GESTION.value