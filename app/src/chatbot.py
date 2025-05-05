from typing import Optional, Dict, Any, List, Tuple
from src.langchain_setup import setup_sql_agent
from src.database import DatabaseManager
from langchain_community.utilities.sql_database import SQLDatabase
from src.config import get_db_uri
import re
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatbotSQL:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.agent = None
        self.sql_db = None
        
        try:
            # Conectar a la base de datos
            if not self.db_manager.connect():
                raise RuntimeError("No se pudo conectar a PostgreSQL")
            
            # Configurar SQLDatabase para LangChain
            self.sql_db = SQLDatabase.from_uri(get_db_uri())
            
            # Inicializar agente SQL
            self.agent = setup_sql_agent(self.db_manager)
            if not self.agent:
                raise RuntimeError("No se pudo inicializar el agente SQL")
            
            logger.info("Chatbot SQL inicializado correctamente")
            
        except Exception as e:
            logger.error(f"Error durante la inicialización: {e}")
            self._cleanup_resources()
            raise RuntimeError("No se pudo inicializar el chatbot") from e

    def process_query(self, user_input: str) -> Dict[str, Any]:
        """
        Procesa una consulta del usuario y devuelve una respuesta estructurada
        
        Args:
            user_input: Consulta en lenguaje natural o SQL directo (prefijado con 'sql:')
            
        Returns:
            Dict con:
            - success: Bool indicando si la operación fue exitosa
            - response: Respuesta formateada
            - query: Consulta SQL generada (opcional)
            - results: Resultados en bruto (opcional)
        """
        response = {
            "success": False,
            "response": "Lo siento, ocurrió un error al procesar tu consulta.",
            "query": None,
            "results": None
        }
        
        try:
            # Modo SQL directo (para desarrollo/depuración)
            if user_input.strip().lower().startswith("sql:"):
                query = user_input[4:].strip()
                columns, data = self._execute_direct_query(query)
                
                if columns and data:
                    response.update({
                        "success": True,
                        "response": self._format_results(columns, data),
                        "query": query,
                        "results": data
                    })
                return response
            
            # Consulta en lenguaje natural
            agent_response = self.agent.invoke({"input": user_input})
            sql_query = self._extract_sql_query(agent_response)
            
            response.update({
                "success": True,
                "response": agent_response.get("output", "No pude generar una respuesta."),
                "query": sql_query
            })
            return response
            
        except Exception as e:
            logger.error(f"Error al procesar consulta: {e}")
            response["response"] = f"Error: {str(e)}"
            return response

    def _execute_direct_query(self, query: str) -> Tuple[Optional[List[str]], Optional[List[Dict]]]:
        """Ejecuta una consulta SQL directa y devuelve columnas y resultados"""
        try:
            return self.db_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Error al ejecutar consulta directa: {e}")
            return None, None

    def _format_results(self, columns: List[str], data: List[Dict]) -> str:
        """
        Formatea los resultados de una consulta como tabla HTML
        
        Args:
            columns: Lista de nombres de columnas
            data: Lista de diccionarios con los resultados
            
        Returns:
            String con tabla HTML formateada
        """
        if not columns or not data:
            return "No se encontraron resultados."
        
        html = ["<div class='table-responsive'><table class='table table-striped'><thead><tr>"]
        html.extend(f"<th>{col}</th>" for col in columns)
        html.append("</tr></thead><tbody>")
        
        for row in data:
            html.append("<tr>")
            html.extend(f"<td>{row.get(col, '')}</td>" for col in columns)
            html.append("</tr>")
        
        html.append("</tbody></table></div>")
        return "".join(html)

    def _extract_sql_query(self, agent_response: Dict[str, Any]) -> Optional[str]:
        """
        Extrae la consulta SQL de la respuesta del agente
        
        Args:
            agent_response: Respuesta del agente LangChain
            
        Returns:
            Consulta SQL extraída o None si no se encontró
        """
        output = agent_response.get("output", "")
        matches = re.findall(r"```sql\n(.*?)\n```", output, re.DOTALL)
        return matches[0].strip() if matches else None

    def _cleanup_resources(self):
        """Libera todos los recursos del chatbot"""
        try:
            if hasattr(self, 'db_manager') and self.db_manager:
                self.db_manager.close()
                logger.info("Conexión a PostgreSQL cerrada")
        except Exception as e:
            logger.error(f"Error al cerrar conexión: {e}")

    def close(self):
        """Cierra limpiamente todos los recursos"""
        self._cleanup_resources()
        logger.info("Chatbot SQL cerrado correctamente")

    def __enter__(self):
        """Permite usar el chatbot en un contexto with"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Garantiza que los recursos se liberen al salir del contexto"""
        self.close()