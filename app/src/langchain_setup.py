from langchain_community.agent_toolkits import create_sql_agent
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities.sql_database import SQLDatabase
from src.config import GROQ_API_KEY, MODEL_NAME, get_db_uri
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

def setup_sql_agent(db_manager) -> Optional[Any]:
    """Configura el agente SQL con LangChain"""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY no está configurada")

    # Crear instancia de SQLDatabase para LangChain
    try:
        db = SQLDatabase.from_uri(get_db_uri())
    except Exception as e:
        logger.error(f"Error al crear SQLDatabase: {e}")
        return None

    # Obtener esquema de la base de datos
    schema = db_manager.get_database_schema()
    if not schema:
        logger.error("No se pudo obtener el esquema de la base de datos")
        return None

    # Construir descripción del esquema
    schema_lines = ["Esquema de la base de datos:"]
    for table_name, table_info in schema.items():
        schema_lines.append(f"\nTabla: {table_name}\nColumnas:")
        for column in table_info['columns']:
            desc = f"- {column['name']}: {column['type']}"
            if column['primary_key']:
                desc += " (PRIMARY KEY)"
            if not column['nullable']:
                desc += " (NOT NULL)"
            schema_lines.append(desc)
        
        if table_info['foreign_keys']:
            schema_lines.append("Relaciones:")
            for fk in table_info['foreign_keys']:
                schema_lines.append(f"- {fk['constrained_columns']} → {fk['referred_table']}")

    schema_text = "\n".join(schema_lines)

    # Configurar el modelo de lenguaje
    llm = ChatGroq(
        temperature=0,
        model_name=MODEL_NAME,
        groq_api_key=GROQ_API_KEY,
        max_tokens=1024
    )

    # Prompt ya interpolado con schema_text
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""
    Eres un experto en bases de datos PostgreSQL. Tu tarea es traducir preguntas en lenguaje natural a consultas SQL válidas, precisas y eficientes, basadas exclusivamente en el siguiente esquema de base de datos:

    {schema_text}

    Instrucciones estrictas:
    1. Siempre responde en español, sin importar el idioma de entrada del usuario.
    2. Usa únicamente las tablas y columnas que aparecen en el esquema.
    3. Asegúrate de que las consultas estén optimizadas: evita subconsultas innecesarias, filtros redundantes o joins innecesarios.
    4. Utiliza el formato de fecha estándar: YYYY-MM-DD.
    5. Devuelve exclusivamente la consulta SQL sin explicaciones, sin formato markdown ni comentarios.
    6. Usa JOINs explícitos con INNER JOIN o LEFT JOIN cuando sea necesario relacionar tablas.
    7. Para contar registros, utiliza COUNT(*); para sumar valores, usa SUM(nombre_columna).
    8. Si se requiere agrupamiento, aplica GROUP BY con las columnas pertinentes.
    9. Ordena los resultados si la intención del usuario lo sugiere, usando ORDER BY con la columna y la dirección adecuada (ASC o DESC).
    10. Limita los resultados si se solicita el “primero”, “más caro”, “último”, etc., utilizando LIMIT 1 junto con ORDER BY.

    Tu respuesta debe ser solo una línea limpia de SQL correctamente formada. No incluyas explicaciones, contexto, comentarios ni nada adicional.
    """),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])

    # Crear agente
    try:
        agent = create_sql_agent(
            llm=llm,
            db=db,
            prompt=prompt,
            agent_type="tool-calling",
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5               # suficiente para Thought→Action→Obs→Done            
            
        )
        return agent
    except Exception as e:
        logger.error(f"Error al crear el agente SQL: {e}")
        return None
