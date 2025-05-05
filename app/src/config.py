import os
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno
load_dotenv()

# Configuración de PostgreSQL
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT')
}


# Configuración de Groq
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
MODEL_NAME = os.getenv('MODEL_NAME')

# Configuración de la aplicación
APP_CONFIG = {
    'TEMPLATES_DIR': Path(__file__).parent.parent / 'templates',
    'STATIC_DIR': Path(__file__).parent.parent / 'static',
    'DEBUG': os.getenv('DEBUG', 'False').lower() == 'true'
}

# Validar configuración
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY no está configurada en las variables de entorno")

def get_db_uri():
    """Genera la URI de conexión para SQLAlchemy"""
    return (
        f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )