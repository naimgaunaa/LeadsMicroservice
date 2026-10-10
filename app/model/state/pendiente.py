from app.model.state.estadoLead import EstadoLead
from app.model.state.calificado import Calificado
from app.model.nombre_estados import NombreEstados

class Pendiente(EstadoLead):
    def calificar(self):
        return Calificado()

    def tomar(self):
        pass

    def derivar(self):
        pass

    def descartar(self):
        pass

    def getEstado(self):
        return NombreEstados.PENDIENTE.value