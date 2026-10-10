from app.model.state.estadoLead import EstadoLead
from app.model.nombre_estados import NombreEstados

class Descartado(EstadoLead):
    def calificar(self):
        pass

    def tomar(self):
        pass

    def derivar(self):
        pass

    def descartar(self):
        pass

    def getEstado(self):
        return NombreEstados.DESCARTADO.value