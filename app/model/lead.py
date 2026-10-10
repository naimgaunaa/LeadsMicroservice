import uuid
from datetime import datetime
from sqlalchemy import Column, Float, Boolean, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Lead(Base):
    """Modelo SQLAlchemy para la tabla LEAD según el DER."""

    __tablename__ = "lead"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    cliente_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        comment="referencia externa al servicio clientes",
    )
    vehiculo_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        comment="referencia externa al servicio vehiculos",
    )

    anticipo = Column(Float, nullable=False)
    solicita_financiacion = Column(Boolean, nullable=False)
    ficha_completa = Column(Boolean, nullable=False)
    puntaje = Column(Integer, nullable=True)
    nivel = Column(String, nullable=True)
    estado = Column(String, nullable=False)

    provincia = Column(String, nullable=True)
    localidad = Column(String, nullable=True)

    permuta_tiene = Column(Boolean, nullable=False)
    permuta_descripcion = Column(String, nullable=True)
    permuta_valor_declarado = Column(Float, nullable=True)
    permuta_computable = Column(Boolean, nullable=True)

    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)