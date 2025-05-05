from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.inspection import inspect
from src.models import engine
from typing import List, Dict, Any, Optional, Tuple
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.Session = sessionmaker(bind=engine)
        self.session = None
        
    def connect(self) -> bool:
        """Establece conexión con la base de datos"""
        try:
            if not self.session:
                self.session = self.Session()
                logger.info("Conexión a PostgreSQL establecida")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error al conectar a PostgreSQL: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> Optional[Tuple[List[str], List[Dict]]]:
        """
        Ejecuta una consulta SQL directa
        
        Args:
            query: Consulta SQL a ejecutar
            params: Parámetros para la consulta
            
        Returns:
            Tuple con (columnas, resultados) o None si hay error
        """
        if not self.connect():
            return None
            
        try:
            result = self.session.execute(query, params or {})
            if result.returns_rows:
                columns = list(result.keys())
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                return columns, rows
            self.session.commit()
            return None, None
        except SQLAlchemyError as e:
            logger.error(f"Error al ejecutar consulta: {e}")
            self.session.rollback()
            return None, None
    
    def get_database_schema(self) -> Dict[str, Any]:
        """Obtiene el esquema completo de la base de datos"""
        if not self.connect():
            return {}
            
        inspector = inspect(engine)
        schema = {}
        
        for table_name in inspector.get_table_names():
            # Obtener columnas
            columns = []
            for column in inspector.get_columns(table_name):
                col_info = {
                    'name': column['name'],
                    'type': str(column['type']),
                    'nullable': column['nullable'],
                    'primary_key': column.get('primary_key', False)
                }
                columns.append(col_info)
            
            # Obtener relaciones
            foreign_keys = []
            for fk in inspector.get_foreign_keys(table_name):
                fk_info = {
                    'constrained_columns': fk['constrained_columns'],
                    'referred_table': fk['referred_table']
                }
                foreign_keys.append(fk_info)
            
            schema[table_name] = {
                'columns': columns,
                'foreign_keys': foreign_keys
            }
        
        return schema
    
    def close(self) -> None:
        """Cierra la conexión a la base de datos"""
        if self.session:
            try:
                self.session.close()
                logger.info("Conexión a PostgreSQL cerrada")
            except SQLAlchemyError as e:
                logger.error(f"Error al cerrar sesión: {e}")
            finally:
                self.session = None