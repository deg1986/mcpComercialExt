# 🔧 config.py - Configuración Central mcpComercialExt v1.3 - SECURE
import os
from dotenv import load_dotenv

# Cargar variables desde .env
load_dotenv()

# ===== CONFIGURACIÓN TELEGRAM (SEGURA) =====
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# ===== CONFIGURACIÓN REDASH API (SEGURA) =====
REDASH_BASE_URL = os.getenv('REDASH_BASE_URL')
REDASH_API_KEY = os.getenv('REDASH_API_KEY')
REDASH_QUERY_ID = os.getenv('REDASH_QUERY_ID')

# ===== NUEVA CONFIGURACIÓN PARA CLIENTES NO DISPONIBLES =====
REDASH_UNAVAILABLE_API_KEY = os.getenv('REDASH_UNAVAILABLE_API_KEY')
REDASH_UNAVAILABLE_QUERY_ID = os.getenv('REDASH_UNAVAILABLE_QUERY_ID')

# ===== CONFIGURACIÓN NOCODB API (NUEVA) =====
NOCODB_BASE_URL = os.getenv('NOCODB_BASE_URL')
NOCODB_TOKEN = os.getenv('NOCODB_TOKEN')
NOCODB_TABLE_ID = os.getenv('NOCODB_TABLE_ID')

# ===== URL DE PRE-REGISTRO =====
PREREGISTER_URL = os.getenv('PREREGISTER_URL')

# ===== VALIDACIÓN DE VARIABLES CRÍTICAS =====
required_vars = {
    'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
    'WEBHOOK_URL': WEBHOOK_URL,
    'REDASH_BASE_URL': REDASH_BASE_URL,
    'REDASH_API_KEY': REDASH_API_KEY,
    'REDASH_QUERY_ID': REDASH_QUERY_ID,
    'REDASH_UNAVAILABLE_API_KEY': REDASH_UNAVAILABLE_API_KEY,
    'REDASH_UNAVAILABLE_QUERY_ID': REDASH_UNAVAILABLE_QUERY_ID,
    'NOCODB_BASE_URL': NOCODB_BASE_URL,
    'NOCODB_TOKEN': NOCODB_TOKEN,
    'NOCODB_TABLE_ID': NOCODB_TABLE_ID,
    'PREREGISTER_URL': PREREGISTER_URL
}

# Verificar variables críticas
missing_vars = [var_name for var_name, var_value in required_vars.items() if not var_value]

if missing_vars:
    print("❌ ERROR: Variables de entorno faltantes:")
    for var in missing_vars:
        print(f"   - {var}")
    print("\n💡 Configura estas variables en tu entorno o archivo .env")
    print("📖 Consulta .env.example para ver el formato requerido")
else:
    print("✅ Todas las variables de entorno configuradas correctamente")

# Mostrar estado de configuración (sin exponer valores)
print(f"🔧 Config loaded:")
print(f"   - TELEGRAM_TOKEN: {'✅ Configured' if TELEGRAM_TOKEN else '❌ Missing'}")
print(f"   - REDASH_API: {'✅ Configured' if REDASH_API_KEY else '❌ Missing'}")
print(f"   - NOCODB_API: {'✅ Configured' if NOCODB_TOKEN else '❌ Missing'}")
print(f"   - WEBHOOK_URL: {'✅ Configured' if WEBHOOK_URL else '❌ Missing'}")

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
REDASH_TIMEOUT = int(os.getenv('REDASH_TIMEOUT', '30'))  # segundos
TELEGRAM_TIMEOUT = int(os.getenv('TELEGRAM_TIMEOUT', '8'))  # segundos
WEBHOOK_TIMEOUT = int(os.getenv('WEBHOOK_TIMEOUT', '8'))  # segundos
NOCODB_TIMEOUT = int(os.getenv('NOCODB_TIMEOUT', '15'))  # segundos

# ===== CONFIGURACIÓN BOT =====
MAX_RESULTS_SHOW = int(os.getenv('MAX_RESULTS_SHOW', '5'))
MAX_MESSAGE_LENGTH = int(os.getenv('MAX_MESSAGE_LENGTH', '4000'))

# ===== TIPOS DE DOCUMENTO VÁLIDOS =====
VALID_DOC_TYPES = ['NIT', 'CC']

# ===== CONFIGURACIÓN VALIDACIONES =====
MAX_NIT_LENGTH = int(os.getenv('MAX_NIT_LENGTH', '15'))
MAX_CC_LENGTH = int(os.getenv('MAX_CC_LENGTH', '10'))
MIN_DOC_LENGTH = int(os.getenv('MIN_DOC_LENGTH', '6'))

# ===== CONFIGURACIÓN VALIDACIONES COMERCIAL =====
MIN_CEDULA_LENGTH = int(os.getenv('MIN_CEDULA_LENGTH', '6'))
MAX_CEDULA_LENGTH = int(os.getenv('MAX_CEDULA_LENGTH', '12'))
MIN_NAME_LENGTH = int(os.getenv('MIN_NAME_LENGTH', '2'))
MAX_NAME_LENGTH = int(os.getenv('MAX_NAME_LENGTH', '100'))
MIN_PHONE_LENGTH = int(os.getenv('MIN_PHONE_LENGTH', '7'))
MAX_PHONE_LENGTH = int(os.getenv('MAX_PHONE_LENGTH', '20'))
