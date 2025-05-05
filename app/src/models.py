from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from src.config import get_db_uri

# Crear la base para los modelos
Base = declarative_base()

# Configurar el motor de la base de datos
engine = create_engine(
    get_db_uri(),
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

class Cliente(Base):
    """Modelo para la tabla de clientes"""
    __tablename__ = 'clientes'
    
    cliente_id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    fecha_registro = Column(Date, server_default='CURRENT_DATE')
    
    # Relación con pedidos (one-to-many)
    pedidos = relationship("Pedido", back_populates="cliente", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Cliente(id={self.cliente_id}, nombre='{self.nombre}')>"

class Producto(Base):
    """Modelo para la tabla de productos"""
    __tablename__ = 'productos'
    
    producto_id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    precio = Column(Numeric(10, 2), nullable=False)
    categoria = Column(String(50))
    
    # Relación con detalles de pedido (one-to-many)
    detalles_pedido = relationship("DetallePedido", back_populates="producto")
    
    def __repr__(self):
        return f"<Producto(id={self.producto_id}, nombre='{self.nombre}', precio={self.precio})>"

class Pedido(Base):
    """Modelo para la tabla de pedidos"""
    __tablename__ = 'pedidos'
    
    pedido_id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey('clientes.cliente_id'), nullable=False)
    fecha_pedido = Column(Date, server_default='CURRENT_DATE')
    estado = Column(String(20), server_default='pendiente')
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="pedidos")
    detalles = relationship("DetallePedido", back_populates="pedido", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Pedido(id={self.pedido_id}, cliente_id={self.cliente_id}, estado='{self.estado}')>"

class DetallePedido(Base):
    """Modelo para la tabla de detalles_pedido"""
    __tablename__ = 'detalles_pedido'
    
    detalle_id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey('pedidos.pedido_id'), nullable=False)
    producto_id = Column(Integer, ForeignKey('productos.producto_id'), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    
    # Relaciones (many-to-one)
    pedido = relationship("Pedido", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalles_pedido")
    
    def __repr__(self):
        return f"<DetallePedido(pedido_id={self.pedido_id}, producto_id={self.producto_id}, cantidad={self.cantidad})>"

def create_tables():
    """Crea todas las tablas en la base de datos"""
    Base.metadata.create_all(engine)

def drop_tables():
    """Elimina todas las tablas de la base de datos (para desarrollo)"""
    Base.metadata.drop_all(engine)