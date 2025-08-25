# 🔧 config.py - Configuración Central mcpComercialExt v1.1 - SECURE
import os
from dotenv import load_dotenv

# Cargar variables desde .env
load_dotenv()

# ===== CONFIGURACIÓN TELEGRAM (SEGURA) =====
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://your-app-url.onrender.com')

# ===== CONFIGURACIÓN REDASH API (SEGURA) =====
REDASH_BASE_URL = os.getenv('REDASH_BASE_URL', 'https://redash-mcp.farmuhub.co')
REDASH_API_KEY = os.getenv('REDASH_API_KEY')
REDASH_QUERY_ID = os.getenv('REDASH_QUERY_ID', '100')

# ===== VALIDACIÓN DE VARIABLES CRÍTICAS =====
if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN no está configurado en .env")
if not REDASH_API_KEY:
    raise ValueError("❌ REDASH_API_KEY no está configurado en .env")

# ===== NO LLM - SOLO LÓGICA DIRECTA =====
# Este sistema NO utiliza ningún modelo de lenguaje
# Todo el procesamiento es lógica de programación directa

# ===== CONFIGURACIÓN CACHE =====
clients_cache = {
    "data": None,
    "timestamp": 0,
    "ttl": 3600  # 1 hora para datos estables de clientes
}

# ===== CONFIGURACIÓN TIMEOUTS =====
REDASH_TIMEOUT = 30  # segundos - tiempo suficiente para queries grandes
TELEGRAM_TIMEOUT = 8  # segundos
WEBHOOK_TIMEOUT = 8  # segundos

# ===== CONFIGURACIÓN BOT =====
MAX_RESULTS_SHOW = 5   # Máximo resultados a mostrar
MAX_MESSAGE_LENGTH = 4000

# ===== TIPOS DE DOCUMENTO VÁLIDOS =====
VALID_DOC_TYPES = ['NIT', 'CC']

# ===== CONFIGURACIÓN VALIDACIONES =====
MAX_NIT_LENGTH = 15      # NIT máximo en Colombia
MAX_CC_LENGTH = 10       # Cédula máxima en Colombia  
MIN_DOC_LENGTH = 6       # Mínimo caracteres para documento
