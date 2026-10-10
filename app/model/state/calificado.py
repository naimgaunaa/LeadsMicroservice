from app.model.state.estadoLead import EstadoLead
from app.model.state.enGestion import EnGestion
from app.model.nombre_estados import NombreEstados

class Calificado(EstadoLead):
    def calificar(self):
        pass

    def tomar(self):
        return EnGestion()

    def derivar(self):
        pass

    def descartar(self):
        pass

    def getEstado(self):
        return NombreEstados.CALIFICADO.value