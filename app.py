# 🚀 mcpComercialExt v1.3 - Aplicación Principal + NocoDB
import os
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import logging

# Imports modulares
from config import *
from redash_service import get_clients_from_redash, search_client_by_document_with_availability, get_clients_summary
from nocodb_service import (check_comercial_exists, create_comercial, get_comercial_info, 
                           check_order_exists, process_order_assignment, get_comercial_by_cedula)
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
        "name": "mcpComercialExt - Bot Comercial Externo + NocoDB",
        "version": "1.3.0",
        "status": "running",
        "description": "Sistema de búsqueda de clientes para comerciales externos via Telegram + Gestión de Comerciales",
        "features": [
            "Búsqueda de clientes por NIT y CC",
            "Integración con Redash API", 
            "Registro de comerciales con NocoDB",
            "Cache inteligente",
            "Validación automática de documentos",
            "Bot de Telegram interactivo",
            "Validación de duplicados comerciales",
            "Formatos de email y teléfono validados"
        ],
        "timestamp": datetime.now().isoformat(),
        "cache_status": {
            "enabled": True,
            "ttl_seconds": clients_cache["ttl"],
            "last_update": datetime.fromtimestamp(clients_cache["timestamp"]).isoformat() if clients_cache["timestamp"] > 0 else "never"
        },
        "telegram_bot": {
            "enabled": bool(TELEGRAM_TOKEN),
            "token_valid": validate_telegram_token() if TELEGRAM_TOKEN else False,
            "webhook_configured": bot_configured,
            "webhook_url": f"{WEBHOOK_URL}/telegram-webhook" if TELEGRAM_TOKEN and WEBHOOK_URL else None
        },
        "redash_integration": {
            "base_url": REDASH_BASE_URL or "not_configured",
            "query_id": REDASH_QUERY_ID or "not_configured", 
            "api_configured": bool(REDASH_API_KEY)
        },
        "nocodb_integration": {
            "base_url": NOCODB_BASE_URL or "not_configured",
            "table_id": NOCODB_TABLE_ID or "not_configured",
            "api_configured": bool(NOCODB_TOKEN),
            "timeout": NOCODB_TIMEOUT
        },
        "api_endpoints": {
            "clients": {
                "/api/clients": "Lista de clientes desde Redash",
                "/api/clients/search": "Búsqueda por documento", 
                "/api/clients/summary": "Resumen y estadísticas"
            },
            "comerciales": {
                "/api/comerciales/check": "Verificar existencia de comercial",
                "/api/comerciales/create": "Crear nuevo comercial",
                "/api/comerciales/info": "Información de comercial"
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
        },
        "comercial_validation": {
            "cedula": f"Entre {MIN_CEDULA_LENGTH} y {MAX_CEDULA_LENGTH} dígitos", 
            "name": f"Entre {MIN_NAME_LENGTH} y {MAX_NAME_LENGTH} caracteres",
            "phone": f"Entre {MIN_PHONE_LENGTH} y {MAX_PHONE_LENGTH} dígitos",
            "email": "Formato válido con @ y dominio"
        }
    })

@app.route('/health')
def health():
    """Health check optimizado con NocoDB"""
    import time
    start_time = time.time()
    
    # Test Redash connection
    redash_test = get_clients_summary()
    
    # Test NocoDB connection
    nocodb_test = {"success": True, "error": None}
    try:
        if NOCODB_TOKEN:
            test_check = check_comercial_exists("999999999")  # Cédula de test
            if not test_check.get("success"):
                nocodb_test = {"success": False, "error": test_check.get("error")}
        else:
            nocodb_test = {"success": False, "error": "NOCODB_TOKEN not configured"}
    except Exception as e:
        nocodb_test = {"success": False, "error": str(e)}
    
    response_time = time.time() - start_time
    
    # Test Telegram token
    telegram_valid = validate_telegram_token() if TELEGRAM_TOKEN else False
    
    return jsonify({
        "status": "healthy",
        "response_time_ms": round(response_time * 1000, 2),
        "cache_hit": redash_test.get('stats', {}).get('cached', False) if redash_test.get('success') else False,
        "services": {
            "flask": "running",
            "redash_api": "ok" if redash_test.get('success') else "error",
            "nocodb_api": "ok" if nocodb_test.get('success') else "error",
            "cache": "active" if clients_cache["data"] else "empty",
            "telegram_bot": "configured" if telegram_valid else "invalid_token",
            "webhook": "configured" if bot_configured else "not_configured"
        },
        "data_status": {
            "clients_available": redash_test.get('stats', {}).get('total_clients', 0) if redash_test.get('success') else 0,
            "columns_detected": redash_test.get('stats', {}).get('total_columns', 0) if redash_test.get('success') else 0,
            "cache_age_minutes": round((time.time() - clients_cache["timestamp"]) / 60, 1) if clients_cache["timestamp"] > 0 else 0,
            "nocodb_connection": "ok" if nocodb_test.get('success') else f"error: {nocodb_test.get('error')}"
        },
        "last_check": datetime.now().isoformat()
    })

# ===== API ENDPOINTS CLIENTES =====

@app.route('/api/clients')
def api_clients():
    """API para obtener clientes desde Redash"""
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
        result = search_client_by_document_with_availability(doc_type, doc_number)
        
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

# ===== API ENDPOINTS COMERCIALES =====

