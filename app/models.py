from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from .database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    telefono = Column(String(50), nullable=True)
    email = Column(String(120), nullable=True)
    direccion = Column(String(180), nullable=True)
    clasificacion = Column(String(50), default="particular")  # particular, promotor, constructor, administracion
    portal_acceso = Column(Boolean, default=False)
    
    proyectos = relationship("Proyecto", back_populates="cliente")
    facturas = relationship("Factura", back_populates="cliente")


class Proveedor(Base):
    __tablename__ = "proveedores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    contacto = Column(String(120), nullable=True)
    telefono = Column(String(50), nullable=True)
    email = Column(String(120), nullable=True)

    materiales = relationship("Material", back_populates="proveedor")


class Material(Base):
    __tablename__ = "materiales"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(50), nullable=False)  # perfil, herraje, vidrio
    referencia = Column(String(100), nullable=False, unique=True)
    descripcion = Column(String(200), nullable=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True)
    precio_unitario = Column(Float, default=0.0)
    stock_actual = Column(Float, default=0.0)
    stock_minimo = Column(Float, default=0.0)
    unidad_medida = Column(String(20), default="unidad")  # metros, m2, unidad
    longitud_restante = Column(Float, nullable=True)  # para perfiles

    proveedor = relationship("Proveedor", back_populates="materiales")


class Proyecto(Base):
    __tablename__ = "proyectos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(140), nullable=False)
    tipo = Column(String(80), nullable=False)  # carpinteria o alumineria
    estado = Column(String(50), default="planificacion")
    descripcion = Column(Text, nullable=True)
    direccion_obra = Column(String(200), nullable=True)
    geolocalizacion = Column(String(100), nullable=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow)

    cliente = relationship("Cliente", back_populates="proyectos")
    presupuestos = relationship("Presupuesto", back_populates="proyecto")
    ordenes_produccion = relationship("OrdenProduccion", back_populates="proyecto")
    instalaciones = relationship("Instalacion", back_populates="proyecto")
    incidencias = relationship("Incidencia", back_populates="proyecto")


class Presupuesto(Base):
    __tablename__ = "presupuestos"

    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=False)
    version = Column(Integer, default=1)
    estado = Column(String(50), default="pendiente")  # pendiente, aceptado, rechazado, negociacion
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Totales calculados
    total_materiales = Column(Float, default=0.0)
    total_mano_obra = Column(Float, default=0.0)
    total_transporte = Column(Float, default=0.0)
    margen_porcentaje = Column(Float, default=0.0)
    total_final = Column(Float, default=0.0)
    
    firma_digital = Column(Boolean, default=False)

    proyecto = relationship("Proyecto", back_populates="presupuestos")
    items = relationship("PresupuestoItem", back_populates="presupuesto")


class PresupuestoItem(Base):
    __tablename__ = "presupuesto_items"

    id = Column(Integer, primary_key=True, index=True)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materiales.id"), nullable=True)
    descripcion = Column(String(200), nullable=False)
    cantidad = Column(Float, default=1.0)
    precio_unitario = Column(Float, default=0.0)
    subtotal = Column(Float, default=0.0)

    presupuesto = relationship("Presupuesto", back_populates="items")
    material = relationship("Material")


class Empleado(Base):
    __tablename__ = "empleados"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    rol = Column(String(50), nullable=False)  # operario, instalador, comercial
    telefono = Column(String(50), nullable=True)
    
    tareas = relationship("TareaProduccion", back_populates="operario")


class OrdenProduccion(Base):
    __tablename__ = "ordenes_produccion"

    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=False)
    presupuesto_id = Column(Integer, ForeignKey("presupuestos.id"), nullable=True)
    estado = Column(String(50), default="pendiente")  # pendiente, cortando, soldando, acabado, listo
    fecha_limite = Column(DateTime, nullable=True)
    prioridad = Column(String(20), default="normal")  # baja, normal, alta, urgente

    proyecto = relationship("Proyecto", back_populates="ordenes_produccion")
    tareas = relationship("TareaProduccion", back_populates="orden")


class TareaProduccion(Base):
    __tablename__ = "tareas_produccion"

    id = Column(Integer, primary_key=True, index=True)
    orden_id = Column(Integer, ForeignKey("ordenes_produccion.id"), nullable=False)
    operario_id = Column(Integer, ForeignKey("empleados.id"), nullable=True)
    descripcion = Column(String(200), nullable=False)
    estado = Column(String(50), default="pendiente")
    tiempo_registrado_horas = Column(Float, default=0.0)

    orden = relationship("OrdenProduccion", back_populates="tareas")
    operario = relationship("Empleado", back_populates="tareas")


class Instalacion(Base):
    __tablename__ = "instalaciones"

    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=False)
    fecha_programada = Column(DateTime, nullable=True)
    vehiculo = Column(String(100), nullable=True)
    estado = Column(String(50), default="programada")  # programada, en_curso, completada
    firma_cliente = Column(Boolean, default=False)
    notas = Column(Text, nullable=True)

    proyecto = relationship("Proyecto", back_populates="instalaciones")


class Factura(Base):
    __tablename__ = "facturas"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=True)
    monto = Column(Float, nullable=False)
    estado = Column(String(50), default="emitida")  # emtida, pagada, vencida
    fecha_emision = Column(DateTime, default=datetime.utcnow)
    fecha_vencimiento = Column(DateTime, nullable=True)

    cliente = relationship("Cliente", back_populates="facturas")
    proyecto = relationship("Proyecto")


class Incidencia(Base):
    __tablename__ = "incidencias"

    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(Integer, ForeignKey("proyectos.id"), nullable=False)
    descripcion = Column(Text, nullable=False)
    estado = Column(String(50), default="abierta")  # abierta, en_proceso, resuelta
    fecha_reporte = Column(DateTime, default=datetime.utcnow)
    resolucion = Column(Text, nullable=True)

    proyecto = relationship("Proyecto", back_populates="incidencias")


class Empresa(Base):
    __tablename__ = "empresa"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), default="Mi Empresa")
    nif = Column(String(50), nullable=True)
    direccion = Column(String(200), nullable=True)
    telefono = Column(String(50), nullable=True)
    email = Column(String(120), nullable=True)
    sitio_web = Column(String(120), nullable=True)
