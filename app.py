# 🚀 mcpComercialExt v1.0 - Aplicación Principal
import os
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
import logging

# Imports modulares
from config import *
from redash_service import get_clients_from_redash, search_client_by_document, get_clients_summary
from bot_handlers import setup_telegram_routes
from utils import setup_webhook, validate_telegram_token

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
CORS(app)

# Variables globales
bot_configured = False

# ===== ENDPOINTS PRINCIPALES =====

@app.route('/')
def home():
    """Endpoint principal"""
    return jsonify({
        "name": "mcpComercialExt - Bot Comercial Externo",
        "version": "1.0.0",
        "status": "running",
        "description": "Sistema de búsqueda de clientes para comerciales externos via Telegram",
        "features": [
            "Búsqueda de clientes por NIT y CC",
            "Integración con Redash API",
            "Cache inteligente",
            "Validación automática de documentos",
            "Bot de Telegram interactivo"
        ],
        "timestamp": datetime.now().isoformat(),
        "cache_status": {
            "enabled": True,
            "ttl_seconds": clients_cache["ttl"],
            "last_update": datetime.fromtimestamp(clients_cache["timestamp"]).isoformat() if clients_cache["timestamp"] > 0 else "never"
        },
        "telegram_bot": {
            "enabled": bool(TELEGRAM_TOKEN),
            "token_valid": validate_telegram_token(),
            "webhook_configured": bot_configured,
            "webhook_url": f"{WEBHOOK_URL}/telegram-webhook" if TELEGRAM_TOKEN else None
        },
        "redash_integration": {
            "base_url": REDASH_BASE_URL,
            "query_id": REDASH_QUERY_ID,
            "api_configured": bool(REDASH_API_KEY)
        },
        "api_endpoints": {
            "clients": {
                "/api/clients": "Lista de clientes desde Redash",
                "/api/clients/search": "Búsqueda por documento",
                "/api/clients/summary": "Resumen y estadísticas"
            },
            "system": {
                "/health": "Estado del sistema",
                "/setup-webhook": "Configurar webhook de Telegram"
            }
        },
        "document_types": {
            "supported": VALID_DOC_TYPES,
            "validation": {
                "NIT": f"Entre {MIN_DOC_LENGTH} y {MAX_NIT_LENGTH} dígitos",
                "CC": f"Entre {MIN_DOC_LENGTH} y {MAX_CC_LENGTH} dígitos"
            }
        }
    })

@app.route('/health')
def health():
    """Health check optimizado"""
    import time
    start_time = time.time()
    
    # Test Redash connection
    redash_test = get_clients_summary()
    response_time = time.time() - start_time
    
    # Test Telegram token
    telegram_valid = validate_telegram_token()
    
    return jsonify({
        "status": "healthy",
        "response_time_ms": round(response_time * 1000, 2),
        "cache_hit": redash_test.get('stats', {}).get('cached', False) if redash_test.get('success') else False,
        "services": {
            "flask": "running",
            "redash_api": "ok" if redash_test.get('success') else "error",
            "cache": "active" if clients_cache["data"] else "empty",
            "telegram_bot": "configured" if telegram_valid else "invalid_token",
            "webhook": "configured" if bot_configured else "not_configured"
        },
        "data_status": {
            "clients_available": redash_test.get('stats', {}).get('total_clients', 0) if redash_test.get('success') else 0,
            "columns_detected": redash_test.get('stats', {}).get('total_columns', 0) if redash_test.get('success') else 0,
            "cache_age_minutes": round((time.time() - clients_cache["timestamp"]) / 60, 1) if clients_cache["timestamp"] > 0 else 0
        },
        "last_check": datetime.now().isoformat()
    })

# ===== API ENDPOINTS =====