@app.route('/api/comerciales/check', methods=['GET'])
def api_check_comercial():
    """API para verificar existencia de comercial"""
    cedula = request.args.get('cedula', '').strip()
    
    if not cedula:
        return jsonify({
            "error": "Parámetro requerido: cedula",
            "example": "/api/comerciales/check?cedula=12345678"
        }), 400
    
    try:
        result = check_comercial_exists(cedula)
        
        if result.get("success"):
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"❌ API check comercial error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/comerciales/create', methods=['POST'])
def api_create_comercial():
    """API para crear nuevo comercial"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "JSON data requerido"}), 400
        
        required_fields = ['cedula', 'email', 'name', 'phone']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                "error": f"Campos requeridos faltantes: {', '.join(missing_fields)}",
                "required_fields": required_fields,
                "example": {
                    "cedula": "12345678",
                    "email": "comercial@empresa.com",
                    "name": "Juan Pérez",
                    "phone": "3001234567"
                }
            }), 400
        
        result = create_comercial(
            cedula=data['cedula'],
            email=data['email'],
            name=data['name'],
            phone=data['phone']
        )
        
        if result.get("success"):
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"❌ API create comercial error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/comerciales/info', methods=['GET'])
def api_comercial_info():
    """API para obtener información de comercial"""
    cedula = request.args.get('cedula', '').strip()
    
    if not cedula:
        return jsonify({
            "error": "Parámetro requerido: cedula",
            "example": "/api/comerciales/info?cedula=12345678"
        }), 400
    
    try:
        result = get_comercial_info(cedula)
        
        if result.get("success"):
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"❌ API comercial info error: {e}")
        return jsonify({"error": str(e)}), 500

# ===== API ENDPOINTS ÓRDENES =====

@app.route('/api/orders/check', methods=['GET'])
def api_check_order():
    """API para verificar existencia de orden"""
    order_number = request.args.get('order_number', '').strip()
    
    if not order_number:
        return jsonify({
            "error": "Parámetro requerido: order_number",
            "example": "/api/orders/check?order_number=MP-0003"
        }), 400
    
    try:
        result = check_order_exists(order_number)
        
        if result.get("success"):
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"❌ API check order error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/orders/assign', methods=['POST'])
def api_assign_order():
    """API para asignar orden a comercial"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "JSON data requerido"}), 400
        
        required_fields = ['cedula', 'order_number']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                "error": f"Campos requeridos faltantes: {', '.join(missing_fields)}",
                "required_fields": required_fields,
                "example": {
                    "cedula": "12345678",
                    "order_number": "MP-0003"
                }
            }), 400
        
        result = process_order_assignment(
            cedula=data['cedula'],
            order_number=data['order_number']
        )
        
        if result.get("success"):
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"❌ API assign order error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/orders/process', methods=['POST'])
def api_process_order():
    """API para procesar asignación completa (comercial + orden)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "JSON data requerido"}), 400
        
        required_fields = ['cedula', 'order_number']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                "error": f"Campos requeridos faltantes: {', '.join(missing_fields)}",
                "required_fields": required_fields,
                "process": {
                    "step_1": "Verificar comercial existe",
                    "step_2": "Verificar orden existe",
                    "step_3": "Asignar orden al comercial"
                },
                "example": {
                    "cedula": "12345678",
                    "order_number": "MP-0003"
                }
            }), 400
        
        result = process_order_assignment(
            cedula=data['cedula'],
            order_number=data['order_number']
        )
        
        if result.get("success"):
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"❌ API process order error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/comerciales/get', methods=['GET'])
def api_get_comercial():
    """API para obtener comercial por cédula con ID"""
    cedula = request.args.get('cedula', '').strip()
    
    if not cedula:
        return jsonify({
            "error": "Parámetro requerido: cedula",
            "example": "/api/comerciales/get?cedula=12345678"
        }), 400
    
    try:
        result = get_comercial_by_cedula(cedula)
        
        if result.get("success"):
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"❌ API get comercial error: {e}")
        return jsonify({"error": str(e)}), 500

# ===== ENDPOINT WEBHOOK =====

@app.route('/setup-webhook', methods=['POST'])
def setup_webhook_endpoint():
    """Endpoint para configurar webhook"""
    global bot_configured
    
    try:
        if not TELEGRAM_TOKEN:
            return jsonify({
                "success": False,
                "error": "TELEGRAM_TOKEN no configurado",
                "token_provided": False
            }), 400
        
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
    logger.info("🚀 Starting mcpComercialExt v1.3 + NocoDB")
    
    # Validar configuración crítica
    if not TELEGRAM_TOKEN:
        logger.warning("⚠️ TELEGRAM_TOKEN not configured")
    elif not validate_telegram_token():
        logger.warning("⚠️ Invalid TELEGRAM_TOKEN")
    else:
        logger.info("✅ Telegram token validated")
    
    if not REDASH_API_KEY:
        logger.warning("⚠️ REDASH_API_KEY not configured")
    else:
        logger.info("✅ Redash API key configured")
    
    if not NOCODB_TOKEN:
        logger.warning("⚠️ NOCODB_TOKEN not configured")
    else:
        logger.info("✅ NocoDB token configured")
    
    # Test NocoDB connection
    if NOCODB_TOKEN:
        try:
            logger.info("🔗 Testing NocoDB connection...")
            test_result = check_comercial_exists("999999999")  # Cédula de test
            if test_result.get("success"):
                logger.info("✅ NocoDB connection successful")
            else:
                logger.warning(f"⚠️ NocoDB connection issue: {test_result.get('error')}")
        except Exception as e:
            logger.warning(f"⚠️ NocoDB connection test failed: {e}")
    
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
    logger.info("👤 Ready for comercial registration via Telegram bot")
    
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
