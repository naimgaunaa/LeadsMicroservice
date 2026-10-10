from abc import ABC, abstractmethod


class EstadoLead(ABC):
    """Interfaz base para el patrón State de estados de Lead."""

    @abstractmethod
    def calificar(self) -> None:
        """Transicion al estado Calificado"""
        ...

    @abstractmethod
    def tomar(self) -> None:
        """Transición al estado EnGestión."""
        ...

    @abstractmethod
    def derivar(self) -> None:
        """Transición al estado Derivado."""
        ...

    @abstractmethod
    def descartar(self) -> None:
        """Transición al estado Descartado."""
        ...