@app.route('/api/clients')
def api_clients():
    """API para obtener clientes desde Redash"""
    from flask import request
    
    limit = request.args.get('limit', type=int)
    include_sample = request.args.get('include_sample', 'false').lower() == 'true'
    
    try:
        data = get_clients_from_redash()
        
        if not data.get("success"):
            return jsonify({"error": data.get("error")}), 500
        
        clients_data = data.get("data", {})
        clients = clients_data.get("clients", [])
        columns = clients_data.get("columns", [])
        
        # Aplicar límite si se especifica
        if limit and limit > 0:
            clients = clients[:limit]
        
        response = {
            "success": True,
            "total_clients": len(clients_data.get("clients", [])),
            "returned_clients": len(clients),
            "columns": len(columns),
            "cached": data.get("cached", False),
            "column_info": [{"name": col.get("name"), "type": col.get("type")} for col in columns]
        }
        
        # Incluir muestra de datos si se solicita
        if include_sample:
            response["sample_clients"] = clients[:5]  # Primeros 5 como muestra
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ API clients error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/clients/search', methods=['GET'])
def api_search_client():
    """API para buscar cliente por documento"""
    from flask import request
    
    doc_type = request.args.get('type', '').upper()
    doc_number = request.args.get('number', '').strip()
    
    if not doc_type or not doc_number:
        return jsonify({
            "error": "Parámetros requeridos: type (NIT/CC) y number",
            "example": "/api/clients/search?type=NIT&number=901234567"
        }), 400
    
    if doc_type not in VALID_DOC_TYPES:
        return jsonify({
            "error": f"Tipo de documento inválido: {doc_type}",
            "valid_types": VALID_DOC_TYPES
        }), 400
    
    try:
        result = search_client_by_document(doc_type, doc_number)
        
        if result.get("success"):
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"❌ API search error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/clients/summary')
def api_clients_summary():
    """API para obtener resumen de clientes"""
    try:
        summary = get_clients_summary()
        
        if summary.get("success"):
            return jsonify(summary)
        else:
            return jsonify(summary), 500
            
    except Exception as e:
        logger.error(f"❌ API summary error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/setup-webhook', methods=['POST'])
def setup_webhook_endpoint():
    """Endpoint para configurar webhook"""
    global bot_configured
    
    try:
        if not validate_telegram_token():
            return jsonify({
                "success": False,
                "error": "Token de Telegram inválido",
                "token_provided": bool(TELEGRAM_TOKEN)
            }), 400
        
        success = setup_webhook()
        bot_configured = success
        
        return jsonify({
            "success": success,
            "webhook_configured": bot_configured,
            "webhook_url": f"{WEBHOOK_URL}/telegram-webhook",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"❌ Webhook setup error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# ===== CONFIGURACIÓN BOT =====

# Registrar rutas del bot
setup_telegram_routes(app)

# ===== MAIN =====

if __name__ == '__main__':
    logger.info("🚀 Starting mcpComercialExt v1.0")
    
    # Validar configuración crítica
    if not TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN not configured")
    elif not validate_telegram_token():
        logger.error("❌ Invalid TELEGRAM_TOKEN")
    else:
        logger.info("✅ Telegram token validated")
    
    if not REDASH_API_KEY:
        logger.error("❌ REDASH_API_KEY not configured")
    else:
        logger.info("✅ Redash API key configured")
    
    # Configurar webhook si es posible
    if TELEGRAM_TOKEN and validate_telegram_token():
        try:
            bot_configured = setup_webhook()
            logger.info(f"🤖 Bot webhook: {'✅ Configured' if bot_configured else '❌ Failed'}")
        except Exception as e:
            logger.warning(f"⚠️ Webhook setup failed: {e}")
    
    # Pre-cargar cache de clientes
    try:
        logger.info("📊 Pre-loading clients cache...")
        cache_result = get_clients_from_redash()
        if cache_result.get("success"):
            total_clients = cache_result.get("total", 0)
            logger.info(f"✅ Cache pre-loaded with {total_clients:,} clients")
        else:
            logger.warning(f"⚠️ Cache pre-load failed: {cache_result.get('error')}")
    except Exception as e:
        logger.warning(f"⚠️ Cache pre-load exception: {e}")
    
    # Ejecutar Flask
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Starting Flask app on port {port}")
    logger.info("🔍 Ready for client searches via Telegram bot")
    
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
