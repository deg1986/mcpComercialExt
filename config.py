# 🔧 config.py - Configuración Central mcpComercialExt v1.0 - SIN LLM
import os

# ===== CONFIGURACIÓN TELEGRAM =====
TELEGRAM_TOKEN = "7337079580:AAFxBDY4B1Muc6sUpV0uNxYa6DgVQh3LE_8"
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', 'https://your-app-url.onrender.com')

# ===== CONFIGURACIÓN REDASH API =====
REDASH_BASE_URL = "https://redash-mcp.farmuhub.co"
REDASH_API_KEY = "MJAgj9yCdpVsWFdinPPfqBkQuvTBKmhCOD9JEmNZ"
REDASH_QUERY_ID = "100"

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
