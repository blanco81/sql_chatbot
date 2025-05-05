from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from src.chatbot import ChatbotSQL
from typing import Optional
import logging
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Inicializar la aplicación FastAPI
app = FastAPI(
    title="Chatbot SQL con LangChain",
    description="Aplicación que permite consultar una base de datos PostgreSQL usando lenguaje natural",
    version="1.0.0"
)

# Configurar CORS (para desarrollo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar rutas estáticas correctamente
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")
templates_dir = os.path.join(current_dir, "templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# Inicializar el chatbot
try:
    chatbot = ChatbotSQL()
    logger.info("Chatbot inicializado correctamente")
except Exception as e:
    logger.error(f"Error al inicializar el chatbot: {e}")
    raise RuntimeError("No se pudo inicializar el chatbot")

@app.get("/", include_in_schema=False)
async def read_root(request: Request):
    """Endpoint raíz que muestra la página principal"""
    try:
        return templates.TemplateResponse(
            "index.html",
            {"request": request}
        )
    except Exception as e:
        logger.error(f"Error al cargar la página principal: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/chat", include_in_schema=False)
async def chat_interface(request: Request):
    """Endpoint que muestra la interfaz de chat"""
    try:
        return templates.TemplateResponse(
            "chat.html",
            {
                "request": request,
                "user_input": None,
                "bot_response": None
            }
        )
    except Exception as e:
        logger.error(f"Error al cargar la interfaz de chat: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.post("/query", include_in_schema=False)
async def process_query(request: Request, user_input: str = Form(...)):
    """Endpoint que procesa las consultas del usuario"""
    try:
        if not user_input.strip():
            return RedirectResponse("/chat", status_code=303)
            
        response = chatbot.process_query(user_input)
        
        if not response.get("success", False):
            logger.warning(f"Consulta no procesada correctamente: {user_input}")
            return templates.TemplateResponse(
                "chat.html",
                {
                    "request": request,
                    "user_input": user_input,
                    "bot_response": "Lo siento, no pude procesar tu consulta."
                }
            )
        
        return templates.TemplateResponse(
            "chat.html",
            {
                "request": request,
                "user_input": user_input,
                "bot_response": response["response"]
            }
        )
    except Exception as e:
        logger.error(f"Error al procesar consulta: {e}")
        return RedirectResponse("/chat", status_code=303)

@app.on_event("shutdown")
async def shutdown_event():
    """Maneja el cierre de la aplicación"""
    try:
        chatbot.close()
        logger.info("Recursos del chatbot liberados correctamente")
    except Exception as e:
        logger.error(f"Error al cerrar recursos: {e}")

# Punto de entrada para desarrollo
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        proxy_headers=True
    )