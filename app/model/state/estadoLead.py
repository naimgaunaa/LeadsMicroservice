from abc import ABC, abstractmethod

class EstadoLead(ABC):
    """Interfaz base para el patrón State de estados de Lead."""

    @abstractmethod
    def calificar(self):
        """Transicion al estado Calificado"""
        ...

    @abstractmethod
    def tomar(self):
        """Transición al estado EnGestión."""
        ...

    @abstractmethod
    def derivar(self):
        """Transición al estado Derivado."""
        ...

    @abstractmethod
    def descartar(self):
        """Transición al estado Descartado."""
        ...

    @abstractmethod
    def getEstado(self):
        """Obtener nombre de estado actual"""
        ...
