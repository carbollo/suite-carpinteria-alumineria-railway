from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from .database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    telefono = Column(String(50), nullable=True)
    email = Column(String(120), nullable=True)
    direccion = Column(String(180), nullable=True)

    proyectos = relationship("Proyecto", back_populates="cliente")


class Proyecto(Base):
    __tablename__ = "proyectos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(140), nullable=False)
    tipo = Column(String(80), nullable=False)  # carpinteria o alumineria
    estado = Column(String(50), default="planificacion")
    descripcion = Column(Text, nullable=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow)

    cliente = relationship("Cliente", back_populates="proyectos")
    presupuestos = relationship("Presupuesto", back_populates="proyecto")
    tareas = relationship("Tarea", back_populates="proyecto")


class Presupuesto(Base):
    __tablename__ = "presupuestos"

    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=False)
    material = Column(Float, default=0.0)
    mano_obra = Column(Float, default=0.0)
    transporte = Column(Float, default=0.0)
    margen = Column(Float, default=0.0)
    total = Column(Float, default=0.0)

    proyecto = relationship("Proyecto", back_populates="presupuestos")


class Tarea(Base):
    __tablename__ = "tareas"

    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=False)
    titulo = Column(String(120), nullable=False)
    estado = Column(String(40), default="pendiente")
    responsable = Column(String(80), nullable=True)

    proyecto = relationship("Proyecto", back_populates="tareas")
