# 🔧 config.py - Configuración Central mcpComercialExt v1.1 - SECURE
import os
from dotenv import load_dotenv

# Cargar variables desde .env
load_dotenv()

# ===== CONFIGURACIÓN TELEGRAM (SEGURA) =====
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '7337079580:AAFxBDY4B1Muc6sUpV0uNxYa6DgVQh3LE_8')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://mcpcomercialext.onrender.com')

# ===== CONFIGURACIÓN REDASH API (SEGURA) =====
REDASH_BASE_URL = os.getenv('REDASH_BASE_URL', 'https://redash-mcp.farmuhub.co')
REDASH_API_KEY = os.getenv('REDASH_API_KEY', 'MJAgj9yCdpVsWFdinPPfqBkQuvTBKmhCOD9JEmNZ')
REDASH_QUERY_ID = os.getenv('REDASH_QUERY_ID', '100')

# ===== NUEVA CONFIGURACIÓN PARA CLIENTES NO DISPONIBLES =====
REDASH_UNAVAILABLE_API_KEY = os.getenv('REDASH_UNAVAILABLE_API_KEY', 'nQmXGYBuKdck7VBTrqvOZ45ypmp5idTlZpVEumbz')
REDASH_UNAVAILABLE_QUERY_ID = os.getenv('REDASH_UNAVAILABLE_QUERY_ID', '133')

# ===== URL DE PRE-REGISTRO =====
PREREGISTER_URL = os.getenv('PREREGISTER_URL', 'https://saludia.me/pre-register')

# ===== VALIDACIÓN DE VARIABLES CRÍTICAS =====
if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == 'your_token_here':
    print("⚠️ WARNING: TELEGRAM_TOKEN usando valor por defecto")

if not REDASH_API_KEY or REDASH_API_KEY == 'your_api_key_here':
    print("⚠️ WARNING: REDASH_API_KEY usando valor por defecto")

print(f"🔧 Config loaded: WEBHOOK_URL={WEBHOOK_URL}")
print(f"🔧 Config loaded: TELEGRAM_TOKEN={'✅ Configured' if TELEGRAM_TOKEN else '❌ Missing'}")

# ===== NO LLM - SOLO LÓGICA DIRECTA =====
# Este sistema NO utiliza ningún modelo de lenguaje
# Todo el procesamiento es lógica de programación directa

# ===== CONFIGURACIÓN CACHE =====
clients_cache = {
    "data": None,
    "timestamp": 0,
    "ttl": 3600  # 1 hora para datos estables de clientes
}

# ===== CONFIGURACIÓN CACHE CLIENTES NO DISPONIBLES =====
unavailable_clients_cache = {
    "data": None,
    "timestamp": 0,
    "ttl": 1800  # 30 minutos para datos más dinámicos
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
